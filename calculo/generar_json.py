"""
generar_json.py — Genera los archivos que lee la web (carpeta web/data/).

Para cada sitio de la lista SITIOS:
  1. Calcula el horizonte con el mapa LOLA de 80 m (horizonte.py).
  2. Obtiene de JPL Horizons la posición del Sol y la Tierra, hora por hora, en el año ANIO (horizons.py).
  3. Calcula en cada hora qué fracción del Sol se ve y si la Tierra está sobre el horizonte.
  4. Guarda <id>.json con los resultados y agrega el sitio a sitios.json.

Uso: python calculo/generar_json.py
"""
import json
import numpy as np
from pathlib import Path
from horizons import efemerides, SOL, TIERRA
from horizonte import horizonte, fraccion_sol

ANIO = 2027
INICIO, FIN = f"{ANIO}-01-01 00:00", f"{ANIO}-12-31 23:00"
SALIDA = Path(__file__).resolve().parent.parent / "web" / "data"
SALIDA.mkdir(parents=True, exist_ok=True)

# Sitios a calcular (lat/lon en grados, lon negativa = oeste)
# Coordenadas: punto más alto a ≤4 km del centro de cada mapa LOLA de 5 m (Barker 2020), ver centros_5m.py
SITIOS = [
    dict(id="cresta", nombre="Cresta Shackleton–de Gerlache", nombre_en="Shackleton–de Gerlache Ridge",
         lat=-89.44, lon=-137.0999, grupo="Polo sur"),        # Site01 (Connecting ridge)
    dict(id="shackleton", nombre="Borde de Shackleton", nombre_en="Shackleton Rim",
         lat=-89.7804, lon=-156.1970, grupo="Polo sur"),      # Site04 (Shackleton rim)
]

lista = []
for s in SITIOS:
    print(f"Calculando {s['nombre']}...")

    # Horizonte del sitio y posiciones del Sol y la Tierra
    h0, az, hor = horizonte(s["lat"], s["lon"])
    fechas, saz, sel = efemerides(SOL, s["lat"], s["lon"], h0, INICIO, FIN)
    _, taz, tel = efemerides(TIERRA, s["lat"], s["lon"], h0, INICIO, FIN)

    # Elevación del horizonte en el azimut exacto del Sol y la Tierra (interpolada)
    per = lambda a: np.interp(np.asarray(a) % 360, np.append(az, 360), np.append(hor, hor[0]))
    frac = np.round(fraccion_sol(sel, per(saz)), 3)        # 0 a 1: fracción del Sol visible
    vis = (np.asarray(tel) > per(taz)).astype(int)         # 1 = Tierra visible, 0 = oculta

    datos = dict(
        id=s["id"], nombre=s["nombre"], nombre_en=s["nombre_en"],
        lat=s["lat"], lon=s["lon"], altura_m=round(float(h0)),
        inicio=fechas[0], paso_horas=1, horas=len(fechas),
        horizonte=dict(az=az.tolist(), el=[round(float(x), 3) for x in hor]),
        sol=dict(az=[round(x, 3) for x in saz], el=[round(x, 3) for x in sel], frac=frac.tolist()),
        tierra=dict(az=[round(x, 3) for x in taz], el=[round(x, 3) for x in tel], visible=vis.tolist()),
        resumen=dict(luz_pct=round(float(frac.mean() * 100), 1),
                     tierra_pct=round(float(vis.mean() * 100), 1)),
        terreno=None,   # pendiente y sombra permanente (pendiente de cálculo)
    )

    # Archivo del sitio (compacto para que pese menos)
    with open(SALIDA / f"{s['id']}.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))

    lista.append({k: datos[k] for k in ("id", "nombre", "nombre_en", "lat", "lon", "altura_m")} | {"grupo": s["grupo"]})
    print(f"  altura {datos['altura_m']} m | luz {datos['resumen']['luz_pct']}% | Tierra {datos['resumen']['tierra_pct']}%")

# Lista general de sitios
with open(SALIDA / "sitios.json", "w", encoding="utf-8") as f:
    json.dump(dict(anio=ANIO, paso_horas=1, horas=len(fechas), sitios=lista), f, ensure_ascii=False, indent=2)
print("Listo: JSON en web/data/")