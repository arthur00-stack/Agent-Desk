"""Client LLM unique utilisé par tous les agents.

Deux modes :
- Mode réel : appelle l'API OpenAI (Responses API) et force du JSON.
- Mode mock (USE_MOCK_LLM=1) : renvoie des réponses factices, pour répéter
  la démo hors-ligne / sans consommer de crédits / sans risque de plantage.

L'import d'`openai` est fait à la demande (lazy) pour que le mode mock
fonctionne même si le package n'est pas installé.
"""
import json
import os
import re

from app import config  # charge le .env

_client = None


def get_client():
    global _client
    if _client is None:
        from openai import OpenAI  # import tardif volontaire

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY introuvable. Vérifie que :\n"
                "  1. le fichier .env existe à la racine du projet (pas juste .env.example)\n"
                "     -> cp .env.example .env, puis remplis-le\n"
                "  2. il contient une ligne OPENAI_API_KEY=sk-...\n"
                "  3. python-dotenv est installé : pip install -r requirements.txt (dans ton venv activé)"
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _extract_json(raw: str) -> dict:
    """Extrait le premier objet JSON valide d'une chaîne, même si le modèle
    a ajouté du texte ou des ``` autour (ça arrive)."""
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    # Dernier recours : on ne casse jamais la démo
    return {
        "stance": "neutral",
        "confidence": 0.0,
        "reasoning": f"[PARSE_ERROR] Réponse brute non parsable: {raw[:300]}",
        "key_points": [],
    }


def chat_json(system: str, user: str, model: str = None) -> dict:
    if os.environ.get("USE_MOCK_LLM") == "1":
        from app.mock_responses import get_mock_response
        return get_mock_response(system)

    client = get_client()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-5")
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return _extract_json(response.output_text)
