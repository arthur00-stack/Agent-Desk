from app.agents.base_agent import BaseAgent

_JSON_FORMAT = (
    'Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format : '
    '{"stance": "bullish|bearish|neutral", "confidence": 0.0-1.0, '
    '"reasoning": "...", "key_points": ["...", "..."]}'
)


class MacroAgent(BaseAgent):
    name = "macro"
    system_prompt = (
        "Tu es l'analyste MACRO d'une desk de trading IA. Tu évalues l'environnement "
        "macroéconomique (taux, inflation, sentiment de marché, dynamique du secteur) et son "
        "impact probable sur l'actif étudié. " + _JSON_FORMAT
    )

    def build_prompt(self, context: dict) -> str:
        news = "\n".join(f"- {n}" for n in context.get("news", []))
        return (
            f"Actif étudié : {context['ticker']} (secteur : {context.get('sector', 'inconnu')}).\n"
            f"Actualités récentes :\n{news}\n\n"
            f"Question de l'utilisateur : {context['query']}\n"
            "Donne ta stance macro sur cet actif."
        )
