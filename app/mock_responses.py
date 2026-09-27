"""Réponses factices pour USE_MOCK_LLM=1.

À utiliser pour :
- développer/tester sans consommer de crédits API
- répéter et FILMER la démo sans dépendre d'internet ou de l'API le jour J
"""
import random


def get_mock_response(system_prompt: str) -> dict:
    if "PORTFOLIO MANAGER" in system_prompt:
        return {
            "recommendation": random.choice(["BUY", "HOLD", "SELL"]),
            "confidence": round(random.uniform(0.55, 0.85), 2),
            "memo": (
                "[MOCK] Le titre présente un momentum technique positif mais une valorisation "
                "tendue ; le contexte macro reste incertain à court terme. Position à taille "
                "réduite recommandée, à réévaluer après la prochaine publication de résultats."
            ),
            "key_risks": [
                "Publication de résultats dans les prochaines semaines",
                "Valorisation élevée par rapport au secteur",
            ],
            "dissenting_views": (
                "[MOCK] L'analyste fondamental reste prudent malgré un signal technique positif."
            ),
        }
    if "RISQUE" in system_prompt or "COMPLIANCE" in system_prompt:
        return {
            "stance": random.choice(["bullish", "neutral", "bearish"]),
            "confidence": round(random.uniform(0.4, 0.7), 2),
            "reasoning": (
                "[MOCK] Contradiction potentielle entre signal technique et signal fondamental ; "
                "volatilité récente au-dessus de la moyenne du secteur."
            ),
            "key_points": [
                "Volatilité au-dessus de la moyenne",
                "Date de résultats proche",
                "Concentration sectorielle",
            ],
        }
    return {
        "stance": random.choice(["bullish", "neutral", "bearish"]),
        "confidence": round(random.uniform(0.5, 0.9), 2),
        "reasoning": "[MOCK] Analyse générée hors-ligne pour la démo (USE_MOCK_LLM=1).",
        "key_points": ["Point clé 1", "Point clé 2"],
    }
