import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from agent import search_news, generate_content, generate_audio, extract_intent
import uuid

# Global memory for storing Chat History
memory = {
    "default": {
        "chat_history": [],
        "latest_news": []
    }
}

app = FastAPI(title="NewsPulse API")

class GenerateRequest(BaseModel):
    topic: str
    context: Optional[List[str]] = None
    session_id: Optional[str] = "default"

class SynthesizeRequest(BaseModel):
    text: str

@app.post("/generate")
def generate_endpoint(req: GenerateRequest):
    try:
        # Initialize session memory if not exists
        if req.session_id not in memory:
            memory[req.session_id] = {"chat_history": [], "latest_news": []}
            
        session = memory[req.session_id]
        
        # Extract intent if context is provided
        actual_topic = req.topic
        if req.context:
            actual_topic = extract_intent(req.topic, req.context)
            
        # Append user's raw topic to chat history
        session["chat_history"].append({"role": "user", "content": req.topic})
            
        if actual_topic == "CONVERSATIONAL":
            print("Routing to Conversational Mode (Using cached news)")
            news_items = session["latest_news"]
            topic_for_generation = "Conversational Follow-up"
            is_conv = True
        else:
            news_items = search_news(actual_topic, max_results=5)
            if not news_items:
                return JSONResponse({"error": "No news found."}, status_code=404)
            session["latest_news"] = news_items
            topic_for_generation = actual_topic
            is_conv = False
        
        data = generate_content(topic_for_generation, news_items, session["chat_history"], is_conversational=is_conv)
        
        # Append AI's spoken script to chat history
        session["chat_history"].append({"role": "assistant", "content": data.get("spoken_script", "")})
        
        # Pre-generate the main audio
        audio_file = f"{uuid.uuid4()}.mp3"
        generate_audio(data.get("spoken_script", ""), audio_file)
        
        return JSONResponse({
            "flashcards": data.get("flashcards", []),
            "spoken_script": data.get("spoken_script", ""),
            "audio_url": f"/audio/{audio_file}"
        })
    except Exception as e:
        print(f"Error in /generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/synthesize")
def synthesize_endpoint(req: SynthesizeRequest):
    try:
        audio_file = f"{uuid.uuid4()}.mp3"
        generate_audio(req.text, audio_file)
        return {"audio_url": f"/audio/{audio_file}"}
    except Exception as e:
        print(f"Error in /synthesize: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
def get_audio(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="File not found")

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount the static directory to serve index.html, style.css, app.js
app.mount("/", StaticFiles(directory="static", html=True), name="static")
