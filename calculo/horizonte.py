"""horizonte.py — Horizonte local desde el mapa LDEM 80 m (LOLA) + luz y Tierra con Horizons.
Método: 360 rayos desde el observador (2 m sobre el suelo), alturas interpoladas del mapa,
elevación calculada en 3D sobre la esfera lunar (R = 1737400 m), máximo por cada grado de azimut."""
import numpy as np, rasterio
from rasterio.warp import transform
from pathlib import Path

R = 1737400.0
LUNA = "+proj=longlat +R=1737400 +no_defs"
LDEM = Path(__file__).resolve().parent.parent / "datos" / "LDEM_80S_80MPP_ADJ.tif"
RADIO_SOL = 0.2666  # grados


def _cargar():
    with rasterio.open(LDEM) as ds:
        z = ds.read(1).astype(np.float32)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        return z, ds.transform, ds.crs


def _interp(z, inv, x, y):
    """Altura interpolada (bilineal) en coordenadas del mapa; NaN si cae afuera."""
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
    r = R + h
    return np.array([r * np.cos(lat) * np.cos(lon), r * np.cos(lat) * np.sin(lon), r * np.sin(lat)])


def horizonte(lat, lon, alto_obs=2.0, dmax=150e3, paso=40.0):
    z, T, crs = _cargar()
    inv = ~T
    xo, yo = (np.array(v)[0] for v in transform(LUNA, crs, [lon], [lat]))
    if not (0 <= (inv * (xo, yo))[0] < z.shape[1] and 0 <= (inv * (xo, yo))[1] < z.shape[0]):
        raise ValueError("El punto está fuera del mapa LDEM")
    h0 = _interp(z, inv, [xo], [yo])[0]
    if abs(h0) < 20:          # si el mapa viniera en km, pasarlo a metros
        z *= 1000.0; h0 *= 1000.0

    # direcciones norte y este en el plano del mapa
    xn, yn = (np.array(v)[0] for v in transform(LUNA, crs, [lon], [lat + 0.01]))
    xe, ye = (np.array(v)[0] for v in transform(LUNA, crs, [lon + 0.01], [lat]))
    n = np.array([xn - xo, yn - yo]); n /= np.linalg.norm(n)
    e = np.array([xe - xo, ye - yo]); e -= n * (e @ n); e /= np.linalg.norm(e)

    # rayos: 360 azimuts x muestras cada 'paso' metros
    A = np.radians(np.arange(360.0))[:, None]
    d = np.arange(paso, dmax + paso, paso)[None, :]
    X = (xo + (np.sin(A) * e[0] + np.cos(A) * n[0]) * d).ravel()
    Y = (yo + (np.sin(A) * e[1] + np.cos(A) * n[1]) * d).ravel()
    H = _interp(z, inv, X, Y)
    lo, la = transform(crs, LUNA, X, Y)
    P = _xyz(np.radians(la), np.radians(lo), H)

    # elevación y azimut verdaderos vistos desde el observador (3D)
    fi, la0 = np.radians(lat), np.radians(lon)
    O = _xyz(fi, la0, h0 + alto_obs)
    U = O / np.linalg.norm(O)
    E = np.array([-np.sin(la0), np.cos(la0), 0.0])
    N = np.cross(U, E)
    v = P - O[:, None]
    el = np.degrees(np.arctan2(U @ v, np.hypot(E @ v, N @ v)))
    az = np.degrees(np.arctan2(E @ v, N @ v)) % 360

    hor = np.full(360, -90.0)
    m = np.isfinite(el)
    np.maximum.at(hor, np.rint(az[m]).astype(int) % 360, el[m])
    return h0, np.arange(360), hor


def fraccion_sol(el, h):
    t = np.clip((h - np.asarray(el)) / RADIO_SOL, -1, 1)
    return (np.arccos(t) - t * np.sqrt(1 - t**2)) / np.pi


if __name__ == "__main__":
    from horizons import efemerides, SOL, TIERRA
    lat, lon = -89.44, -137.0999   # Cresta
    h0, az, hor = horizonte(lat, lon)
    print(f"Altura del suelo en el mapa: {h0:.0f} m (esperado ~1958)")
    print(f"Horizonte: min {hor.min():.2f}°  max {hor.max():.2f}°  medio {hor.mean():.2f}°")

    ini, fin = "2027-01-01 00:00", "2027-12-31 23:00"
    _, saz, sel = efemerides(SOL, lat, lon, h0, ini, fin)
    _, taz, tel = efemerides(TIERRA, lat, lon, h0, ini, fin)
    per = lambda a: np.interp(np.asarray(a) % 360, np.append(az, 360), np.append(hor, hor[0]))
    luz = fraccion_sol(sel, per(saz)).mean() * 100
    tie = (np.asarray(tel) > per(taz)).mean() * 100
    print(f"2027 con relieve real (80 m): luz {luz:.1f}% | Tierra {tie:.1f}%")

    import matplotlib.pyplot as plt
    plt.plot(az, hor); plt.xlabel("Azimut (°)"); plt.ylabel("Elevación del horizonte (°)")
    plt.title("Horizonte — Cresta (LDEM 80 m)"); plt.grid(True)
    plt.savefig(Path(__file__).with_name("horizonte_cresta.png"), dpi=120)
    print("Gráfico guardado: calculo/horizonte_cresta.png")