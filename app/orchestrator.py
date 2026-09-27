"""Orchestration de la desk.

Trois chemins possibles :
1. USE_MOCK_LLM=1           -> chemin Python natif, réponses factices
   (zéro appel externe, filet de sécurité pour répéter/filmer hors-ligne)
2. Mode réel, Pipelex OK    -> le cœur du raisonnement passe par le
   pipeline Pipelex (.mthds), "workflow agentique déterministe"
3. Mode réel, Pipelex échoue -> fallback automatique vers le même chemin
   Python natif que (1), mais avec de VRAIS appels LLM (chat_json ne mock
   que si USE_MOCK_LLM=1, qui n'est pas le cas ici). Ce filet de sécurité
   supplémentaire évite qu'un souci Pipelex (clé, quota, bug CLI) ne casse
   la démo live : le produit continue de répondre avec de vraies données et
   un vrai raisonnement, juste sans passer par Pipelex ce coup-ci.
"""
import logging
import os

from app.tools.market_data import get_stock_snapshot
from app.tools.web_search import get_recent_news

logger = logging.getLogger("alpha_desk.orchestrator")


def run_desk(query: str, ticker: str) -> dict:
    snapshot = get_stock_snapshot(ticker)
    news = get_recent_news(f"{ticker} stock", max_items=5)

    degraded_reason = None
    if os.environ.get("USE_MOCK_LLM") == "1":
        result = _run_desk_native(query, ticker, snapshot, news)
    else:
        try:
            result = _run_desk_pipelex(query, ticker, snapshot, news)
        except Exception as exc:  # noqa: BLE001 - on ne laisse jamais planter la démo
            logger.warning("Pipelex a échoué, fallback natif : %s", exc)
            degraded_reason = str(exc)[:300]
            result = _run_desk_native(query, ticker, snapshot, news)

    return {
        "ticker": ticker,
        "query": query,
        "snapshot": snapshot,
        "news": news,
        "stances": result["stances"],
        "memo": result["memo"],
        "degraded_reason": degraded_reason,  # None si tout s'est bien passé
    }


def _run_desk_pipelex(query: str, ticker: str, snapshot: dict, news: list) -> dict:
    from app.pipelex_pipeline import run_desk_via_pipelex

    return run_desk_via_pipelex(ticker=ticker, query=query, snapshot=snapshot, news=news)


def _run_desk_native(query: str, ticker: str, snapshot: dict, news: list) -> dict:
    """Chemin 100% Python. Fait de VRAIS appels LLM sauf si USE_MOCK_LLM=1
    (c'est chat_json, appelé par chaque agent, qui gère ce détail)."""
    from app.agents.macro_agent import MacroAgent
    from app.agents.fundamentals_agent import FundamentalsAgent
    from app.agents.technical_agent import TechnicalAgent
    from app.agents.risk_agent import RiskAgent
    from app.agents.portfolio_manager import PortfolioManagerAgent

    base_context = {
        "query": query,
        "ticker": ticker,
        "snapshot": snapshot,
        "news": news,
        "sector": snapshot.get("sector"),
    }

    specialists = [MacroAgent(), FundamentalsAgent(), TechnicalAgent()]
    stances = [agent.analyze(base_context) for agent in specialists]

    risk_stance = RiskAgent().analyze({**base_context, "stances": stances})
    stances.append(risk_stance)

    memo = PortfolioManagerAgent().analyze({**base_context, "stances": stances})

    return {"stances": stances, "memo": memo}
