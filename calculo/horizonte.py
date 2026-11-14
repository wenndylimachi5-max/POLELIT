"""
horizonte.py — Horizonte local de un sitio lunar a partir del mapa de alturas LOLA.

Método:
  - Mapa LDEM (Lunar Digital Elevation Model) de 80 m/píxel del polo sur, medido por
    LOLA (Lunar Orbiter Laser Altimeter, a bordo de LRO).
  - Desde el sitio (observador a 2 m del suelo) se trazan 360 rayos, uno por grado de azimut,
    con muestras cada 40 m hasta 150 km.
  - La elevación de cada muestra se calcula en 3D sobre la esfera lunar, por lo que incluye
    la curvatura de la Luna. El horizonte es la elevación máxima en cada azimut.
  - El Sol se trata como un disco de radio 0.2666° para calcular qué fracción se ve.

Fuente del mapa: NASA PGDA (Planetary Geodesy Data Archive), https://pgda.gsfc.nasa.gov/products/90
"""
import numpy as np
import rasterio
from rasterio.warp import transform
from pathlib import Path

R = 1737400.0                                   # radio lunar de referencia del mapa (m)
LUNA = "+proj=longlat +R=1737400 +no_defs"      # sistema lat/lon sobre la esfera lunar
LDEM = Path(__file__).resolve().parent.parent / "datos" / "LDEM_80S_80MPP_ADJ.tif"
RADIO_SOL = 0.2666                              # radio aparente del Sol (°)


def _cargar():
    """Lee el mapa: alturas, transformación píxel↔metros y proyección."""
    with rasterio.open(LDEM) as ds:
        z = ds.read(1).astype(np.float32)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        return z, ds.transform, ds.crs


def _interp(z, inv, x, y):
    """Altura en (x, y) interpolando entre los 4 píxeles vecinos. NaN si cae fuera del mapa."""
    c, f = inv * (np.asarray(x, float), np.asarray(y, float))
    c, f = np.asarray(c) - 0.5, np.asarray(f) - 0.5
    c0, f0 = np.floor(c).astype(int), np.floor(f).astype(int)
    ok = (c0 >= 0) & (f0 >= 0) & (c0 < z.shape[1] - 1) & (f0 < z.shape[0] - 1)
    out = np.full(c.shape, np.nan)
    a, b, dc, df = c0[ok], f0[ok], c[ok] - c0[ok], f[ok] - f0[ok]
    out[ok] = (z[b, a] * (1 - dc) * (1 - df) + z[b, a + 1] * dc * (1 - df)
               + z[b + 1, a] * (1 - dc) * df + z[b + 1, a + 1] * dc * df)
    return out


def _xyz(lat, lon, h):
    """Lat, lon (radianes) y altura (m) → coordenadas 3D con centro en la Luna."""
    r = R + h
    return np.array([r * np.cos(lat) * np.cos(lon), r * np.cos(lat) * np.sin(lon), r * np.sin(lat)])


def horizonte(lat, lon, alto_obs=2.0, dmax=150e3, paso=40.0):
    """
    Devuelve la altura del suelo (m), los azimuts 0–359° y la elevación del horizonte (°) en cada uno.
    """
    z, T, crs = _cargar()
    inv = ~T

    # Posición del sitio en el mapa (proyección polar estereográfica, metros)
    xo, yo = (np.array(v)[0] for v in transform(LUNA, crs, [lon], [lat]))
    if not (0 <= (inv * (xo, yo))[0] < z.shape[1] and 0 <= (inv * (xo, yo))[1] < z.shape[0]):
        raise ValueError("El punto está fuera del mapa LDEM")

    h0 = _interp(z, inv, [xo], [yo])[0]
    if abs(h0) < 20:                            # si el mapa estuviera en km, se pasa a metros
        z *= 1000.0; h0 *= 1000.0

    # Direcciones norte y este sobre el mapa
    xn, yn = (np.array(v)[0] for v in transform(LUNA, crs, [lon], [lat + 0.01]))
    xe, ye = (np.array(v)[0] for v in transform(LUNA, crs, [lon + 0.01], [lat]))
    n = np.array([xn - xo, yn - yo]); n /= np.linalg.norm(n)
    e = np.array([xe - xo, ye - yo]); e -= n * (e @ n); e /= np.linalg.norm(e)

    # 360 rayos con muestras cada 'paso' metros
    A = np.radians(np.arange(360.0))[:, None]
    d = np.arange(paso, dmax + paso, paso)[None, :]
    X = (xo + (np.sin(A) * e[0] + np.cos(A) * n[0]) * d).ravel()
    Y = (yo + (np.sin(A) * e[1] + np.cos(A) * n[1]) * d).ravel()
    H = _interp(z, inv, X, Y)
    lo, la = transform(crs, LUNA, X, Y)
    P = _xyz(np.radians(la), np.radians(lo), H)

    # Ejes locales del observador: U vertical, E este, N norte
    fi, la0 = np.radians(lat), np.radians(lon)
    O = _xyz(fi, la0, h0 + alto_obs)
    U = O / np.linalg.norm(O)
    E = np.array([-np.sin(la0), np.cos(la0), 0.0])
    N = np.cross(U, E)

    # Elevación y azimut de cada muestra vista desde el observador
    v = P - O[:, None]
    el = np.degrees(np.arctan2(U @ v, np.hypot(E @ v, N @ v)))
    az = np.degrees(np.arctan2(E @ v, N @ v)) % 360

    # Horizonte: máxima elevación en cada grado de azimut
    hor = np.full(360, -90.0)
    m = np.isfinite(el)
    np.maximum.at(hor, np.rint(az[m]).astype(int) % 360, el[m])
    return h0, np.arange(360), hor


def fraccion_sol(el, h):
    """
    Fracción visible del disco solar (0 = tapado, 1 = completo), según la elevación
    del centro del Sol (el) y la del horizonte en su azimut (h). Área de segmento circular.
    """
    t = np.clip((h - np.asarray(el)) / RADIO_SOL, -1, 1)
    return (np.arccos(t) - t * np.sqrt(1 - t**2)) / np.pi


# Verificación rápida: python calculo\horizonte.py
if __name__ == "__main__":
    from horizons import efemerides, SOL, TIERRA
    lat, lon = -89.44, -137.0999                # Cresta Shackleton–de Gerlache
    h0, az, hor = horizonte(lat, lon)
    print(f"Altura del suelo: {h0:.0f} m")
    print(f"Horizonte: min {hor.min():.2f}°  max {hor.max():.2f}°  medio {hor.mean():.2f}°")

    ini, fin = "2027-01-01 00:00", "2027-12-31 23:00"
    _, saz, sel = efemerides(SOL, lat, lon, h0, ini, fin)
    _, taz, tel = efemerides(TIERRA, lat, lon, h0, ini, fin)
    per = lambda a: np.interp(np.asarray(a) % 360, np.append(az, 360), np.append(hor, hor[0]))
    luz = fraccion_sol(sel, per(saz)).mean() * 100
    tie = (np.asarray(tel) > per(taz)).mean() * 100
    print(f"2027: luz {luz:.1f}% | Tierra {tie:.1f}%")

    import matplotlib.pyplot as plt
    plt.plot(az, hor); plt.xlabel("Azimut (°)"); plt.ylabel("Elevación del horizonte (°)")
    plt.title("Horizonte — Cresta (LDEM 80 m)"); plt.grid(True)
    plt.savefig(Path(__file__).with_name("horizonte_cresta.png"), dpi=120)
    print("Gráfico guardado: calculo/horizonte_cresta.png")