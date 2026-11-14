# Prueba completa de Horizons desde la Cresta: Sol, Tierra y un año entero
import requests

URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def consultar(cuerpo, inicio, fin, paso):
    params = {
        "format": "text",
        "COMMAND": f"'{cuerpo}'",                  # 10 = Sol, 399 = Tierra
        "CENTER": "'coord@301'",                   # observador en la superficie de la Luna
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": "'222.9001,-89.44,1.958'",   # Cresta: lon Este, lat, altura en km
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "START_TIME": f"'{inicio}'",
        "STOP_TIME": f"'{fin}'",
        "STEP_SIZE": f"'{paso}'",
        "QUANTITIES": "'4'",                       # acimut y elevación
    }
    t = requests.get(URL, params=params, timeout=120).text
    if "$$SOE" not in t:
        print(t[:3000])                            # si falla, muestra el error
        return []
    filas = t[t.find("$$SOE") + 5:t.find("$$EOE")].strip().splitlines()
    return filas


# 1 y 2) Sol y Tierra, 4 horas
for nombre, cuerpo in [("SOL", "10"), ("TIERRA", "399")]:
    print(f"\n=== {nombre} ===")
    for fila in consultar(cuerpo, "2027-01-14 11:00", "2027-01-14 14:00", "1 h"):
        print(fila)

# 3) Un año entero, hora por hora (solo cuenta las filas)
filas = consultar("10", "2027-01-01 00:00", "2027-12-31 23:00", "1 h")
print(f"\n=== AÑO ENTERO (Sol) ===\nFilas recibidas: {len(filas)} (esperadas: 8760)")
if filas:
    print("Primera:", filas[0])
    print("Última: ", filas[-1])