"""Snapshot de marché pour un ticker, via l'API officielle Finnhub (gratuite,
documentée, pas de scraping). Fallback automatique sur des données factices
si la clé API manque, si le réseau échoue, ou si le rate limit est atteint —
même logique de résilience que pour les news.

Note technique : l'endpoint /stock/candle (historique de prix) est verrouillé
sur le plan gratuit Finnhub, donc pas de vraies moyennes mobiles possibles.
On utilise à la place la distance au plus haut/bas sur 52 semaines (dispo sur
/stock/metric en gratuit) : c'est un facteur momentum reconnu en finance
empirique (52-week high effect), pas juste un pis-aller technique.
"""
import os
import random

import requests

from app.cache import cache_get, cache_set

FINNHUB_BASE = "https://finnhub.io/api/v1"


def get_stock_snapshot(ticker: str) -> dict:
    cached = cache_get(f"snapshot:{ticker}")
    if cached is not None:
        return cached

    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        result = _mock_snapshot(ticker)
        cache_set(f"snapshot:{ticker}", result, ttl_seconds=30)
        return result

    try:
        quote = _get(f"{FINNHUB_BASE}/quote", {"symbol": ticker, "token": api_key})
        profile = _get(f"{FINNHUB_BASE}/stock/profile2", {"symbol": ticker, "token": api_key})
        metrics = _get(
            f"{FINNHUB_BASE}/stock/metric",
            {"symbol": ticker, "metric": "all", "token": api_key},
        ).get("metric", {})

        price = quote.get("c")
        prev_close = quote.get("pc")
        if not price or not prev_close:
            raise ValueError("quote vide ou ticker invalide")

        change_pct = round((price / prev_close - 1) * 100, 2)
        week52_high = metrics.get("52WeekHigh")
        week52_low = metrics.get("52WeekLow")

        pct_of_range = None
        dist_from_high_pct = None
        if week52_high and week52_low and week52_high != week52_low:
            pct_of_range = round((price - week52_low) / (week52_high - week52_low) * 100, 1)
        if week52_high:
            dist_from_high_pct = round((price / week52_high - 1) * 100, 2)

        result = {
            "ticker": ticker,
            "price": round(price, 2),
            "change_pct": change_pct,
            "day_high": quote.get("h"),
            "day_low": quote.get("l"),
            "week52_high": week52_high,
            "week52_low": week52_low,
            "pct_of_52w_range": pct_of_range,
            "distance_from_52w_high_pct": dist_from_high_pct,
            "pe_ratio": metrics.get("peBasicExclExtraTTM") or metrics.get("peNormalizedAnnual"),
            "market_cap_musd": profile.get("marketCapitalization"),  # en millions USD
            "sector": profile.get("finnhubIndustry", "N/A"),
            "source": "finnhub (API officielle, plan gratuit)",
        }
        cache_set(f"snapshot:{ticker}", result, ttl_seconds=120)
        return result
    except Exception:
        result = _mock_snapshot(ticker)
        cache_set(f"snapshot:{ticker}", result, ttl_seconds=30)
        return result


def _get(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()


def _mock_snapshot(ticker: str) -> dict:
    rng = random.Random(ticker)
    price = round(rng.uniform(50, 400), 2)
    week52_high = round(price * rng.uniform(1.05, 1.35), 2)
    week52_low = round(price * rng.uniform(0.65, 0.95), 2)
    return {
        "ticker": ticker,
        "price": price,
        "change_pct": round(rng.uniform(-3, 3), 2),
        "day_high": round(price * 1.01, 2),
        "day_low": round(price * 0.99, 2),
        "week52_high": week52_high,
        "week52_low": week52_low,
        "pct_of_52w_range": round((price - week52_low) / (week52_high - week52_low) * 100, 1),
        "distance_from_52w_high_pct": round((price / week52_high - 1) * 100, 2),
        "pe_ratio": round(rng.uniform(10, 40), 1),
        "market_cap_musd": rng.randint(5_000, 900_000),
        "sector": "Technology",
        "source": "mock (offline demo data)",
    }
