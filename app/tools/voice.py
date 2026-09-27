"""Intégration Gradium : voix de sortie (TTS) pour chaque agent et
transcription vocale (STT) en entrée.

On utilise les endpoints REST one-shot (pas de WebSocket à gérer) : le plus
simple et le plus robuste pour une démo de hackathon. Comme pour Finnhub et
les news, l'absence de clé ou une erreur réseau renvoie None plutôt que de
lever une exception : le front bascule alors silencieusement sur l'affichage
texte seul, jamais de plantage.

En mode USE_MOCK_LLM=1, aucun appel réseau n'est fait du tout (cohérent avec
le principe : mode mock = zéro dépendance externe, pour répéter la démo hors
ligne).
"""
import json
import os

import requests

GRADIUM_TTS_URL = "https://api.gradium.ai/api/post/speech/tts"
GRADIUM_STT_URL = "https://api.gradium.ai/api/post/speech/asr"

# Une voix différente par rôle pour l'effet "salle de marché". Remplace ces
# ID par de vraies voix choisies dans la bibliothèque Gradium (Studio) une
# fois que tu as ta clé.
VOICE_IDS = {
    "macro": os.environ.get("GRADIUM_VOICE_MACRO", "YTpq7expH9539ERJ"),
    "fundamentals": os.environ.get("GRADIUM_VOICE_FUNDAMENTALS", "YTpq7expH9539ERJ"),
    "technical": os.environ.get("GRADIUM_VOICE_TECHNICAL", "YTpq7expH9539ERJ"),
    "risk": os.environ.get("GRADIUM_VOICE_RISK", "YTpq7expH9539ERJ"),
    "portfolio_manager": os.environ.get("GRADIUM_VOICE_PM", "YTpq7expH9539ERJ"),
}


def _is_disabled() -> bool:
    return os.environ.get("USE_MOCK_LLM") == "1" or not os.environ.get("GRADIUM_API_KEY")


def synthesize_speech(text: str, agent: str = "portfolio_manager") -> bytes | None:
    """Renvoie l'audio WAV (bytes) pour ce texte, ou None si la voix est
    indisponible (mode mock, pas de clé, erreur réseau)."""
    if _is_disabled():
        return None
    try:
        resp = requests.post(
            GRADIUM_TTS_URL,
            headers={"x-api-key": os.environ["GRADIUM_API_KEY"], "Content-Type": "application/json"},
            json={
                "text": text,
                "voice_id": VOICE_IDS.get(agent, VOICE_IDS["portfolio_manager"]),
                "output_format": "wav",
                "only_audio": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def transcribe_speech(audio_bytes: bytes, content_type: str = "audio/wav") -> str | None:
    """Transcrit un enregistrement micro en texte, ou None si indisponible."""
    if _is_disabled():
        return None
    try:
        resp = requests.post(
            GRADIUM_STT_URL,
            data=audio_bytes,
            headers={"x-api-key": os.environ["GRADIUM_API_KEY"], "Content-Type": content_type},
            stream=True,
            timeout=20,
        )
        resp.raise_for_status()
        segments = []
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            msg = json.loads(line)
            if msg.get("type") == "text":
                segments.append(msg["text"])
        return " ".join(segments) if segments else None
    except Exception:
        return None
