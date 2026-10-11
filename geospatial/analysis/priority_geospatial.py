from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "priority_spatial_summary.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
)

OUTPUT_GPKG = OUTPUT_DIR / "priority_zones.gpkg"
OUTPUT_GEOJSON = OUTPUT_DIR / "priority_zones.geojson"

GRID_SIZE = 0.002

CRS = "EPSG:4326"


def build_grid_geometry(
    grid_x: int,
    grid_y: int,
    min_x: float,
    min_y: float,
):
    """
    Build the polygon corresponding to one spatial grid cell.
    """

    x_min = min_x + grid_x * GRID_SIZE
    y_min = min_y + grid_y * GRID_SIZE

    x_max = x_min + GRID_SIZE
    y_max = y_min + GRID_SIZE

    return box(
        x_min,
        y_min,
        x_max,
        y_max,
    )


def main() -> None:

    print("=" * 50)
    print("PRIORITY GEOSPATIAL")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = pd.read_csv(INPUT_FILE)

    print(f"\nZonas espaciales: {len(df):,}")

    required_columns = {
        "grid_x",
        "grid_y",
        "observations",
        "mean_priority",
        "max_priority",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "priority_density",
        "spatial_rank",
        "mean_x",
        "mean_y",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    # --------------------------------------------------
    # ORIGEN DE LA GRID
    # --------------------------------------------------

    min_x = df["mean_x"].min()
    min_y = df["mean_y"].min()

    # Ajustamos el origen para representar la grid
    min_x = min_x - (
        df["grid_x"].min() * GRID_SIZE
    )

    min_y = min_y - (
        df["grid_y"].min() * GRID_SIZE
    )

    # --------------------------------------------------
    # GEOMETRÍAS
    # --------------------------------------------------

    geometries = [
        build_grid_geometry(
            int(row.grid_x),
            int(row.grid_y),
            min_x,
            min_y,
        )
        for row in df.itertuples()
    ]

    gdf = gpd.GeoDataFrame(
        df.copy(),
        geometry=geometries,
        crs=CRS,
    )

    # --------------------------------------------------
    # SELECCIÓN DE COLUMNAS
    # --------------------------------------------------

    columns = [
        "spatial_rank",
        "observations",
        "mean_priority",
        "max_priority",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "priority_density",
        "mean_x",
        "mean_y",
        "geometry",
    ]

    gdf = gdf[columns]

    # --------------------------------------------------
    # ORDEN ESPACIAL
    # --------------------------------------------------

    gdf = gdf.sort_values(
        "spatial_rank"
    ).reset_index(drop=True)

    # --------------------------------------------------
    # EXPORTACIÓN
    # --------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OUTPUT_GPKG.exists():
        OUTPUT_GPKG.unlink()

    if OUTPUT_GEOJSON.exists():
        OUTPUT_GEOJSON.unlink()

    gdf.to_file(
        OUTPUT_GPKG,
        layer="priority_zones",
        driver="GPKG",
    )

    gdf.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    # --------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------

    print("\n=== CAPA ESPACIAL ===")

    print(f"Zonas: {len(gdf):,}")
    print(f"CRS: {gdf.crs}")

    print("\n=== TOP 5 ZONAS ===")

    print(
        gdf[
            [
                "spatial_rank",
                "observations",
                "mean_ndvi",
                "mean_ndbi",
                "mean_lst",
                "mean_priority",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )

    print("\n=== RESULTADOS ===")

    print(
        f"GeoPackage:\n{OUTPUT_GPKG}"
    )

    print(
        f"\nGeoJSON:\n{OUTPUT_GEOJSON}"
    )


if __name__ == "__main__":
    main()