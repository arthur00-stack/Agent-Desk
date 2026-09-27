"""API FastAPI exposant la desk d'agents + la voix (Gradium).
Lancer avec : uvicorn app.main:app --reload
"""

from app import config  # charge .env avant tout le reste, quel que soit le chemin emprunté ensuite
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.orchestrator import run_desk
from app.tools.voice import synthesize_speech, transcribe_speech

app = FastAPI(title="Alpha Desk — AI Trading Floor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    query: str
    ticker: str


class SpeakRequest(BaseModel):
    text: str
    agent: str = "portfolio_manager"


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return run_desk(query=req.query, ticker=req.ticker.upper())


@app.post("/speak")
def speak(req: SpeakRequest):
    """Synthétise un texte en audio via Gradium. Renvoie 204 (pas de contenu)
    si la voix est indisponible — le front doit gérer ce cas en silence."""
    audio = synthesize_speech(req.text, agent=req.agent)
    if audio is None:
        return Response(status_code=204)
    return Response(content=audio, media_type="audio/wav")


@app.post("/listen")
async def listen(file: UploadFile = File(...)):
    """Transcrit un enregistrement micro en texte via Gradium."""
    audio_bytes = await file.read()
    text = transcribe_speech(audio_bytes, content_type=file.content_type or "audio/wav")
    if text is None:
        return {"text": None, "available": False}
    return {"text": text, "available": True}


@app.get("/")
def root():
    return FileResponse("frontend/index.html")


app.mount("/static", StaticFiles(directory="frontend"), name="static")
