import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from agent import search_news, generate_content, generate_audio, extract_intent
import uuid

app = FastAPI(title="AI Radio Host API")

class GenerateRequest(BaseModel):
    topic: str
    context: Optional[List[str]] = None

class SynthesizeRequest(BaseModel):
    text: str

@app.post("/generate")
def generate_endpoint(req: GenerateRequest):
    try:
        # Extract intent if context is provided
        actual_topic = req.topic
        if req.context:
            actual_topic = extract_intent(req.topic, req.context)
            
        news_items = search_news(actual_topic, max_results=5)
        if not news_items:
            return JSONResponse({"error": "No news found."}, status_code=404)
        
        data = generate_content(req.topic, news_items)
        
        # Pre-generate the main audio
        audio_file = f"{uuid.uuid4()}.mp3"
        generate_audio(data.get("spoken_script", ""), audio_file)
        
        return {
            "flashcards": data.get("flashcards", []),
            "spoken_script": data.get("spoken_script", ""),
            "audio_url": f"/audio/{audio_file}"
        }
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
