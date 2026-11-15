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
from api.clima_espacial import obtener_clima_espacial

# Simple in‑memory cache for the space‑weather endpoint (15 min TTL)
_clima_cache = {"data": None, "ts": 0}

from datetime import datetime, timedelta
from typing import List, Dict, Any

import requests
import numpy as np
import rasterio
from rasterio.warp import transform
from rasterio.windows import Window
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

# -------------------------------------------------
# Endpoint: /api/analizar (adapted to frontend contract)
# -------------------------------------------------
@app.get("/api/analizar")
def analizar(
    lat: float = Query(..., ge=-90, le=-80),
    lon: float = Query(..., ge=-180, le=360),
) -> Dict[str, Any]:
    # Normalizar longitud al rango -180..180 que espera el motor
    lon_norm = ((lon + 180) % 360) - 180
    # Compute horizon with multi‑resolution engine
    h0, az_arr, hor_arr, resol = motor.horizonte_optimizado(lat, lon_norm)
    az_arr, hor_arr = np.asarray(az_arr, dtype=float), np.asarray(hor_arr, dtype=float)

    # Load efemérides (cached) para Sol y Tierra
    fechas, saz, sel = _efemerides_cached(SOL, lat, lon_norm, h0)
    _, taz, tel = _efemerides_cached(TIERRA, lat, lon_norm, h0)

    # Interpolación del horizonte en azimut del Sol/Tierra
    per = lambda a: np.interp(np.asarray(a) % 360, np.append(az_arr, 360), np.append(hor_arr, hor_arr[0]))
    # fraccion_sol está en calculo.horizonte
    from calculo.horizonte import fraccion_sol
    frac = np.round(fraccion_sol(sel, per(saz)), 3)
    vis_t = (np.asarray(tel) > per(taz)).astype(int)

    # Construir resultados según contrato del frontend
    datos: Dict[str, Any] = {
        "lat": lat,
        "lon": lon,
        "altura_m": round(float(h0)),
        "horizonte": hor_arr.tolist(),  # Compatibilidad con los clientes que leen elevaciones.
        "perfil_horizonte": {"az": az_arr.tolist(), "el": hor_arr.tolist()},
        "sol": {
            "az": np.round(np.asarray(saz, dtype=float), 3).tolist(),
            "el": np.round(np.asarray(sel, dtype=float), 3).tolist(),
            "frac": frac.tolist(),
            "hasta_puesta": horas_hasta_cambio(sol_vis := (frac > 0).tolist()),
            "hasta_salida": horas_hasta_cambio([not v for v in sol_vis]),
        },
        "tierra": {
            "az": np.round(np.asarray(taz, dtype=float), 3).tolist(),
            "el": np.round(np.asarray(tel, dtype=float), 3).tolist(),
            "visible": vis_t.tolist(),
            "hasta_puesta": horas_hasta_cambio(tie_vis := (vis_t > 0).tolist()),
            "hasta_salida": horas_hasta_cambio([not v for v in tie_vis]),
        },
        "resumen": {
            "luz_pct": round(float(np.mean(frac) * 100), 1),
            "tierra_pct": round(float(np.mean(vis_t) * 100), 1),
            "max_oscuridad_h": racha_maxima([not v for v in sol_vis]),
            "max_sin_tierra_h": racha_maxima([not v for v in tie_vis]),
            "sol_y_tierra_pct": round(float(np.mean(np.logical_and(sol_vis, tie_vis)) * 100), 1),
        },
        "terreno": motor.terreno(lat, lon_norm),
        "metadatos_cientificos": {
            "resolucion_cercana": resol,
            "incertidumbre_altura_rms_m": "0.30–0.50",
            "incertidumbre_pendiente_deg": "1.5–2.5",
            "advertencia_falsos_positivos_psr_%": "30–50",
        },
    }
    return datos

# Endpoint: /api/clima-espacial
@app.get("/api/clima-espacial")
def clima_espacial() -> Dict[str, Any]:
    global _clima_cache
    now = time.time()
    if _clima_cache["data"] is not None and now - _clima_cache["ts"] < 15 * 60:
        return _clima_cache["data"]
    result = obtener_clima_espacial()
    if result["datos_completos"]:
        _clima_cache = {"data": result, "ts": now}
    return result


# ---------------------------------------------------------------------------
# Endpoint: /api/terreno-3d
# ---------------------------------------------------------------------------
@app.get("/api/terreno-3d")
def terreno_3d(
    lat: float = Query(..., ge=-90, le=-80),
    lon: float = Query(..., ge=-180, le=360),
    radio_km: float = Query(2.0, gt=0),
    hora: int = Query(0, ge=0, le=8759),
) -> Dict[str, Any]:
    # Normalizar longitud al rango -180..180 esperado por motor
    lon_norm = ((lon + 180) % 360) - 180
    # Abrir las cabeceras en orden de resolución y leer solo la ventana elegida.
    for path in [*motor.SITE_5M_FILES, motor.LDEM_80_PATH]:
        with rasterio.open(path) as ds:
            xs, ys = transform(motor.LUNA_CRS, ds.crs, [lon_norm], [lat])
            row, col = ds.index(xs[0], ys[0])
            if not (0 <= row < ds.height and 0 <= col < ds.width):
                continue

            paso_m, paso_y = ds.res
            rx = int(radio_km * 1000 / paso_m)
            ry = int(radio_km * 1000 / paso_y)
            left, top = max(0, col - rx), max(0, row - ry)
            right, bottom = min(ds.width, col + rx + 1), min(ds.height, row + ry + 1)
            window = Window(left, top, right - left, bottom - top)
            band = ds.read(1, window=window, masked=True).astype(float)
            elev = band.filled(np.nan) * ds.scales[0] + ds.offsets[0]
            altura_centro_m = elev[row - top, col - left]
            break
    else:
        raise HTTPException(status_code=422, detail="El punto está fuera de los mapas disponibles.")

    ny, nx = elev.shape
    ancho_m = nx * paso_m
    slope = np.full_like(elev, np.nan)
    if nx > 1 and ny > 1:
        dy, dx = np.gradient(elev, paso_y, paso_m)
        slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    elev_flat = [float(v) if np.isfinite(v) else None for v in elev.ravel()]
    slope_flat = [float(v) if np.isfinite(v) else None for v in slope.ravel()]

    # Vector dirección solar para la hora solicitada
    fechas, saz, sel = _efemerides_cached(SOL, lat, lon_norm, motor.horizonte_optimizado(lat, lon_norm)[0])
    if len(saz) == 0:
        sol_vec = [0.0, 0.0, 0.0]
    else:
        idx = hora % len(saz)
        az_rad = np.radians(saz[idx])
        el_rad = np.radians(sel[idx])
        sol_vec = [float(np.cos(el_rad) * np.cos(az_rad)), float(np.cos(el_rad) * np.sin(az_rad)), float(np.sin(el_rad))]

    return {
        "nx": nx,
        "ny": ny,
        "paso_m": paso_m,
        "ancho_m": ancho_m,
        "altura_centro_m": float(altura_centro_m) if np.isfinite(altura_centro_m) else None,
        "elevaciones": elev_flat,
        "pendientes": slope_flat,
        "sol_vec": sol_vec,
    }

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
            images = []
    except Exception:
        images = [
            "https://images.nasa.gov/details/GSFC_20171208_Archive_e001989",
            "https://images.nasa.gov/details/GSFC_20171208_Archive_e001817",
            "https://images.nasa.gov/details/MAF_20211119_LunarEclipse01",
        ]
    result = {"flamadas_solares": flares, "imagenes_nasa": images}
    cache.save(cache_key, {"_ts": time.time(), "data": result})
    return result

web_dir = Path(__file__).resolve().parent.parent / "web"


@app.get("/api/sitios")
def sitios() -> Dict[str, Any]:
    """Catálogo de sitios y metadatos temporales utilizados por el navegador."""
    try:
        with (web_dir / "data" / "sitios.json").open(encoding="utf-8") as catalogo:
            return json.load(catalogo)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="El catálogo de sitios no está disponible.") from exc


if web_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
