"""
centros_5m.py — Puntos de referencia de cada mapa LOLA de 5 m/píxel.

Los mapas de 5 m (Barker et al. 2020, NASA PGDA producto 78) cubren sitios candidatos
del polo sur. NASA no publica un lat/lon por sitio. Para cada mapa se informa:
  - el centro del mapa
  - el punto más alto de todo el mapa
  - el punto más alto a menos de 4 km del centro (representa al sitio y evita los bordes del mapa)
En el polo, los puntos altos son los que reciben más luz.

Fuente: https://pgda.gsfc.nasa.gov/products/78
Uso: python calculo/centros_5m.py
"""
import numpy as np
import rasterio
from rasterio.warp import transform
from pathlib import Path

LUNA = "+proj=longlat +R=1737400 +no_defs"
DATOS = Path(__file__).resolve().parent.parent / "datos"
RADIO_M = 4000          # radio de búsqueda alrededor del centro (m)


def a_latlon(ds, x, y):
    """Coordenadas del mapa (m) → latitud y longitud (°)."""
    lon, lat = (np.array(v)[0] for v in transform(ds.crs, LUNA, [x], [y]))
    return lat, lon


for tif in sorted(DATOS.glob("*_5mpp_surf.tif")):
    with rasterio.open(tif) as ds:
        z = ds.read(1).astype(np.float32)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        T = ds.transform
        b = ds.bounds
        print(f"\n{tif.name}  (tamaño {(b.right-b.left)/1000:.1f} x {(b.top-b.bottom)/1000:.1f} km)")

        # Centro del mapa
        xc, yc = (b.left + b.right) / 2, (b.bottom + b.top) / 2
        f, c = ds.index(xc, yc)
        lat, lon = a_latlon(ds, xc, yc)
        print(f"  Centro:      lat {lat:.4f}  lon {lon:.4f}  altura {z[f, c]:.0f} m")

        # Punto más alto de todo el mapa
        f, c = np.unravel_index(np.nanargmax(z), z.shape)
        x, y = ds.xy(f, c)
        lat, lon = a_latlon(ds, x, y)
        print(f"  Más alto:    lat {lat:.4f}  lon {lon:.4f}  altura {z[f, c]:.0f} m")

        # Punto más alto a menos de RADIO_M del centro
        xs = T.c + (np.arange(z.shape[1]) + 0.5) * T.a      # coordenada x de cada columna
        ys = T.f + (np.arange(z.shape[0]) + 0.5) * T.e      # coordenada y de cada fila
        dist = np.hypot(xs[None, :] - xc, ys[:, None] - yc)
        zc = np.where(dist <= RADIO_M, z, np.nan)
        f, c = np.unravel_index(np.nanargmax(zc), zc.shape)
        x, y = ds.xy(f, c)
        lat, lon = a_latlon(ds, x, y)
        print(f"  Alto ≤{RADIO_M/1000:.0f} km:  lat {lat:.4f}  lon {lon:.4f}  altura {z[f, c]:.0f} m")