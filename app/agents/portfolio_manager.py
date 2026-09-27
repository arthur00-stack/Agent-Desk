from app.agents.base_agent import BaseAgent


class PortfolioManagerAgent(BaseAgent):
    """Agent orchestrateur final : reçoit toutes les stances (y compris celle
    du Risk agent) et doit ARBITRER explicitement les désaccords pour produire
    une recommandation unique. C'est la brique de 'prise de décision' exigée
    par le règlement du hackathon."""

    name = "portfolio_manager"
    system_prompt = (
        "Tu es le PORTFOLIO MANAGER d'une desk de trading IA. Tu reçois les analyses de tes "
        "analystes (macro, fondamental, technique, risque) et tu dois trancher : produire une "
        "recommandation finale claire et un mémo synthétique, en arbitrant explicitement les "
        "désaccords. Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format : "
        '{"recommendation": "BUY|HOLD|SELL", "confidence": 0.0-1.0, "memo": "...", '
        '"key_risks": ["...", "..."], "dissenting_views": "..."}'
    )

    def build_prompt(self, context: dict) -> str:
        stances_txt = "\n".join(
            f"- {s['agent'].upper()} : {s['stance']} (confiance {s['confidence']})\n"
            f"  Raisonnement : {s['reasoning']}"
            for s in context["stances"]
        )
        return (
            f"Actif : {context['ticker']}\nQuestion initiale : {context['query']}\n\n"
            f"Analyses de l'équipe :\n{stances_txt}\n\n"
            "Synthétise ces analyses en une recommandation finale, en expliquant comment tu "
            "arbitres les désaccords entre analystes."
        )
