from app.agents.base_agent import BaseAgent

_JSON_FORMAT = (
    'Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format : '
    '{"stance": "bullish|bearish|neutral", "confidence": 0.0-1.0, '
    '"reasoning": "...", "key_points": ["...", "..."]}'
)


class RiskAgent(BaseAgent):
    """Agent 'critique' : ne donne pas une opinion directionnelle indépendante,
    mais challenge les stances des 3 autres agents (contradictions, biais,
    risques non mentionnés). C'est ce qui apporte la vraie logique de débat
    multi-agents, pas juste 3 appels LLM en parallèle."""

    name = "risk"
    system_prompt = (
        "Tu es l'analyste RISQUE / COMPLIANCE d'une desk de trading IA. Ton rôle est de "
        "challenger les autres analystes : repérer les contradictions entre leurs analyses, "
        "les biais, et les risques non mentionnés (volatilité, date de résultats proche, "
        "concentration sectorielle, liquidité). Ici 'stance' représente ton niveau de confort "
        "global avec la thèse (bullish = peu de risque, bearish = risque élevé). " + _JSON_FORMAT
    )

    def build_prompt(self, context: dict) -> str:
        stances_txt = "\n".join(
            f"- {s['agent']} : {s['stance']} (confiance {s['confidence']}) — {s['reasoning']}"
            for s in context["stances"]
        )
        return (
            f"Actif : {context['ticker']}\n\nAnalyses des autres agents :\n{stances_txt}\n\n"
            "Identifie les risques et contradictions, et donne ton verdict risque."
        )
