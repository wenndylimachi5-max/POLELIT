# clima_espacial.py
"""NASA DONKI Solar Space Weather endpoint.
Provides a helper to fetch recent Solar Energetic Particle (SEP) events
and recent Solar Flare (FLR) events of class M or X for the last 72 hours.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

NASA_API_URL_SEP = "https://api.nasa.gov/DONKI/SEP"
NASA_API_URL_FLR = "https://api.nasa.gov/DONKI/FLR"
DEFAULT_TIMEOUT = 10  # seconds


def _fetch_events(url: str, start: str, end: str) -> List[Dict[str, Any]]:
    """Fetch events from a DONKI endpoint.
    Returns a list of event dicts (empty if none or on error).
    """
    api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    params = {
        "startDate": start,
        "endDate": end,
        "api_key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
    except Exception:
        # Any problem (network, HTTP error, JSON decode) -> empty list
        return []


def obtener_clima_espacial() -> dict:
    """Return a summary of recent solar space‑weather activity.
    - Looks at SEP (Solar Energetic Particle) events.
    - Looks at FLR (Solar Flare) events, filtering for class M or X.
    Returns a dict with keys ``nivel``, ``mensaje`` and ``eventos``.
    """
    now = datetime.utcnow()
    start_dt = now - timedelta(days=2)  # 3 days inclusive = today + 2 previous days
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = now.strftime("%Y-%m-%d")

    sep_events = _fetch_events(NASA_API_URL_SEP, start_str, end_str)
    flr_events = _fetch_events(NASA_API_URL_FLR, start_str, end_str)

    # Filter flares of class M or X
    flr_mx = [e for e in flr_events if e.get("classType") in {"M", "X"}]

    if sep_events or flr_mx:
        # Build a combined list for the response – include type info
        combined: List[Dict[str, Any]] = []
        for e in sep_events:
            event = e.copy()
            event["tipo"] = "SEP"
            combined.append(event)
        for e in flr_mx:
            event = e.copy()
            event["tipo"] = "FLR_MX"
            combined.append(event)
        return {
            "nivel": "ALERTA",
            "mensaje": "Se detectaron eventos solares de alta energía en las últimas 72 h.",
            "eventos": combined,
        }
    else:
        return {
            "nivel": "NOMINAL",
            "mensaje": "Sin eventos severos de radiación solar en las últimas 72h.",
            "eventos": [],
        }
