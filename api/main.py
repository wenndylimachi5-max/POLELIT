# FastAPI server for the lunar analysis backend

"""Main entry point for the API.

All heavy assets (GeoTIFFs, pre‑computed efemérides cache) are loaded once in the
lifespan context manager. The endpoints expose the exact JSON schema required by
the existing web UI and add the scientific metadata block.
"""

import json
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pydantic import BaseModel

import requests
import numpy as np
import rasterio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api import cache, motor
from calculo.horizons import efemerides, SOL, TIERRA

# ---------------------------------------------------------------------------
# FastAPI app with modern lifespan (async context manager)
# ---------------------------------------------------------------------------
app = FastAPI(title="PoleLit Lunar Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple TTL cache for mission context (1 h)
_CONTEXT_CACHE_TTL = 3600  # seconds

def _context_cache_key(site_id: str) -> str:
    return f"context_{site_id}"

def _is_fresh(entry: Dict[str, Any]) -> bool:
    ts = entry.get("_ts")
    return ts is not None and (time.time() - ts) < _CONTEXT_CACHE_TTL

# ---------------------------------------------------------------------------
# Lifespan – ensure heavy assets are loaded once
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    # Force loading of rasters inside motor (lazy functions will cache internally)
    motor._cargar_80()  # type: ignore[attr-defined]
    motor._load_5m_maps()  # type: ignore[attr-defined]
    return

# ---------------------------------------------------------------------------
# Helper: cached efemerides for a given body and coordinate
# ---------------------------------------------------------------------------
def _efemerides_cached(body: str, lat: float, lon: float, h0: float) -> tuple:
    key = f"efem_{body}_{lat:.4f}_{lon:.4f}_{h0:.1f}"
    cached = cache.load(key)
    if cached:
        return cached
    # Not cached – fetch from JPL Horizons (full year 2027)
    start = "2027-01-01 00:00"
    end = "2027-12-31 23:00"
    fechas, az, el = efemerides(body, lat, lon, h0, start, end)
    data = (fechas, az, el)
    cache.save(key, data)
    return data

# ---------------------------------------------------------------------------
# Utilities copied from generar_json (lightweight helpers)
# ---------------------------------------------------------------------------
def horas_hasta_cambio(arr: List[bool]) -> List[Any]:
    out = [None] * len(arr)
    proximo = None
    for i in range(len(arr) - 1, -1, -1):
        if not arr[i]:
            proximo, out[i] = i, 0
        elif proximo is not None:
            out[i] = proximo - i
    return out

def racha_maxima(arr: List[bool]) -> int:
    maxo = cur = 0
    for v in arr:
        cur = cur + 1 if v else 0
        maxo = max(maxo, cur)
    return maxo

# ---------------------------------------------------------------------------
# Endpoint: /api/analizar
# ---------------------------------------------------------------------------
@app.get("/api/analizar")
def analizar(
    lat: float = Query(..., ge=-90, le=-80),
    lon: float = Query(..., ge=-180, le=360),
) -> Dict[str, Any]:
    # Normalizar longitud al rango -180..180 que espera el motor
    lon_norm = ((lon + 180) % 360) - 180
    # Compute horizon with multi‑resolution engine
    h0, az_arr, hor_arr, resol = motor.horizonte_optimizado(lat, lon_norm)

    # Load efemérides (cached) for Sun and Earth
    fechas, saz, sel = _efemerides_cached(SOL, lat, lon_norm, h0)
    _, taz, tel = _efemerides_cached(TIERRA, lat, lon_norm, h0)

    # Interpolación del horizonte en azimut del Sol/Tierra
    per = lambda a: np.interp(np.asarray(a) % 360, np.append(az_arr, 360), np.append(hor_arr, hor_arr[0]))
    # fraccion_sol is defined in calculo.horizonte; import lazily to avoid circular imports
    from calculo.horizonte import fraccion_sol
    frac = np.round(fraccion_sol(sel, per(saz)), 3)
    vis_t = (np.asarray(tel) > per(taz)).astype(int)

    sol_vis = (frac > 0).tolist()
    tie_vis = (vis_t > 0).tolist()

    datos: Dict[str, Any] = {
        "id": "dynamic",
        "nombre": "Dynamic Site",
        "nombre_en": "Dynamic Site",
        "lat": lat,
        "lon": lon,
        "altura_m": round(float(h0)),
        "inicio": fechas[0],
        "paso_horas": 1,
        "horas": len(fechas),
        "horizonte": {"az": az_arr.tolist(), "el": [round(float(v), 3) for v in hor_arr]},
        "sol": {
            "az": [round(x, 3) for x in saz],
            "el": [round(x, 3) for x in sel],
            "frac": frac.tolist(),
            "hasta_puesta": horas_hasta_cambio(sol_vis),
            "hasta_salida": horas_hasta_cambio([not v for v in sol_vis]),
        },
        "tierra": {
            "az": [round(x, 3) for x in taz],
            "el": [round(x, 3) for x in tel],
            "visible": vis_t.tolist(),
            "hasta_puesta": horas_hasta_cambio(tie_vis),
            "hasta_salida": horas_hasta_cambio([not v for v in tie_vis]),
        },
        "resumen": {
            "luz_pct": round(float(np.mean(frac) * 100), 1),
            "tierra_pct": round(float(np.mean(vis_t) * 100), 1),
            "max_oscuridad_h": racha_maxima([not v for v in sol_vis]),
            "max_sin_tierra_h": racha_maxima([not v for v in tie_vis]),
        },
        "terreno": motor.terreno(lat, lon),
        "metadatos_cientificos": {
            "resolucion_cercana": resol,
            "incertidumbre_altura_rms_m": "0.30–0.50",
            "incertidumbre_pendiente_deg": "1.5–2.5",
            "advertencia_falsos_positivos_psr_%": "30–50",
        },
    }
    return datos

# ---------------------------------------------------------------------------
# Endpoint: /api/terreno-3d
# ---------------------------------------------------------------------------
@app.get("/api/terreno-3d")
def terreno_3d(
    lat: float = Query(..., ge=-90, le=-80),
    lon: float = Query(..., ge=-180, le=360),
    radio_km: float = Query(2.0, gt=0),
) -> Dict[str, Any]:
    # Normalizar longitud al rango -180..180 esperado por motor
    lon_norm = ((lon + 180) % 360) - 180
    # Determine which raster to use (5 m if point inside any 5 m map, else 80 m)
    # Re‑load the 5 m map dictionary to obtain both data and file paths
    maps5 = motor._load_5m_maps()  # type: ignore[attr-defined]
    # Build a stem→Path lookup from the original files list
    path_lookup = {p.stem: p for p in motor.SITE_5M_FILES}

    chosen_z = chosen_tr = chosen_crs = None
    chosen_res = 80
    # Try 5 m maps first
    for name, (z, tr, crs) in maps5.items():
        # Convert point to this map CRS
        xo, yo = (np.array(v)[0] for v in rasterio.warp.transform(motor.LUNA_CRS, crs, [lon_norm], [lat]))
        inv = ~tr
        if 0 <= (inv @ (xo, yo))[0] < z.shape[1] - 1 and 0 <= (inv @ (xo, yo))[1] < z.shape[0] - 1:
            chosen_z, chosen_tr, chosen_crs = z, tr, crs
            chosen_res = 5
            raster_path = path_lookup.get(name)
            break
    if chosen_z is None:
        # fallback to 80 m global DEM
        chosen_z, chosen_tr, chosen_crs = motor._cargar_80()  # type: ignore[attr-defined]
        chosen_res = 80
        raster_path = Path(motor.LDEM_80_PATH)

    # Transform lat/lon to raster coordinates
    x, y = (np.array(v)[0] for v in rasterio.warp.transform(motor.LUNA_CRS, chosen_crs, [lon_norm], [lat]))
    col, row = chosen_tr * (x, y)
    col, row = int(col), int(row)
    pix_radius = int(radio_km * 1000 / chosen_res)
    window = rasterio.windows.Window(col - pix_radius, row - pix_radius, 2 * pix_radius + 1, 2 * pix_radius + 1)
    with rasterio.open(raster_path) as ds:
        elev = ds.read(1, window=window).astype(float)
    # Replace nodata with None for JSON friendliness
    if ds.nodata is not None:
        elev = np.where(elev == ds.nodata, np.nan, elev)
    elev_list = [[None if np.isnan(v) else float(v) for v in row] for row in elev]
    return {"resolucion": chosen_res, "elevacion_m": elev_list}

# ---------------------------------------------------------------------------
# Endpoint: /api/contexto-mision
# ---------------------------------------------------------------------------
@app.get("/api/contexto-mision")
def contexto_mision(sitio: str = Query(...)) -> Dict[str, Any]:
    cache_key = _context_cache_key(sitio)
    entry = cache.load(cache_key)
    if entry and _is_fresh(entry):
        return entry["data"]
    # Fetch solar flares from NASA DONKI
    try:
        # Compute date range: last 30 days from today
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        flr_resp = requests.get(
            "https://api.nasa.gov/DONKI/FLR",
            params={
                "api_key": "DEMO_KEY",
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
            },
            timeout=4,
        )
        flr_resp.raise_for_status()
        flares = flr_resp.json()
    except Exception:
        flares = []
    # Fetch up to 3 images from NASA Image Library
    # Map short site names to richer search terms for better results
    site_map = {
        "cresta": "Shackleton crater lunar south pole",
        "shackleton": "Shackleton crater Moon",
        "degerlache": "lunar south pole LRO",
        "malapert": "Malapert mountain Moon",
    }
    query_term = site_map.get(sitio.lower(), sitio)
    try:
        img_resp = requests.get(
            "https://images-api.nasa.gov/search",
            params={"q": query_term, "media_type": "image", "page": 1},
            timeout=4,
        )
        img_resp.raise_for_status()
        items = img_resp.json().get("collection", {}).get("items", [])[:3]
        images = [it.get("links", [{}])[0].get("href") for it in items]
        if not images:
            # fallback curated images about the lunar South Pole
            images = [
                "https://images.nasa.gov/details/PIA24439",
                "https://images.nasa.gov/details/PIA00128",
                "https://images.nasa.gov/details/GSFC_20171208_Archive_e001353",
            ]
    except Exception:
        images = [
            "https://images.nasa.gov/details/GSFC_20171208_Archive_e001989",
            "https://images.nasa.gov/details/GSFC_20171208_Archive_e001817",
            "https://images.nasa.gov/details/MAF_20211119_LunarEclipse01",
        ]
    result = {"flamadas_solares": flares, "imagenes_nasa": images}
    cache.save(cache_key, {"_ts": time.time(), "data": result})
    return result
    # -------------------------------------------------
# Mount static frontend (web/) at root URL
# -------------------------------------------------
web_dir = Path(__file__).resolve().parent.parent / "web"
if web_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
