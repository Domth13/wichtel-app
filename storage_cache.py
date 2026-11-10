"""
Sehr kleiner In-Memory-Cache für Datenbank-Lesezugriffe.

- Kurze TTL (Standard 3 s), damit mehrere Aufrufe innerhalb eines
  Streamlit-Reruns nicht jeweils eine Datei-/Mongo-Abfrage auslösen.
- Gibt Deep-Copies zurück, damit Aufrufer keine Cache-Objekte verändern.
- Wird bei Schreibvorgängen gezielt invalidiert.
"""
import copy
import threading
import time
from typing import Any, Callable, Dict, Tuple

DEFAULT_TTL = 3.0

_lock = threading.RLock()
_cache: Dict[str, Tuple[float, Any]] = {}


class StorageUnavailableError(RuntimeError):
    """Datenquelle (JSON/MongoDB) ist momentan nicht erreichbar oder defekt."""


def cached(key: str, loader: Callable[[], Any], ttl: float = DEFAULT_TTL) -> Any:
    now = time.monotonic()
    with _lock:
        entry = _cache.get(key)
        if entry is not None and entry[0] > now:
            return copy.deepcopy(entry[1])

    value = loader()

    with _lock:
        _cache[key] = (time.monotonic() + ttl, copy.deepcopy(value))
    return copy.deepcopy(value)


def invalidate(*keys: str) -> None:
    with _lock:
        if not keys:
            _cache.clear()
            return
        for key in keys:
            _cache.pop(key, None)


def clear() -> None:
    invalidate()
