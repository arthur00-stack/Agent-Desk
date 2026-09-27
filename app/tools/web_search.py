"""Récupère des actualités récentes sur un actif via l'outil web_search
natif de l'API OpenAI (Responses API). Fallback mock si pas de clé / pas
de réseau / erreur API — même logique de robustesse que market_data.py.
"""
import os


def get_recent_news(query: str, max_items: int = 5) -> list:
    if os.environ.get("USE_MOCK_LLM") == "1":
        return _mock_news(query)

    try:
        from app.llm_client import get_client

        client = get_client()
        model = os.environ.get("OPENAI_MODEL", "gpt-5")
        resp = client.responses.create(
            model=model,
            tools=[{"type": "web_search"}],
            input=(
                f"Donne les {max_items} actualités les plus récentes et pertinentes sur : "
                f"{query}. Une ligne par actu, format : 'Titre — résumé en une phrase.'"
            ),
        )
        lines = [l.strip("-• ").strip() for l in resp.output_text.split("\n") if l.strip()]
        return lines[:max_items] if lines else _mock_news(query)
    except Exception:
        return _mock_news(query)


def _mock_news(query: str) -> list:
    return [
        f"[MOCK] {query} : les analystes restent partagés avant la prochaine publication.",
        f"[MOCK] {query} : volumes en hausse dans un secteur volatil cette semaine.",
        f"[MOCK] {query} : pas d'actualité réglementaire majeure recensée.",
    ]
