"""
ejemplo_json.py — Genera un JSON de ejemplo para la web (formato definitivo).
Datos reales de Horizons para la Cresta; horizonte todavía plano (0°).
"""
import os, json, math
from horizons import efemerides, SOL, TIERRA

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(CARPETA, "web", "data")
os.makedirs(SALIDA, exist_ok=True)

SITIO = dict(id="cresta", nombre="Cresta de conexión", nombre_en="Connecting Ridge",
             lat=-89.44, lon=-137.0999, altura_m=1958, grupo="Polo sur")
INICIO, FIN = "2027-01-01 00:00", "2027-12-31 23:00"
RADIO_SOL = 0.2666     # radio aparente del Sol en grados (aproximado; se ajusta en el cálculo final)

fechas, sol_az, sol_el = efemerides(SOL, SITIO["lat"], SITIO["lon"], SITIO["altura_m"], INICIO, FIN)
_, tie_az, tie_el = efemerides(TIERRA, SITIO["lat"], SITIO["lon"], SITIO["altura_m"], INICIO, FIN)

hor_az = list(range(360))
hor_el = [0.0] * 360                        # PROVISORIO: horizonte plano (después, montañas LOLA)


def fraccion_sol(el, h):
    """Fracción visible del disco solar (0 a 1) con el horizonte h en esa dirección."""
    t = max(-1.0, min(1.0, (h - el) / RADIO_SOL))
    return (math.acos(t) - t * math.sqrt(1 - t * t)) / math.pi


sol_frac = [round(fraccion_sol(e, hor_el[int(a) % 360]), 3) for a, e in zip(sol_az, sol_el)]
tie_vis = [1 if e > hor_el[int(a) % 360] else 0 for a, e in zip(tie_az, tie_el)]

datos = dict(
    id=SITIO["id"], nombre=SITIO["nombre"], nombre_en=SITIO["nombre_en"],
    lat=SITIO["lat"], lon=SITIO["lon"], altura_m=SITIO["altura_m"],
    inicio=fechas[0], paso_horas=1, horas=len(fechas),
    horizonte=dict(az=hor_az, el=hor_el),
    sol=dict(az=[round(x, 2) for x in sol_az], el=[round(x, 3) for x in sol_el], frac=sol_frac),
    tierra=dict(az=[round(x, 2) for x in tie_az], el=[round(x, 3) for x in tie_el], visible=tie_vis),
    resumen=dict(luz_pct=round(100 * sum(sol_frac) / len(sol_frac), 1),
                 tierra_pct=round(100 * sum(tie_vis) / len(tie_vis), 1)),
    terreno=None,                            # se completa después (pendiente, sombras)
)
with open(os.path.join(SALIDA, "cresta.json"), "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))

lista = dict(anio=2027, paso_horas=1, horas=len(fechas),
             sitios=[{k: SITIO[k] for k in ("id", "nombre", "nombre_en", "lat", "lon", "altura_m", "grupo")}])
with open(os.path.join(SALIDA, "sitios.json"), "w", encoding="utf-8") as f:
    json.dump(lista, f, ensure_ascii=False, indent=2)

print(f"Listo: {len(fechas)} horas | luz {datos['resumen']['luz_pct']}% | Tierra {datos['resumen']['tierra_pct']}% (horizonte plano)")