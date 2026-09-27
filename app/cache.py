"""Cache en mémoire avec TTL, volontairement minimaliste (pas de Redis pour
un hackathon solo). Évite de re-taper Finnhub/OpenAI à chaque clic quand tu
répètes ta démo sur le même ticker — utile aussi pour ne pas cramer le rate
limit gratuit de Finnhub pendant les tests.
"""
import time

_store: dict = {}


def cache_get(key: str):
    entry = _store.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        _store.pop(key, None)
        return None
    return value


def cache_set(key: str, value, ttl_seconds: int = 120) -> None:
    _store[key] = (time.time() + ttl_seconds, value)
