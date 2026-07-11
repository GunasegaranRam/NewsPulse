# NewsPulse (Personalized AI News Agent)

NewsPulse is an autonomous AI Agent that acts as a personalized, interactive news host. 

## The Vision
NewsPulse replaces traditional static news feeds with a highly interactive, conversational AI Radio Host. Rather than reading articles, you simply tap the central God Button and ask for the news (e.g. *"What's happening in tech today?"*). The AI scrapes real-time news, synthesizes a broadcast script, and reads it to you using a premium neural voice, while rendering beautiful data flashcards on screen.

It features **Stateful Memory** and an **Intelligent Intent Router**. You can interrupt the host at any time and say *"Wait, tell me more about that first topic."* The system will intelligently skip the web scrape, pull the raw HTML from its memory cache, and instantly generate a deeply comprehensive conversational deep-dive.

## How it works (Agentic Architecture)
1. **The Pulse UI:** A fluid, glassmorphism UI built with Vanilla JS/HTML/CSS that uses a single state-machine button to manage audio unlocking, interruptions, and recording.
2. **The Intelligent Router:** Uses **GPT-OSS-120B** (via Fireworks AI) to mathematically route user voice inputs into either a `SEARCH` intent or a `CONVERSATIONAL` deep-dive.
3. **The Agentic Brain:** If a search is required, it scrapes Google News RSS feeds. It feeds the raw HTML context to the LLM to generate a JSON payload containing both the spoken script and structured UI flashcards.
4. **The Voice (TTS):** Uses `edge-tts` (Christopher Neural) to synthesize the text into an energetic, perfectly paced human voice.

## Technologies Used
*   **FastAPI & Uvicorn** for a lightning-fast asynchronous backend.
*   **Fireworks AI API** (AMD Infrastructure) for LLM reasoning and intent routing.
*   **Vanilla JS, HTML, Vanilla CSS** for a dependency-free, high-performance interactive frontend.
*   **Google News RSS** for real-time news scraping.
*   **Edge-TTS** for premium speech generation.

## Local Setup (Without Docker)
If you have `uv` installed, you can run this instantly:

1. Clone the repository and navigate into it.
2. Install dependencies: `uv pip install -r requirements.txt`
3. Export your Fireworks API Key: `export FIREWORKS_API_KEY=your_key_here`
4. Boot the FastAPI Server: `uvicorn api:app --reload`
5. Open `http://localhost:8000` in your browser.

## Running via Docker
1. Build the image: 
   ```bash
   docker build -t newspulse .
   ```
2. Run the container (Make sure to pass your API key):
   ```bash
   docker run -p 8000:8000 -e FIREWORKS_API_KEY=your_key_here newspulse
   ```
3. Open `http://localhost:8000` in your browser.
