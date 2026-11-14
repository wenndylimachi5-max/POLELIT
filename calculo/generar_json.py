"""generar_json.py — Genera los JSON finales para la web con horizonte real (LDEM 80 m) y Horizons."""
import json
import numpy as np
from pathlib import Path
from horizons import efemerides, SOL, TIERRA
from horizonte import horizonte, fraccion_sol

ANIO = 2027
INICIO, FIN = f"{ANIO}-01-01 00:00", f"{ANIO}-12-31 23:00"
SALIDA = Path(__file__).resolve().parent.parent / "web" / "data"
SALIDA.mkdir(parents=True, exist_ok=True)

SITIOS = [
    dict(id="cresta", nombre="Cresta Shackleton–de Gerlache", nombre_en="Shackleton–de Gerlache Ridge",
         lat=-89.44, lon=-137.0999, grupo="Polo sur"),
]

lista = []
for s in SITIOS:
    print(f"Calculando {s['nombre']}...")
    h0, az, hor = horizonte(s["lat"], s["lon"])
    fechas, saz, sel = efemerides(SOL, s["lat"], s["lon"], h0, INICIO, FIN)
    _, taz, tel = efemerides(TIERRA, s["lat"], s["lon"], h0, INICIO, FIN)

    per = lambda a: np.interp(np.asarray(a) % 360, np.append(az, 360), np.append(hor, hor[0]))
    frac = np.round(fraccion_sol(sel, per(saz)), 3)
    vis = (np.asarray(tel) > per(taz)).astype(int)

    datos = dict(
        id=s["id"], nombre=s["nombre"], nombre_en=s["nombre_en"],
        lat=s["lat"], lon=s["lon"], altura_m=round(float(h0)),
        inicio=fechas[0], paso_horas=1, horas=len(fechas),
        horizonte=dict(az=az.tolist(), el=[round(float(x), 3) for x in hor]),
        sol=dict(az=[round(x, 3) for x in saz], el=[round(x, 3) for x in sel], frac=frac.tolist()),
        tierra=dict(az=[round(x, 3) for x in taz], el=[round(x, 3) for x in tel], visible=vis.tolist()),
        resumen=dict(luz_pct=round(float(frac.mean() * 100), 1), tierra_pct=round(float(vis.mean() * 100), 1)),
        terreno=None,   # pendiente y sombra permanente: se completa después
    )
    with open(SALIDA / f"{s['id']}.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))
    lista.append({k: datos[k] for k in ("id", "nombre", "nombre_en", "lat", "lon", "altura_m")} | {"grupo": s["grupo"]})
    print(f"  luz {datos['resumen']['luz_pct']}% | Tierra {datos['resumen']['tierra_pct']}%")

with open(SALIDA / "sitios.json", "w", encoding="utf-8") as f:
    json.dump(dict(anio=ANIO, paso_horas=1, horas=len(fechas), sitios=lista), f, ensure_ascii=False, indent=2)
print("Listo: JSON en web/data/")