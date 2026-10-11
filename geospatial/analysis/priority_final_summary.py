from pathlib import Path

import geopandas as gpd
import pandas as pd


INPUT_FILE = Path(
    "data/processed/analysis/priority_zones.gpkg"
)

OUTPUT_DIR = Path(
    "data/processed/analysis"
)

SUMMARY_FILE = OUTPUT_DIR / "priority_final_summary.csv"
ZONE_FILE = OUTPUT_DIR / "priority_zone_statistics.csv"

PROJECTED_CRS = "EPSG:3116"


def main() -> None:
    print("=" * 50)
    print("PRIORITY FINAL SUMMARY")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(INPUT_FILE)

    print(f"\nZonas cargadas: {len(gdf)}")

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    required_columns = [
        "spatial_rank",
        "observations",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "mean_priority",
        "geometry",
    ]

    missing = [
        column
        for column in required_columns
        if column not in gdf.columns
    ]

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {missing}"
        )

    # ==================================================
    # ÁREA
    # ==================================================

    projected = gdf.to_crs(PROJECTED_CRS)

    gdf["area_m2"] = projected.geometry.area
    gdf["area_ha"] = gdf["area_m2"] / 10_000

    # ==================================================
    # CENTROIDES
    # ==================================================

    projected_centroids = projected.geometry.centroid

    centroids_wgs84 = gpd.GeoSeries(
        projected_centroids,
        crs=PROJECTED_CRS,
    ).to_crs("EPSG:4326")

    gdf["centroid_x"] = centroids_wgs84.x
    gdf["centroid_y"] = centroids_wgs84.y

    # ==================================================
    # NIVEL DE PRIORIDAD
    # ==================================================

    def classify_priority(score: float) -> str:
        if score >= 0.75:
            return "MUY_ALTA"
        if score >= 0.70:
            return "ALTA"
        if score >= 0.65:
            return "MEDIA"
        return "BAJA"

    gdf["priority_level"] = (
        gdf["mean_priority"]
        .apply(classify_priority)
    )

    # ==================================================
    # PORCENTAJE DE OBSERVACIONES
    # ==================================================

    total_observations = gdf["observations"].sum()

    gdf["observation_percentage"] = (
        gdf["observations"]
        / total_observations
        * 100
    )

    # ==================================================
    # RESUMEN GENERAL
    # ==================================================

    print("\n=== RESUMEN GENERAL ===")

    print(
        f"Zonas prioritarias: {len(gdf):,}"
    )

    print(
        f"Observaciones P90: "
        f"{total_observations:,}"
    )

    print(
        f"Priority medio: "
        f"{gdf['mean_priority'].mean():.6f}"
    )

    print(
        f"Priority máximo: "
        f"{gdf['mean_priority'].max():.6f}"
    )

    print(
        f"NDVI medio: "
        f"{gdf['mean_ndvi'].mean():.6f}"
    )

    print(
        f"NDBI medio: "
        f"{gdf['mean_ndbi'].mean():.6f}"
    )

    print(
        f"LST media: "
        f"{gdf['mean_lst'].mean():.6f}"
    )

    print(
        f"Área total: "
        f"{gdf['area_ha'].sum():.2f} ha"
    )

    # ==================================================
    # DISTRIBUCIÓN DE PRIORIDAD
    # ==================================================

    print("\n=== NIVELES DE PRIORIDAD ===")

    level_summary = (
        gdf.groupby("priority_level")
        .agg(
            zones=("priority_level", "size"),
            observations=("observations", "sum"),
            mean_priority=("mean_priority", "mean"),
            mean_ndvi=("mean_ndvi", "mean"),
            mean_ndbi=("mean_ndbi", "mean"),
            mean_lst=("mean_lst", "mean"),
            area_ha=("area_ha", "sum"),
        )
        .sort_values(
            "mean_priority",
            ascending=False,
        )
    )

    print(level_summary)

    # ==================================================
    # TOP 10
    # ==================================================

    print("\n=== TOP 10 ZONAS ===")

    top10 = (
        gdf.sort_values(
            "mean_priority",
            ascending=False,
        )
        .head(10)
    )

    columns = [
        "spatial_rank",
        "observations",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "mean_priority",
        "area_ha",
        "centroid_x",
        "centroid_y",
        "priority_level",
    ]

    print(
        top10[columns].to_string(
            index=False
        )
    )

    # ==================================================
    # CSV GENERAL
    # ==================================================

    summary_columns = [
        "spatial_rank",
        "observations",
        "observation_percentage",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "mean_priority",
        "area_m2",
        "area_ha",
        "centroid_x",
        "centroid_y",
        "priority_level",
    ]

    gdf[summary_columns].to_csv(
        ZONE_FILE,
        index=False,
    )

    # ==================================================
    # RESUMEN POR NIVEL
    # ==================================================

    level_summary.reset_index().to_csv(
        SUMMARY_FILE,
        index=False,
    )

    # ==================================================
    # RESULTADOS
    # ==================================================

    print("\n=== RESULTADOS ===")

    print(
        f"Resumen por nivel: {SUMMARY_FILE}"
    )

    print(
        f"Estadísticas por zona: {ZONE_FILE}"
    )


if __name__ == "__main__":
    main()