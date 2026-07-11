import os, json
from openai import OpenAI
client = OpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=os.environ.get("FIREWORKS_API_KEY"))
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
response = client.chat.completions.create(
    model="accounts/fireworks/models/gpt-oss-120b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Topic: Stock market\n\nWrite the broadcast content in JSON format now."}
    ],
    temperature=0.7,
    max_tokens=2000,
    response_format={"type": "json_object"}
)
print("RAW:")
print(response.choices[0].message.content)
