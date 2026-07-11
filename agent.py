import os
import asyncio
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from openai import OpenAI
import edge_tts

# We will use Microsoft Edge's free TTS.
# 'en-US-AriaNeural' is a very crisp, energetic female voice.
TTS_VOICE = "en-US-AriaNeural"

def search_news(topic, max_results=5):
    """Searches Google News RSS for the latest articles on the topic."""
    print(f"Searching news for: {topic}")
    results = []
    
    encoded_topic = urllib.parse.quote(topic)
    url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item')[:max_results]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            # Google news description is often HTML, but it's enough for the LLM to understand
            desc = item.find('description').text if item.find('description') is not None else "No Summary"
            results.append({'title': title, 'body': desc})
    except Exception as e:
        print(f"Error fetching news: {e}")
        
    return results

def extract_intent(user_input, current_context):
    """Uses LLM to deduce the real search query if the user uses relative terms like 'the first one'."""
    if not current_context:
        return user_input # No context, return raw input
        
    api_key = os.environ.get("FIREWORKS_API_KEY")
    client = OpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=api_key)
    
    prompt = (
        f"The user input is: '{user_input}'.\n"
        f"The current flashcards on their screen are: {current_context}.\n\n"
        "Your goal is to extract the purest, most effective Google News search query from the user input.\n"
        "- If the user uses a relative term (e.g., 'the first one', 'that tech story'), map it to the exact flashcard topic.\n"
        "- If the user says 'Deep dive into X' or 'Tell me about X', output ONLY 'X'.\n"
        "- Do NOT include conversational filler like 'Deep dive into' or 'Search for'.\n"
        "Output ONLY the final search query. Nothing else."
    )
    
    response = client.chat.completions.create(
        model="accounts/fireworks/models/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=20
    )
    
    content = response.choices[0].message.content
    if content:
        query = content.strip()
        print(f"LLM Extracted Intent: '{query}'")
    else:
        query = user_input
        print(f"LLM Glitch (None). Fallback to Raw Input: '{query}'")
        
    if not query:
        query = user_input
    return query

def generate_content(topic, news_items):
    """Uses Fireworks AI to generate a radio script and UI flashcards."""
    print("Generating content...")
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY environment variable not set.")
    
    # Initialize OpenAI client pointing to Fireworks API
    client = OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=api_key,
    )
    
    # Prepare the context from the news
    context = ""
    for idx, item in enumerate(news_items):
        context += f"Headline {idx+1}: {item.get('title')}\nSummary: {item.get('body')}\n\n"
    
    system_prompt = (
        "You are an energetic and engaging AI radio host. "
        "You will be given a list of recent news headlines and summaries about a topic. "
        "Your job is to write a comprehensive, 60-second broadcast script summarizing the news in detail, and ALSO extract strictly constricted flashcards for the UI. "
        "The AUDIO script must be highly detailed and comprehensive. The FLASHCARDS must be heavily constricted, showing only minimal keywords/numbers. "
        "Speak directly to the listeners in the script. Do NOT say any greetings like 'Hello listeners', just dive straight into the news. "
        "IMPORTANT: You MUST output ONLY valid JSON. Do not wrap it in markdown block quotes (no ```json). "
        "CRITICAL: Escape all newlines inside strings as \\n. Do NOT use literal newlines inside JSON strings. "
        "The JSON must have this exact structure: "
        "{ "
        "  \"spoken_script\": \"The highly comprehensive energetic broadcast script here. Escape quotes and use \\n for newlines.\", "
        "  \"flashcards\": [ "
        "    { \"headline\": \"Constricted Short Title\", \"key_stat\": \"E.g., +4.5%\", \"short_summary\": \"1 heavily constricted sentence\" } "
        "  ] "
        "}"
    )
    
    user_prompt = f"Topic: {topic}\n\nNews Feeds:\n{context}\n\nWrite the broadcast content in JSON format now."
    
    response = client.chat.completions.create(
        model="accounts/fireworks/models/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    script_content = content.strip() if content else ""
    if not script_content:
        raise ValueError("LLM returned empty content.")
    
    # Robust JSON extraction
    import re
    # Find everything from the first { to the last }
    match = re.search(r'\{.*\}', script_content, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            if "Extra data" in str(e):
                valid_json = json_str[:e.pos].strip()
                data = json.loads(valid_json)
            else:
                print("Failed to parse extracted JSON:", e)
                raise e
    else:
        try:
            data = json.loads(script_content)
        except json.JSONDecodeError as e:
            if "Extra data" in str(e):
                valid_json = script_content[:e.pos].strip()
                data = json.loads(valid_json)
            else:
                raise e
            
    print("Content generated successfully.")
    return data

async def async_generate_audio(script, output_file):
    """Asynchronously generates audio from text using edge-tts."""
    print(f"Generating audio to {output_file}...")
    communicate = edge_tts.Communicate(script, "en-US-ChristopherNeural")
    await communicate.save(output_file)
    print("Audio generation complete.")

def generate_audio(script, output_file="output.mp3"):
    """Wrapper to run the async edge-tts function synchronously."""
    asyncio.run(async_generate_audio(script, output_file))
    return output_file
