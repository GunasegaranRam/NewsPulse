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
    if not current_context:
        return user_input
    
    api_key = os.environ.get("FIREWORKS_API_KEY")
    client = OpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=api_key)
        
    prompt = (
        f"The user input is: '{user_input}'.\n"
        f"The current flashcards on their screen are: {current_context}.\n\n"
        "Your goal is to act as an Intelligent Router. Decide if the user is asking a conversational follow-up question, or if they are asking for a new deep-dive search.\n"
        "1. CONVERSATIONAL: If the user is asking you to explain something you just said, asking a follow-up question, or asking to go into detail about one of the flashcards (e.g., 'Explain what HBM memory is', 'Tell me more about the first one', 'Deep dive into that', 'what is the first one'), output ONLY the exact word 'CONVERSATIONAL'.\n"
        "2. SEARCH: If the user is asking to search for a completely new topic from the internet (e.g., 'What is the latest news on Apple', 'Search for tech news'). Extract the purest Google News search query from their input (e.g., 'Apple').\n"
        "Output ONLY the final search query, or the word 'CONVERSATIONAL'. Nothing else."
    )
    
    response = client.chat.completions.create(
        model="accounts/fireworks/models/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=50
    )
    
    content = response.choices[0].message.content
    query = ""
    if content:
        query = content.strip()
        print(f"LLM Extracted Intent/Route: '{query}'")
        
        # Robust parsing: If the LLM included preamble but has the word CONVERSATIONAL
        if "CONVERSATIONAL" in query.upper():
            return "CONVERSATIONAL"
            
        # Clean up quotes if the LLM wrapped it
        query = query.replace('"', '').replace("'", "")
    
    if not query:
        print(f"LLM Glitch (None). Fallback to Rules for: '{user_input}'")
        query = user_input
        
    # Rule-based fallback: If the router failed to say CONVERSATIONAL, 
    # but the input clearly references existing context
    conversational_triggers = ["first", "second", "third", "last", "this", "that", "more", "explain", "why", "mean"]
    if any(trigger in query.lower() for trigger in conversational_triggers) and len(query.split()) < 10:
        print("Rule-based router override: Detected conversational trigger.")
        return "CONVERSATIONAL"
        
    return query

def generate_content(topic, news_items, chat_history=None, is_conversational=False):
    if chat_history is None:
        chat_history = []
    
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY environment variable not set.")
    
    # Initialize OpenAI client pointing to Fireworks API
    client = OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=api_key,
    )
    
    system_prompt = (
        "You are Christopher, the highly engaging, energetic host of NewsPulse. You speak conversationally, with crisp enunciation and perfect pacing.\n"
        "Do NOT say any greetings like 'Good morning' or 'Hello listeners'. Dive straight into the core information.\n"
        "If you are answering a conversational follow-up question, answer the user's specific question using the provided news items and chat history as background knowledge. Go into extremely deep detail if requested.\n"
        "If you are NOT answering a conversational question, summarize the provided news items into an exciting 1-minute news broadcast script.\n"
        "You must ALWAYS return your response in this EXACT JSON structure:\n"
        "{\n"
        "  \"spoken_script\": \"The highly comprehensive energetic broadcast script or your conversational answer. Escape quotes and use \\n for newlines.\",\n"
        "  \"flashcards\": [\n"
        "    { \"headline\": \"Topic Name\", \"key_stat\": \"Key metric\", \"short_summary\": \"A HIGHLY DETAILED, comprehensive paragraph explaining the core story in depth.\" }\n"
        "  ]\n"
        "If the user is asking for a deep dive or follow up on a specific topic, make the flashcard summaries extremely detailed and comprehensive paragraphs.\n"
        "}\n"
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append the last 6 turns of chat history to keep context
    for msg in chat_history[-6:]:
        messages.append(msg)
        
    news_text = "\n\n".join([f"Headline: {item['title']}\nSummary: {item['body']}" for item in news_items]) if news_items else "No news available."
    
    if is_conversational:
        latest_prompt = f"Background News Context:\n{news_text}\n\nGenerate the conversational JSON answer to the user's last question."
    else:
        latest_prompt = f"Here are the latest news items for the topic '{topic}':\n{news_text}\n\nWrite the broadcast content in JSON format now."
        
    messages.append({"role": "user", "content": latest_prompt})
    
    response = client.chat.completions.create(
        model="accounts/fireworks/models/gpt-oss-120b",
        messages=messages,
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
