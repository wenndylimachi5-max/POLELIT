"""
terreno.py — Pendiente del suelo y sombra permanente más cercana para cada sitio.

  - Pendiente: mapas LOLA de 5 m/píxel (Barker et al. 2020, PGDA producto 78).
    Se informa la pendiente en el punto y la media y máxima en un radio de 50 m (zona de aterrizaje).
  - Sombra permanente: mapa LPSR de 20 m/píxel (Barker et al. 2023, PGDA producto 90).
    Se informa la distancia a la región de sombra permanente (PSR) más cercana, buscando hasta 25 km.

Fuentes: https://pgda.gsfc.nasa.gov/products/78 · https://pgda.gsfc.nasa.gov/products/90
Uso: python calculo/terreno.py
"""
import numpy as np
import rasterio
from rasterio.warp import transform
from rasterio.windows import Window
from pathlib import Path

LUNA = "+proj=longlat +R=1737400 +no_defs"
DATOS = Path(__file__).resolve().parent.parent / "datos"
LPSR = DATOS / "LPSR_80S_20MPP_ADJ.TIF"
RADIO_PEND = 50.0        # radio de la zona de aterrizaje (m)
RADIO_PSR = 25000.0      # distancia máxima de búsqueda de sombra permanente (m)


def _xy(ds, lat, lon):
    """Latitud y longitud (°) → coordenadas del mapa (m)."""
    x, y = transform(LUNA, ds.crs, [lon], [lat])
    return x[0], y[0]


def pendiente(lat, lon):
    """Pendiente (°) en el punto y media/máxima en RADIO_PEND, usando el mapa de 5 m que contenga el sitio."""
    for tif in sorted(DATOS.glob("*_5mpp_surf.tif")):
        with rasterio.open(tif) as ds:
            x, y = _xy(ds, lat, lon)
            b = ds.bounds
            if not (b.left < x < b.right and b.bottom < y < b.top):
                continue                                    # el sitio no está en este mapa
            px = abs(ds.transform.a)                        # tamaño de píxel (m)
            n = int(RADIO_PEND / px) + 1
            f, c = ds.index(x, y)
            z = ds.read(1, window=Window(c - n, f - n, 2 * n + 1, 2 * n + 1)).astype(float)
            if ds.nodata is not None:
                z[z == ds.nodata] = np.nan
            gy, gx = np.gradient(z, px)                     # variación de altura por metro
            s = np.degrees(np.arctan(np.hypot(gx, gy)))     # pendiente en grados
            yy, xx = np.mgrid[-n:n + 1, -n:n + 1] * px
            zona = np.hypot(xx, yy) <= RADIO_PEND
            return dict(mapa_5m=tif.name.split("_")[0],
                        pendiente_deg=round(float(s[n, n]), 1),
                        pendiente_media_deg=round(float(np.nanmean(s[zona])), 1),
                        pendiente_max_deg=round(float(np.nanmax(s[zona])), 1))
    return None


def sombra_cercana(lat, lon):
    """Distancia (km) a la sombra permanente más cercana, según el mapa LPSR."""
    with rasterio.open(LPSR) as ds:
        x, y = _xy(ds, lat, lon)
        px = abs(ds.transform.a)
        n = int(RADIO_PSR / px)
        f, c = ds.index(x, y)
        p = ds.read(1, window=Window(c - n, f - n, 2 * n + 1, 2 * n + 1))
        psr = p > 0
        if ds.nodata is not None:
            psr &= p != ds.nodata
        if not psr.any():
            return None
        ff, cc = np.nonzero(psr)
        return round(float(np.hypot(ff - n, cc - n).min() * px / 1000), 2)


def terreno(lat, lon):
    return (pendiente(lat, lon) or {}) | dict(psr_dist_km=sombra_cercana(lat, lon))


# Verificación rápida: python calculo/terreno.py
if __name__ == "__main__":
    with rasterio.open(LPSR) as ds:                         # control: qué valores tiene el mapa LPSR
        muestra = ds.read(1, window=Window(15000, 15000, 400, 400))
        print(f"LPSR: tipo {ds.dtypes[0]}, nodata {ds.nodata}, valores de muestra {np.unique(muestra)[:10]}")

    sitios = {"Cresta": (-89.44, -137.0999), "Shackleton": (-89.7804, -156.1970),
              "de Gerlache": (-88.6639, -68.3883), "Malapert": (-85.9803, 1.6342)}
    for nombre, (lat, lon) in sitios.items():
        print(nombre, terreno(lat, lon))