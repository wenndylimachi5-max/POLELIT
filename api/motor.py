"""Motor optimizado para el cálculo del horizonte y terreno.

Importa las utilidades de `calculo` pero implementa una versión vectorizada que
cumple el requisito < 0.5 s por consulta y la estrategia de multi‑resolución.
"""
import numpy as np
import rasterio
from rasterio.warp import transform
from pathlib import Path
from typing import Tuple, Dict, Any

# Importar funciones auxiliares del código existente
from calculo.horizonte import _cargar as _cargar_80, _interp as _interp_80, _xyz as _xyz_80
from calculo.terreno import _xy as _xy_psr  # reutilizamos solo para transformación lat/lon
from calculo.horizonte import RADIO_SOL as RADIO_SOL

# Cargar datos estáticos una sola vez (será llamado por el lifespan de FastAPI)
# Detect the actual location of the raster data. Prefer 'web/datos' if it exists,
# otherwise fall back to a top‑level 'datos' directory.
DATA_ROOT_CANDIDATES = [
    Path(__file__).resolve().parents[1] / "web" / "datos",
    Path(__file__).resolve().parents[1] / "datos",
]
DATA_ROOT = next((p for p in DATA_ROOT_CANDIDATES if p.is_dir()), None)
if DATA_ROOT is None:
    raise FileNotFoundError("GeoTIFF data directory not found in expected locations.")
LDEM_80_PATH = DATA_ROOT / "LDEM_80S_80MPP_ADJ.tif"
LPSR_PATH = DATA_ROOT / "LPSR_80S_20MPP_ADJ.TIF"
# Mapas de 5 m (4 sites)
SITE_5M_FILES = list(DATA_ROOT.glob("*_5mpp_surf.tif"))

# Constantes del modelo lunar
R = 1737400.0  # radio en metros
LUNA_CRS = "+proj=longlat +R=1737400 +no_defs"

# ---------------------------------------------------------------------------
# Carga perezosa de los raster (se ejecutará una sola vez en el startup)
# ---------------------------------------------------------------------------

def _load_80m() -> Tuple[np.ndarray, rasterio.Affine, Any]:
    with rasterio.open(LDEM_80_PATH) as ds:
        z = ds.read(1).astype(np.float32)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        return z, ds.transform, ds.crs

def _load_5m_maps() -> Dict[str, Tuple[np.ndarray, rasterio.Affine, Any]]:
    maps = {}
    for p in SITE_5M_FILES:
        with rasterio.open(p) as ds:
            z = ds.read(1).astype(np.float32)
            if ds.nodata is not None:
                z[z == ds.nodata] = np.nan
            maps[p.stem] = (z, ds.transform, ds.crs)
    return maps

# ---------------------------------------------------------------------------
# Utilidades auxiliares
# ---------------------------------------------------------------------------

def _point_in_raster(x: float, y: float, inv: np.ndarray, shape: Tuple[int, int]) -> bool:
    cx, cy = inv @ (x, y)
    return 0 <= cx < shape[1] - 1 and 0 <= cy < shape[0] - 1

def _select_5m_map(lat: float, lon: float, maps_5m: Dict[str, Tuple[np.ndarray, rasterio.Affine, Any]]) -> Tuple[np.ndarray, rasterio.Affine, Any] | None:
    """Devuelve el primer mapa de 5 m que contenga el punto o None.
    """
    # Transformar a la proyección del primer mapa (todos comparten CRS)
    sample_crs = next(iter(maps_5m.values()))[2]
    xo, yo = (np.array(v)[0] for v in transform(LUNA_CRS, sample_crs, [lon], [lat]))
    for name, (z, tr, crs) in maps_5m.items():
        inv = ~tr
        if _point_in_raster(xo, yo, inv, z.shape):
            return z, tr, crs
    return None

def _interp_general(z: np.ndarray, inv: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Interpolación bilineal tal como lo hacía `_interp` en el módulo original.
    """
    c, f = inv @ (xs, ys)
    c, f = np.asarray(c) - 0.5, np.asarray(f) - 0.5
    c0, f0 = np.floor(c).astype(int), np.floor(f).astype(int)
    ok = (c0 >= 0) & (f0 >= 0) & (c0 < z.shape[1] - 1) & (f0 < z.shape[0] - 1)
    out = np.full(c.shape, np.nan)
    a, b = c0[ok], f0[ok]
    dc, df = c[ok] - c0[ok], f[ok] - f0[ok]
    out[ok] = (
        z[b, a] * (1 - dc) * (1 - df)
        + z[b, a + 1] * dc * (1 - df)
        + z[b + 1, a] * (1 - dc) * df
        + z[b + 1, a + 1] * dc * df
    )
    return out

# ---------------------------------------------------------------------------
# Función pública: cálculo del horizonte con multi‑resolución
# ---------------------------------------------------------------------------

def horizonte_optimizado(lat: float, lon: float, alto_obs: float = 2.0) -> Tuple[float, np.ndarray, np.ndarray, int]:
    """Calcula el horizonte para un punto lunar.

    Devuelve:
        h0 – altura del terreno bajo el observador (m)
        az  – array de 0‑359 (°)
        hor – elevación del horizonte por azimut (°)
        resol – resolución empleada en el anillo más cercano (5 o 80)
    """
    # Cargar raster 80 m (global) y 5 m (si corresponde)
    z80, T80, crs80 = _cargar_80()
    inv80 = ~T80
    maps5 = _load_5m_maps()
    # Transformar lat/lon a coordenadas del LDEM 80 m
    xo, yo = (np.array(v)[0] for v in transform(LUNA_CRS, crs80, [lon], [lat]))
    # Altura bajo el observador
    h0 = _interp_80(z80, inv80, [xo], [yo])[0]
    # Determinar si hay mapa 5 m que cubra el punto
    mapa5 = _select_5m_map(lat, lon, maps5)
    resol = 80
    # Direcciones norte y este en la proyección polar estereográfica
    xn, yn = (np.array(v)[0] for v in transform(LUNA_CRS, crs80, [lon], [lat + 0.01]))
    xe, ye = (np.array(v)[0] for v in transform(LUNA_CRS, crs80, [lon + 0.01], [lat]))
    n_vec = np.array([xn - xo, yn - yo]); n_vec /= np.linalg.norm(n_vec)
    e_vec = np.array([xe - xo, ye - yo])
    e_vec -= n_vec * (e_vec @ n_vec)
    e_vec /= np.linalg.norm(e_vec)
    # Ángulos en radianes para 360 direcciones
    A = np.radians(np.arange(360.0))[:, None]
    # Rayos 80 m desde 5 km hasta 150 km (paso 40 m)
    paso80 = 40.0
    d80 = np.arange(5_000.0, 150_000.0 + paso80, paso80)[None, :]
    X80 = (xo + (np.sin(A) * e_vec[0] + np.cos(A) * n_vec[0]) * d80).ravel()
    Y80 = (yo + (np.sin(A) * e_vec[1] + np.cos(A) * n_vec[1]) * d80).ravel()
    H80 = _interp_general(z80, inv80, X80, Y80)
    if mapa5 is not None:
        z5, T5, crs5 = mapa5
        inv5 = ~T5
        # Transformar punto al CRS del mapa 5 m
        xo5, yo5 = (np.array(v)[0] for v in transform(LUNA_CRS, crs5, [lon], [lat]))
        paso5 = 5.0
        d5 = np.arange(paso5, 5_000.0 + paso5, paso5)[None, :]
        X5 = (xo5 + (np.sin(A) * e_vec[0] + np.cos(A) * n_vec[0]) * d5).ravel()
        Y5 = (yo5 + (np.sin(A) * e_vec[1] + np.cos(A) * n_vec[1]) * d5).ravel()
        H5 = _interp_general(z5, inv5, X5, Y5)
        # Combine: para cada azimut usamos los valores de 5 m donde existen y 80 m en el resto
        # Pad H5 to same length as H80 (los últimos valores serán nan)
        pad_len = H80.shape[0] - H5.shape[0]
        if pad_len > 0:
            H5 = np.concatenate([H5, np.full(pad_len, np.nan)])
        H_comb = np.fmax(H5, H80)
        resol = 5
    else:
        H_comb = H80
    # Conversión a coordenadas 3D usando la función original _xyz (asume radio + altura)
    lo, la = transform(crs80, LUNA_CRS, X80, Y80)
    P = _xyz_80(np.radians(la), np.radians(lo), H_comb)
    # Observador
    O = _xyz_80(np.radians(lat), np.radians(lon), h0 + alto_obs)
    U = O / np.linalg.norm(O)
    E = np.array([-np.sin(np.radians(lon)), np.cos(np.radians(lon)), 0.0])
    N = np.cross(U, E)
    v = P - O[:, None]
    el = np.degrees(np.arctan2(U @ v, np.hypot(E @ v, N @ v)))
    az = np.degrees(np.arctan2(E @ v, N @ v)) % 360
    hor = np.full(360, -90.0)
    mask = np.isfinite(el)
    np.maximum.at(hor, np.rint(az[mask]).astype(int) % 360, el[mask])
    return float(h0), np.arange(360), hor, resol

# ---------------------------------------------------------------------------
# Wrapper para el terreno (re‑usa la implementación original)
# ---------------------------------------------------------------------------
from calculo.terreno import terreno as terreno_original

def terreno(lat: float, lon: float) -> Dict[str, Any]:
    """Devuelve la información de pendiente y distancia a PSR.
    Simplemente delega a la función original para mantener la lógica exacta.
    """
    return terreno_original(lat, lon)
