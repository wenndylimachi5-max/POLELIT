# -*- coding: utf-8 -*-
"""Descargar datos LDEM

Módulo que asegura la disponibilidad del GeoTIFF ``LDEM_80S_80MPP_ADJ.tif``.

Exporta:
    asegurar_ldem() -> Path
"""

import os
from pathlib import Path
import requests


def asegurar_ldem() -> Path:
    """Garantiza que ``LDEM_80S_80MPP_ADJ.tif`` exista y tenga al menos 150 MiB.

    - El directorio destino se determina con la variable de entorno ``DATA_DIR``;
      si no está definida, se usa ``<repo>/datos`` (un nivel arriba del archivo).
    - Si el archivo ya existe y su tamaño supera ``150_000_000`` bytes, se
      devuelve inmediatamente.
    - En caso contrario se descarga por streaming con ``requests`` desde la URL
      especificada en ``LDEM_URL`` (valor por defecto: NASA PGDA).
    - Si la URL apunta a ``api.github.com`` y ``GITHUB_TOKEN`` está presente,
      se añaden los encabezados de autorización y se solicita el contenido
      binario.
    - La descarga se escribe primero en ``.tif.tmp`` y al completarse se reemplaza
      de forma atómica con ``os.replace`` para evitar archivos corruptos.
    """
    # 1️⃣ Directorio de destino
    default_dir = Path(__file__).resolve().parents[1] / "datos"
    data_dir = Path(os.getenv("DATA_DIR", default_dir))
    data_dir.mkdir(parents=True, exist_ok=True)

    # 2️⃣ Ruta del archivo objetivo
    target_path = data_dir / "LDEM_80S_80MPP_ADJ.tif"

    # 3️⃣ Si ya está presente y suficientemente grande, devolver
    if target_path.is_file() and target_path.stat().st_size > 150_000_000:
        return target_path

    # 4️⃣ Preparar la descarga
    url = os.getenv(
        "LDEM_URL",
        "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/80S/LDEM_80S_80MPP_ADJ.tif",
    )
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/octet-stream"

    # 5️⃣ Descargar en archivo temporal
    tmp_path = target_path.with_suffix(".tif.tmp")
    with requests.get(url, stream=True, timeout=120, headers=headers) as r:
        r.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    # 6️⃣ Reemplazo atómico
    os.replace(tmp_path, target_path)
    return target_path
