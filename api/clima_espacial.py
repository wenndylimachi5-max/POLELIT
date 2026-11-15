"""Actividad solar registrada por NASA DONKI en las últimas 72 horas."""

import os
import re
from datetime import datetime, timedelta, timezone

import requests

NASA_API_URL_SEP = "https://api.nasa.gov/DONKI/SEP"
NASA_API_URL_FLR = "https://api.nasa.gov/DONKI/FLR"
DEFAULT_TIMEOUT = 10


def _fetch_events(url, start, end):
    params = {
        "startDate": start,
        "endDate": end,
        "api_key": os.getenv("NASA_API_KEY", "DEMO_KEY"),
    }
    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        events = response.json()
    except (requests.RequestException, ValueError):
        return None
    return events if isinstance(events, list) else None


def obtener_clima_espacial() -> dict:
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(hours=72)
    eventos = []
    fuentes_incompletas = []
    fuentes = (
        ("SEP", NASA_API_URL_SEP, "eventTime"),
        ("FLR", NASA_API_URL_FLR, "beginTime"),
    )
    for nombre, url, campo_fecha in fuentes:
        registros = _fetch_events(url, desde.date().isoformat(), hasta.date().isoformat())
        if registros is None:
            fuentes_incompletas.append(nombre)
            continue
        completa = True
        for registro in registros:
            try:
                instante = datetime.fromisoformat(registro[campo_fecha].replace("Z", "+00:00"))
                if instante.tzinfo is None:
                    instante = instante.replace(tzinfo=timezone.utc)
                if not desde <= instante <= hasta:
                    continue
                if nombre == "FLR":
                    clase = registro["classType"].strip().upper()
                    if not re.fullmatch(r"[ABCMX](?:\d+(?:\.\d+)?)?", clase):
                        completa = False
                        continue
                    if clase[0] not in "MX":
                        continue
            except (KeyError, ValueError, TypeError, AttributeError):
                completa = False
                continue
            eventos.append({**registro, "tipo": "SEP" if nombre == "SEP" else "FLR_MX"})
        if not completa:
            fuentes_incompletas.append(nombre)

    if eventos:
        nivel, mensaje = "ALERTA", "DONKI registró actividad solar de alta energía en las últimas 72 h."
    elif fuentes_incompletas:
        nivel, mensaje = "SIN_DATOS", "Faltan datos de DONKI para evaluar las últimas 72 h."
    else:
        nivel, mensaje = "NOMINAL", "DONKI no registró eventos SEP ni llamaradas M o X en las últimas 72 h."
    return {
        "nivel": nivel,
        "mensaje": mensaje,
        "eventos": eventos,
        "datos_completos": not fuentes_incompletas,
        "fuentes_incompletas": fuentes_incompletas,
    }
