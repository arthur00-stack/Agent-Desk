"""Tests de base pour les parties critiques d'Alpha Desk :
- le fallback mock des données de marché est déterministe et cohérent
- le parsing JSON résiste aux réponses LLM "sales" (markdown, texte autour)
- l'orchestrateur bascule bien sur le chemin natif si Pipelex échoue
- le cache TTL fonctionne

Lancer avec : pytest -v
"""
import time

from app.cache import cache_get, cache_set
from app.llm_client import _extract_json
from app.tools.market_data import _mock_snapshot


def test_mock_snapshot_is_deterministic():
    """Le même ticker doit toujours donner le même snapshot factice (seedé),
    sinon les tests / répétitions de démo ne sont pas reproductibles."""
    a = _mock_snapshot("NVDA")
    b = _mock_snapshot("NVDA")
    assert a == b


def test_mock_snapshot_is_internally_consistent():
    s = _mock_snapshot("TSLA")
    assert s["week52_low"] < s["price"] < s["week52_high"] or s["price"] <= s["week52_low"]
    assert 0 <= s["pct_of_52w_range"] <= 100


def test_extract_json_plain():
    assert _extract_json('{"stance": "bullish", "confidence": 0.8}') == {
        "stance": "bullish",
        "confidence": 0.8,
    }


def test_extract_json_with_markdown_fences():
    raw = '```json\n{"stance": "bearish", "confidence": 0.6}\n```'
    assert _extract_json(raw) == {"stance": "bearish", "confidence": 0.6}


def test_extract_json_with_surrounding_text():
    raw = 'Voici mon analyse :\n{"stance": "neutral", "confidence": 0.5}\nVoilà.'
    assert _extract_json(raw) == {"stance": "neutral", "confidence": 0.5}


def test_extract_json_unparsable_never_crashes():
    result = _extract_json("ceci n'est pas du JSON du tout")
    assert result["stance"] == "neutral"
    assert "PARSE_ERROR" in result["reasoning"]


def test_cache_roundtrip_and_expiry():
    cache_set("test:key", {"v": 1}, ttl_seconds=1)
    assert cache_get("test:key") == {"v": 1}
    time.sleep(1.1)
    assert cache_get("test:key") is None


def test_orchestrator_falls_back_to_native_when_pipelex_fails(monkeypatch):
    """Le point le plus important pour la fiabilité en démo réelle : si
    Pipelex plante, la desk doit quand même répondre."""
    import app.orchestrator as orchestrator

    monkeypatch.setenv("USE_MOCK_LLM", "0")
    monkeypatch.setattr(
        orchestrator,
        "_run_desk_pipelex",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("pipelex cassé pour le test")),
    )
    monkeypatch.setattr(
        "app.llm_client.chat_json",
        lambda system, user, model=None: {
            "stance": "neutral", "confidence": 0.5, "reasoning": "test", "key_points": [],
            "recommendation": "HOLD", "memo": "test", "key_risks": [], "dissenting_views": "",
        },
    )
    monkeypatch.setattr(
        "app.tools.market_data.get_stock_snapshot",
        lambda ticker: _mock_snapshot(ticker),
    )
    monkeypatch.setattr("app.tools.web_search.get_recent_news", lambda q, max_items=5: ["actu test"])

    result = orchestrator.run_desk(query="test", ticker="NVDA")

    assert result["degraded_reason"] is not None
    assert "pipelex cassé" in result["degraded_reason"]
    assert result["memo"]["recommendation"] == "HOLD"
    assert len(result["stances"]) == 4  # macro, fundamentals, technical, risk
