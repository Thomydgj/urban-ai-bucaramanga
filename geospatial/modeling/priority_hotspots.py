from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_GPKG = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_ai_final_priority.gpkg"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

OUTPUT_GPKG = OUTPUT_DIR / "urban_priority_hotspots.gpkg"
OUTPUT_GEOJSON = OUTPUT_DIR / "urban_priority_hotspots.geojson"
OUTPUT_CSV = OUTPUT_DIR / "urban_priority_hotspots.csv"

SOURCE_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32618"

CELL_SIZE = 500.0  # metros


# ============================================================
# UTILIDADES
# ============================================================

def print_header(title):
    print("=" * 60)
    print(title)
    print("Urban AI Bucaramanga")
    print("=" * 60)


def validate_columns(gdf):
    required = [
        "priority_probability",
        "final_priority",
        "ndvi",
        "ndbi",
        "lst",
    ]

    missing = [column for column in required if column not in gdf.columns]

    if missing:
        raise ValueError(
            "Faltan columnas requeridas en el GeoPackage: "
            + ", ".join(missing)
        )


def safe_numeric(gdf, columns):
    for column in columns:
        gdf[column] = pd.to_numeric(
            gdf[column],
            errors="coerce",
        )

    return gdf


# ============================================================
# CREAR GRID ESPACIAL
# ============================================================

def create_grid(gdf_metric):
    minx, miny, maxx, maxy = gdf_metric.total_bounds

    # Alinear la extensión a la cuadrícula
    minx = np.floor(minx / CELL_SIZE) * CELL_SIZE
    miny = np.floor(miny / CELL_SIZE) * CELL_SIZE
    maxx = np.ceil(maxx / CELL_SIZE) * CELL_SIZE
    maxy = np.ceil(maxy / CELL_SIZE) * CELL_SIZE

    cells = []

    x_values = np.arange(minx, maxx, CELL_SIZE)
    y_values = np.arange(miny, maxy, CELL_SIZE)

    cell_id = 0

    for x in x_values:
        for y in y_values:
            geometry = box(
                x,
                y,
                x + CELL_SIZE,
                y + CELL_SIZE,
            )

            cells.append(
                {
                    "cell_id": cell_id,
                    "geometry": geometry,
                }
            )

            cell_id += 1

    grid = gpd.GeoDataFrame(
        cells,
        geometry="geometry",
        crs=METRIC_CRS,
    )

    return grid


# ============================================================
# MAIN
# ============================================================

def main():

    print_header("PRIORITY HOTSPOTS")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # CARGA
    # --------------------------------------------------------

    if not INPUT_GPKG.exists():
        raise FileNotFoundError(
            f"No existe el archivo de entrada:\n{INPUT_GPKG}"
        )

    gdf = gpd.read_file(INPUT_GPKG)

    print()
    print("=== DATASET ===")
    print(f"Observaciones: {len(gdf):,}")

    if gdf.empty:
        raise ValueError("El GeoPackage está vacío.")

    validate_columns(gdf)

    # --------------------------------------------------------
    # CRS
    # --------------------------------------------------------

    if gdf.crs is None:
        raise ValueError(
            "El GeoPackage no tiene CRS definido."
        )

    print()
    print("=== VALIDACIÓN ===")

    valid = gdf.geometry.is_valid
    empty = gdf.geometry.is_empty
    null = gdf.geometry.isna()

    print(f"Geometrías válidas: {valid.sum():,}")
    print(f"Geometrías vacías: {(empty).sum():,}")
    print(f"Geometrías nulas: {(null).sum():,}")
    print(f"CRS: {gdf.crs}")

    if not valid.all():
        raise ValueError(
            "Existen geometrías inválidas."
        )

    if empty.any():
        raise ValueError(
            "Existen geometrías vacías."
        )

    if null.any():
        raise ValueError(
            "Existen geometrías nulas."
        )

    # --------------------------------------------------------
    # VARIABLES NUMÉRICAS
    # --------------------------------------------------------

    gdf = safe_numeric(
        gdf,
        [
            "priority_probability",
            "ndvi",
            "ndbi",
            "lst",
        ],
    )

    # --------------------------------------------------------
    # PRIORIDAD
    # --------------------------------------------------------

    priority_levels = [
        "MUY_ALTA",
        "ALTA",
    ]

    priority = gdf[
        gdf["final_priority"].isin(priority_levels)
    ].copy()

    print()
    print("=== PRIORIDAD ANALIZADA ===")
    print(
        f"Observaciones prioritarias: {len(priority):,}"
    )

    level_counts = (
        priority["final_priority"]
        .value_counts()
        .to_dict()
    )

    print(
        f"MUY_ALTA: {level_counts.get('MUY_ALTA', 0):,}"
    )

    print(
        f"ALTA: {level_counts.get('ALTA', 0):,}"
    )

    if priority.empty:
        raise ValueError(
            "No existen observaciones de prioridad MUY_ALTA o ALTA."
        )

    # --------------------------------------------------------
    # PROYECCIÓN MÉTRICA
    # --------------------------------------------------------

    priority_metric = priority.to_crs(
        METRIC_CRS
    )

    print()
    print("=== PROYECCIÓN ESPACIAL ===")
    print(f"CRS métrico: {METRIC_CRS}")

    # --------------------------------------------------------
    # GRID DE 500 METROS
    # --------------------------------------------------------

    print()
    print("=== AGRUPACIÓN ESPACIAL ===")
    print(f"Tamaño de celda: {CELL_SIZE:.0f} metros")

    grid = create_grid(priority_metric)

    # --------------------------------------------------------
    # ASIGNAR PUNTOS A CELDAS
    # --------------------------------------------------------

    # Las geometrías originales son puntos o celdas muy pequeñas.
    # Usamos centroides para asignar cada observación a la celda.
    points = priority_metric.copy()

    points["sample_point"] = points.geometry.centroid

    point_gdf = gpd.GeoDataFrame(
        points.drop(columns="geometry"),
        geometry="sample_point",
        crs=METRIC_CRS,
    )

    joined = gpd.sjoin(
        point_gdf,
        grid,
        how="inner",
        predicate="within",
    )

    if joined.empty:
        raise ValueError(
            "No fue posible asignar observaciones a las celdas espaciales."
        )

    # --------------------------------------------------------
    # AGREGACIÓN
    # --------------------------------------------------------

    grouped = (
        joined
        .groupby("cell_id")
        .agg(
            observations=(
                "priority_probability",
                "count",
            ),
            mean_probability=(
                "priority_probability",
                "mean",
            ),
            max_probability=(
                "priority_probability",
                "max",
            ),
            mean_ndvi=(
                "ndvi",
                "mean",
            ),
            mean_ndbi=(
                "ndbi",
                "mean",
            ),
            mean_lst=(
                "lst",
                "mean",
            ),
            very_high_count=(
                "final_priority",
                lambda x: (x == "MUY_ALTA").sum(),
            ),
            high_count=(
                "final_priority",
                lambda x: (x == "ALTA").sum(),
            ),
        )
        .reset_index()
    )

    print(
        f"Celdas ocupadas: {len(grouped):,}"
    )

    # --------------------------------------------------------
    # UNIR GRID + ESTADÍSTICAS
    # --------------------------------------------------------

    hotspots = grid.merge(
        grouped,
        on="cell_id",
        how="inner",
    )

    hotspots = gpd.GeoDataFrame(
        hotspots,
        geometry="geometry",
        crs=METRIC_CRS,
    )

    # --------------------------------------------------------
    # ÁREA REAL
    # --------------------------------------------------------

    # Cada celda es de 500 x 500 m = 250,000 m² = 25 ha.
    hotspots["area_m2"] = (
        hotspots.geometry.area
    )

    hotspots["area_ha"] = (
        hotspots["area_m2"] / 10_000.0
    )

    # --------------------------------------------------------
    # DENSIDAD
    # --------------------------------------------------------

    hotspots["priority_density"] = (
        hotspots["observations"]
        / hotspots["area_ha"]
    )

    # Normalización de densidad para evitar que los valores
    # absolutos dominen el hotspot score.
    density_max = hotspots["priority_density"].max()

    if density_max > 0:
        hotspots["density_normalized"] = (
            hotspots["priority_density"]
            / density_max
        )
    else:
        hotspots["density_normalized"] = 0.0

    # --------------------------------------------------------
    # SCORE DEL HOTSPOT
    # --------------------------------------------------------

    hotspots["hotspot_score"] = (
        0.50 * hotspots["mean_probability"]
        + 0.30 * hotspots["density_normalized"]
        + 0.20 * (
            hotspots["very_high_count"]
            / hotspots["observations"]
        )
    )

    # --------------------------------------------------------
    # RANKING
    # --------------------------------------------------------

    hotspots = hotspots.sort_values(
        [
            "hotspot_score",
            "observations",
            "mean_probability",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(drop=True)

    hotspots["hotspot_rank"] = (
        np.arange(len(hotspots)) + 1
    )

    # --------------------------------------------------------
    # CENTROIDES EN CRS MÉTRICO
    # --------------------------------------------------------

    # IMPORTANTE:
    # El centroide se calcula antes de volver a EPSG:4326.
    centroids_metric = (
        hotspots.geometry.centroid
    )

    hotspots["centroid_x_m"] = (
        centroids_metric.x
    )

    hotspots["centroid_y_m"] = (
        centroids_metric.y
    )

    # --------------------------------------------------------
    # EXPORTACIÓN GEOGRÁFICA EN EPSG:4326
    # --------------------------------------------------------

    hotspots_wgs84 = hotspots.to_crs(
        SOURCE_CRS
    )

    # Transformar los centroides calculados en CRS métrico
    # directamente a EPSG:4326.
    centroids_wgs84 = gpd.GeoSeries(
        centroids_metric,
        crs=METRIC_CRS
    ).to_crs(SOURCE_CRS)

    hotspots_wgs84["longitude"] = (
        centroids_wgs84.x.to_numpy()
    )

    hotspots_wgs84["latitude"] = (
        centroids_wgs84.y.to_numpy()
    )

    # --------------------------------------------------------
    # ESTADÍSTICAS
    # --------------------------------------------------------

    print()
    print("=== HOTSPOTS DETECTADOS ===")
    print(
        f"Hotspots: {len(hotspots_wgs84):,}"
    )

    print(
        f"Observaciones agrupadas: "
        f"{int(hotspots_wgs84['observations'].sum()):,}"
    )

    print(
        f"Área total de hotspots: "
        f"{hotspots_wgs84['area_ha'].sum():,.2f} ha"
    )

    # --------------------------------------------------------
    # TOP 10
    # --------------------------------------------------------

    top10_columns = [
        "hotspot_rank",
        "observations",
        "mean_probability",
        "max_probability",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "area_ha",
        "priority_density",
        "hotspot_score",
        "longitude",
        "latitude",
    ]

    print()
    print("=== TOP 10 HOTSPOTS ===")

    print(
        hotspots_wgs84[
            top10_columns
        ]
        .head(10)
        .to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    # --------------------------------------------------------
    # ESTADÍSTICAS GENERALES
    # --------------------------------------------------------

    print()
    print("=== ESTADÍSTICAS HOTSPOTS ===")

    print(
        "Hotspot score mínimo: "
        f"{hotspots_wgs84['hotspot_score'].min():.6f}"
    )

    print(
        "Hotspot score máximo: "
        f"{hotspots_wgs84['hotspot_score'].max():.6f}"
    )

    print(
        "Hotspot score medio: "
        f"{hotspots_wgs84['hotspot_score'].mean():.6f}"
    )

    print(
        "Observaciones promedio/hotspot: "
        f"{hotspots_wgs84['observations'].mean():.2f}"
    )

    print(
        "Densidad mínima: "
        f"{hotspots_wgs84['priority_density'].min():.4f}"
        " obs/ha"
    )

    print(
        "Densidad máxima: "
        f"{hotspots_wgs84['priority_density'].max():.4f}"
        " obs/ha"
    )

    print(
        "Área promedio/hotspot: "
        f"{hotspots_wgs84['area_ha'].mean():.2f} ha"
    )

    # --------------------------------------------------------
    # EXPORTAR GPKG
    # --------------------------------------------------------

    export_columns = [
        "hotspot_rank",
        "observations",
        "mean_probability",
        "max_probability",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "very_high_count",
        "high_count",
        "area_m2",
        "area_ha",
        "priority_density",
        "density_normalized",
        "hotspot_score",
        "longitude",
        "latitude",
        "geometry",
    ]

    export_gdf = hotspots_wgs84[
        export_columns
    ].copy()

    # Eliminar cualquier archivo anterior
    if OUTPUT_GPKG.exists():
        OUTPUT_GPKG.unlink()

    export_gdf.to_file(
        OUTPUT_GPKG,
        layer="priority_hotspots",
        driver="GPKG",
    )

    # --------------------------------------------------------
    # GEOJSON
    # --------------------------------------------------------

    if OUTPUT_GEOJSON.exists():
        OUTPUT_GEOJSON.unlink()

    export_gdf.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    csv_df = export_gdf.drop(
        columns="geometry"
    )

    csv_df.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # --------------------------------------------------------
    # VALIDACIÓN FINAL
    # --------------------------------------------------------

    print()
    print("=== VALIDACIÓN FINAL ===")

    checks = {
        "Hotspots > 0":
            len(export_gdf) > 0,

        "Observaciones > 0":
            export_gdf["observations"].sum() > 0,

        "Área > 0":
            export_gdf["area_ha"].sum() > 0,

        "Densidad > 0":
            export_gdf["priority_density"].max() > 0,

        "Scores válidos":
            export_gdf["hotspot_score"]
            .between(0, 1)
            .all(),

        "Geometrías válidas":
            export_gdf.geometry.is_valid.all(),

        "Sin geometrías vacías":
            (~export_gdf.geometry.is_empty).all(),

        "Sin geometrías nulas":
            (~export_gdf.geometry.isna()).all(),

        "CRS definido":
            export_gdf.crs is not None,
    }

    for name, result in checks.items():
        print(
            f"[{'OK' if result else 'ERROR'}] {name}"
        )

    if not all(checks.values()):
        raise ValueError(
            "La validación final de hotspots falló."
        )

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    print()
    print("=== RESULTADOS ===")

    print(
        "GeoPackage:"
    )
    print(OUTPUT_GPKG)

    print(
        "GeoJSON:"
    )
    print(OUTPUT_GEOJSON)

    print(
        "CSV:"
    )
    print(OUTPUT_CSV)

    print()
    print("Proceso completado correctamente.")


if __name__ == "__main__":
    main()