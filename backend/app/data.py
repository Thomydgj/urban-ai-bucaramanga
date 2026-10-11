from functools import lru_cache

import geopandas as gpd

from .config import MASTER_GPKG, MASTER_LAYER


@lru_cache(maxsize=1)
def load_master_layer() -> gpd.GeoDataFrame:
    """
    Carga la capa maestra de intervención.

    Se utiliza cache para evitar leer el GeoPackage
    en cada petición HTTP.
    """

    if not MASTER_GPKG.exists():
        raise FileNotFoundError(
            f"No se encontró la capa maestra: {MASTER_GPKG}"
        )

    gdf = gpd.read_file(
        MASTER_GPKG,
        layer=MASTER_LAYER,
    )

    if gdf.empty:
        raise ValueError("La capa maestra está vacía.")

    if gdf.crs is None:
        raise ValueError("La capa maestra no tiene CRS definido.")

    return gdf