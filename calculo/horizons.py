"""
horizons.py — Consulta JPL Horizons (recurso oficial del desafío).
Devuelve acimut y elevación del Sol o la Tierra vistos desde un punto de la Luna, hora por hora.
JPL Horizons: https://ssd.jpl.nasa.gov/horizons/
"""
import requests

URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
SOL, TIERRA = "10", "399"          # códigos de Horizons


def efemerides(cuerpo, lat, lon, altura_m, inicio, fin, paso="1 h"):
    """lat y lon en grados (oeste = negativo). Devuelve (fechas, acimut, elevacion)."""
    params = {
        "format": "text",
        "COMMAND": f"'{cuerpo}'",
        "CENTER": "'coord@301'",                                    # observador en la Luna (301)
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{lon % 360:.6f},{lat:.6f},{altura_m / 1000:.4f}'",   # lon Este, lat, altura en km
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "START_TIME": f"'{inicio}'",
        "STOP_TIME": f"'{fin}'",
        "STEP_SIZE": f"'{paso}'",
        "QUANTITIES": "'4'",                                        # acimut y elevación
    }
    texto = requests.get(URL, params=params, timeout=120).text
    if "$$SOE" not in texto:
        raise RuntimeError("Horizons no devolvió datos:\n" + texto[:2000])
    filas = texto[texto.find("$$SOE") + 5:texto.find("$$EOE")].strip().splitlines()
    fechas, az, el = [], [], []
    for fila in filas:
        p = fila.split()
        fechas.append(p[0] + " " + p[1])        # fecha y hora
        az.append(float(p[-2]))                 # los dos últimos números: acimut y elevación
        el.append(float(p[-1]))                 # (la columna de marcas del medio varía)
    return fechas, az, el