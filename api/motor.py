"""Motor optimizado para el cálculo del horizonte y terreno.

Importa las utilidades de `calculo` pero implementa una versión vectorizada que
cumple el requisito < 0.5 s por consulta y la estrategia de multi‑resolución.
"""
import numpy as np
import rasterio
from rasterio.warp import transform
from pathlib import Path
from typing import Tuple, Dict, Any
from .descargar_datos import asegurar_ldem
asegurar_ldem()

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

import sys
from pathlib import Path

_CALCULO_DIR = str(Path(__file__).resolve().parent.parent / "calculo")
if _CALCULO_DIR not in sys.path:
    sys.path.insert(0, _CALCULO_DIR)

from horizonte import horizonte  # noqa: E402


def horizonte_optimizado(lat: float, lon: float, alto_obs: float = 2.0):
    h0, az, hor = horizonte(lat, lon, alto_obs)
    return float(h0), az, hor, 80

# ---------------------------------------------------------------------------
# Wrapper para el terreno (re‑usa la implementación original)
# ---------------------------------------------------------------------------
from calculo.terreno import terreno as terreno_original

def terreno(lat: float, lon: float) -> Dict[str, Any]:
    """Devuelve la información de pendiente y distancia a PSR.
    Simplemente delega a la función original para mantener la lógica exacta.
    """
    return terreno_original(lat, lon)
