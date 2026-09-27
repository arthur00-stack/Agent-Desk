from app.agents.base_agent import BaseAgent

_JSON_FORMAT = (
    'Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format : '
    '{"stance": "bullish|bearish|neutral", "confidence": 0.0-1.0, '
    '"reasoning": "...", "key_points": ["...", "..."]}'
)


class FundamentalsAgent(BaseAgent):
    name = "fundamentals"
    system_prompt = (
        "Tu es l'analyste FONDAMENTAL d'une desk de trading IA. Tu évalues la valorisation et "
        "la santé financière de l'entreprise (PER, capitalisation) par rapport à son secteur. "
        + _JSON_FORMAT
    )

    def build_prompt(self, context: dict) -> str:
        s = context["snapshot"]
        return (
            f"Snapshot fondamental de {s['ticker']} :\n"
            f"- Prix actuel : {s['price']}\n"
            f"- PER : {s.get('pe_ratio')}\n"
            f"- Capitalisation : {s.get('market_cap_musd')} M$\n"
            f"- Secteur : {s.get('sector')}\n\n"
            f"Question de l'utilisateur : {context['query']}\n"
            "Donne ta stance fondamentale."
        )
