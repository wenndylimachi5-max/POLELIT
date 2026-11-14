"""
horizons.py — Posición del Sol y la Tierra vistas desde un punto de la Luna.

Consulta la API de JPL Horizons (NASA) y devuelve, para cada instante,
el azimut y la elevación del cuerpo pedido vistos desde el sitio.

Fuente: https://ssd.jpl.nasa.gov/horizons/ (documentación de la API: https://ssd-api.jpl.nasa.gov/doc/horizons.html)
"""
import requests

URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
SOL, TIERRA = "10", "399"          # códigos de Horizons: 10 = Sol, 399 = Tierra


def efemerides(cuerpo, lat, lon, altura_m, inicio, fin, paso="1 h"):
    """
    cuerpo    : SOL o TIERRA
    lat, lon  : coordenadas del sitio en grados (lon negativa = oeste)
    altura_m  : altura del sitio en metros
    inicio/fin: fechas "AAAA-MM-DD hh:mm" (UTC)
    paso      : intervalo entre datos
    Devuelve tres listas: fechas, azimut (°) y elevación (°).
    """
    params = {
        "format": "text",
        "COMMAND": f"'{cuerpo}'",
        "CENTER": "'coord@301'",                     # observador sobre la superficie de la Luna (301)
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{lon % 360:.6f},{lat:.6f},{altura_m / 1000:.4f}'",  # lon este 0–360, lat, altura en km
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "START_TIME": f"'{inicio}'",
        "STOP_TIME": f"'{fin}'",
        "STEP_SIZE": f"'{paso}'",
        "QUANTITIES": "'4'",                         # 4 = azimut y elevación aparentes
    }
    texto = requests.get(URL, params=params, timeout=120).text
    if "$$SOE" not in texto:
        raise RuntimeError("Horizons no devolvió datos:\n" + texto[:2000])

    # Los datos están entre las marcas $$SOE (inicio) y $$EOE (fin)
    filas = texto[texto.find("$$SOE") + 5:texto.find("$$EOE")].strip().splitlines()
    fechas, az, el = [], [], []
    for fila in filas:
        p = fila.split()
        fechas.append(p[0] + " " + p[1])             # fecha y hora
        az.append(float(p[-2]))                      # los dos últimos valores de cada fila:
        el.append(float(p[-1]))                      # azimut y elevación
    return fechas, az, el