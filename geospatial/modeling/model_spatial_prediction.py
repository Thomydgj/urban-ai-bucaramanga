from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_model_predictions.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

GPKG_PATH = (
    OUTPUT_DIR
    / "urban_model_predictions.gpkg"
)

GEOJSON_PATH = (
    OUTPUT_DIR
    / "urban_model_predictions.geojson"
)

MAP_PATH = (
    OUTPUT_DIR
    / "urban_model_prediction_map.png"
)


def main() -> None:
    print("=" * 50)
    print("MODEL SPATIAL PREDICTION")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # ==================================================
    # CARGAR PREDICCIONES
    # ==================================================

    df = pd.read_csv(INPUT_PATH)

    print("\n=== DATASET ===")
    print(f"Observaciones: {len(df):,}")

    required_columns = [
        "x",
        "y",
        "priority_probability",
        "model_prediction",
        "high_priority",
        "ndvi",
        "ndbi",
        "lst",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {missing}"
        )

    # ==================================================
    # CREAR GEOMETRÍA
    # ==================================================

    gdf = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(
            df["x"],
            df["y"],
        ),
        crs="EPSG:4326",
    )

    print("\n=== CAPA ESPACIAL ===")
    print(f"Geometrías: {len(gdf):,}")
    print(f"CRS: {gdf.crs}")

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    print("\n=== VALIDACIÓN ===")

    print(
        f"Geometrías válidas: "
        f"{gdf.geometry.is_valid.sum():,}"
    )

    print(
        f"Geometrías vacías: "
        f"{gdf.geometry.is_empty.sum():,}"
    )

    print(
        f"Geometrías nulas: "
        f"{gdf.geometry.isna().sum():,}"
    )

    # ==================================================
    # ESTADÍSTICAS ESPACIALES
    # ==================================================

    print("\n=== EXTENSIÓN ===")

    print(
        f"Longitud mínima: "
        f"{gdf.geometry.x.min():.6f}"
    )

    print(
        f"Longitud máxima: "
        f"{gdf.geometry.x.max():.6f}"
    )

    print(
        f"Latitud mínima: "
        f"{gdf.geometry.y.min():.6f}"
    )

    print(
        f"Latitud máxima: "
        f"{gdf.geometry.y.max():.6f}"
    )

    # ==================================================
    # PRIORIDAD
    # ==================================================

    print("\n=== PRIORITY PROBABILITY ===")

    print(
        f"Mínimo: "
        f"{gdf['priority_probability'].min():.6f}"
    )

    print(
        f"Máximo: "
        f"{gdf['priority_probability'].max():.6f}"
    )

    print(
        f"Media: "
        f"{gdf['priority_probability'].mean():.6f}"
    )

    print(
        f"Mediana: "
        f"{gdf['priority_probability'].median():.6f}"
    )

    # ==================================================
    # MAPA
    # ==================================================

    print("\n=== GENERANDO MAPA ===")

    fig, ax = plt.subplots(
        figsize=(12, 10)
    )

    gdf.plot(
        ax=ax,
        column="priority_probability",
        cmap="RdYlGn_r",
        markersize=1,
        legend=True,
        vmin=0,
        vmax=1,
    )

    ax.set_title(
        "Urban AI Bucaramanga - "
        "Probabilidad de Alta Prioridad",
        fontsize=14,
    )

    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")

    ax.grid(
        True,
        alpha=0.2,
    )

    plt.tight_layout()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.savefig(
        MAP_PATH,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    # ==================================================
    # EXPORTAR GEOPACKAGE
    # ==================================================

    gdf.to_file(
        GPKG_PATH,
        layer="model_predictions",
        driver="GPKG",
    )

    # ==================================================
    # EXPORTAR GEOJSON
    # ==================================================

    gdf.to_file(
        GEOJSON_PATH,
        driver="GeoJSON",
    )

    # ==================================================
    # RESULTADOS
    # ==================================================

    print("\n=== RESULTADOS ===")

    print(
        f"GeoPackage:\n"
        f"{GPKG_PATH}"
    )

    print(
        f"\nGeoJSON:\n"
        f"{GEOJSON_PATH}"
    )

    print(
        f"\nMapa:\n"
        f"{MAP_PATH}"
    )


if __name__ == "__main__":
    main()