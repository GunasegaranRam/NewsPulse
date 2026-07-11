import os
import asyncio
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

def generate_script(topic, news_items):
    """Uses Fireworks AI to generate a radio script based on the news."""
    print("Generating script...")
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
        "Your job is to write a short, 60-second broadcast script summarizing the most interesting points. "
        "Speak directly to the listeners. Do not include stage directions like [Host smiles] or sound effects in the text. "
        "IMPORTANT: Output ONLY the exact words you want spoken. Do not include any thinking process, reasoning, or introductions. "
        "CRITICAL: Do NOT say any greetings like 'Hello listeners', 'Welcome to the broadcast', or state your name. Dive straight into the news immediately."
    )
    
    user_prompt = f"Topic: {topic}\n\nNews Feeds:\n{context}\n\nWrite the broadcast script now."
    
    response = client.chat.completions.create(
        model="accounts/fireworks/models/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    script = response.choices[0].message.content
    print("Script generated successfully.")
    return script

async def async_generate_audio(script, output_file):
    """Asynchronously generates audio from text using edge-tts."""
    print(f"Generating audio to {output_file}...")
    communicate = edge_tts.Communicate(script, TTS_VOICE)
    await communicate.save(output_file)
    print("Audio generation complete.")

def generate_audio(script, output_file="output.mp3"):
    """Wrapper to run the async edge-tts function synchronously."""
    asyncio.run(async_generate_audio(script, output_file))
    return output_file
