# Prueba: ¿se abren los 4 mapas y dan la altura correcta en la Cresta?
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform

LUNA = CRS.from_proj4("+proj=longlat +a=1737400 +b=1737400 +no_defs")
LAT, LON = -89.44, -137.0999            # Cresta

for nombre in ["LDEM_80S_80MPP_ADJ.tif", "LPSR_80S_20MPP_ADJ.TIF",
               "Site01_final_adj_5mpp_surf.tif", "Site04_final_adj_5mpp_surf.tif"]:
    with rasterio.open(f"datos/{nombre}") as m:
        xs, ys = transform(LUNA, m.crs, [LON], [LAT])
        try:
            fila, col = m.index(xs[0], ys[0])
            valor = m.read(1, window=((fila, fila + 1), (col, col + 1)))[0, 0]
        except Exception:
            valor = "fuera del mapa"
        print(f"{nombre}: {m.width}x{m.height} píxeles, {m.res[0]:.0f} m/píxel -> valor en la Cresta: {valor}")