# NewsPulse (Personalized AI News Agent)

This project is built for the **AMD Developer Hackathon: ACT II** (Unicorn Track). 
It is an autonomous AI Agent that acts as a personalized, interactive news host. 

## How it works (Agentic Workflow)
1. **Search Tool:** The agent uses DuckDuckGo News to scrape the latest, real-time headlines on a user-provided topic.
2. **The Brain (Fireworks AI):** It curates those raw news feeds and uses **Llama 3** (hosted on AMD hardware via Fireworks AI API) to autonomously write a conversational, 60-second broadcast script.
3. **The Voice (TTS Tool):** It uses `edge-tts` to synthesize the written script into a high-quality human voice output.

## Technologies Used
*   **Fireworks AI API** (AMD Infrastructure) for LLM reasoning and script generation.
*   **Streamlit** for the web interface.
*   **DuckDuckGo Search** for real-time data scraping.
*   **Edge-TTS** for speech generation.

## Local Setup (Without Docker)
If you have `uv` installed, you can run this instantly:

1. Clone the repository and navigate into it.
2. Install dependencies: `uv pip install -r requirements.txt`
3. Export your Fireworks API Key: `export FIREWORKS_API_KEY=your_key_here`
4. Run the app: `uv run streamlit run app.py`

## Running via Docker (Hackathon Containerization Requirement)
1. Build the image: 
   ```bash
   docker build -t ai-radio-host .
   ```
2. Run the container (Make sure to pass your API key):
   ```bash
   docker run -p 8501:8501 -e FIREWORKS_API_KEY=your_key_here ai-radio-host
   ```
3. Open `http://localhost:8501` in your browser.
