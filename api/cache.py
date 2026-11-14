import os
import pickle
from typing import Any

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(key: str) -> str:
    safe_key = key.replace('/', '_').replace(' ', '_')
    return os.path.join(CACHE_DIR, f"{safe_key}.pkl")

def load(key: str) -> Any:
    path = _cache_path(key)
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None

def save(key: str, data: Any) -> None:
    path = _cache_path(key)
    try:
        with open(path, "wb") as f:
            pickle.dump(data, f)
    except Exception:
        pass
