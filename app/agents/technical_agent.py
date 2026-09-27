from app.agents.base_agent import BaseAgent

_JSON_FORMAT = (
    'Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format : '
    '{"stance": "bullish|bearish|neutral", "confidence": 0.0-1.0, '
    '"reasoning": "...", "key_points": ["...", "..."]}'
)


class TechnicalAgent(BaseAgent):
    name = "technical"
    system_prompt = (
        "Tu es l'analyste TECHNIQUE d'une desk de trading IA. Tu évalues le momentum du titre à "
        "partir de sa position dans son range 52 semaines et de sa variation récente — tu connais "
        "l'effet '52-week high momentum' (les titres proches de leur plus haut sur 52 semaines ont "
        "tendance à surperformer à court terme) et tu t'en sers pour juger le point d'entrée/sortie. "
        + _JSON_FORMAT
    )

    def build_prompt(self, context: dict) -> str:
        s = context["snapshot"]
        return (
            f"Données techniques de {s['ticker']} :\n"
            f"- Prix actuel : {s['price']}\n"
            f"- Variation du jour : {s['change_pct']}%\n"
            f"- Plus haut 52 semaines : {s['week52_high']}\n"
            f"- Plus bas 52 semaines : {s['week52_low']}\n"
            f"- Position dans le range 52 semaines : {s['pct_of_52w_range']}%\n"
            f"- Distance au plus haut 52 semaines : {s['distance_from_52w_high_pct']}%\n\n"
            f"Question de l'utilisateur : {context['query']}\n"
            "Donne ta stance technique en t'appuyant sur ces chiffres."
        )
