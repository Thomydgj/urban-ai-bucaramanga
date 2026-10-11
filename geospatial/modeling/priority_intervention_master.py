"""
PRIORITY INTERVENTION MASTER
Urban AI Bucaramanga

Integra:
- Hotspots
- Zonas de intervención
- Recomendaciones de intervención

Genera una capa maestra única para análisis, GIS y presentación final.
"""

from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODELING_DIR = PROJECT_ROOT / "data" / "processed" / "modeling"

INPUT_ZONES = (
    MODELING_DIR /
    "urban_ai_intervention_zones.gpkg"
)

INPUT_RECOMMENDATIONS = (
    MODELING_DIR /
    "urban_ai_intervention_recommendations.gpkg"
)

OUTPUT_GPKG = (
    MODELING_DIR /
    "urban_ai_master_intervention.gpkg"
)

OUTPUT_GEOJSON = (
    MODELING_DIR /
    "urban_ai_master_intervention.geojson"
)

OUTPUT_CSV = (
    MODELING_DIR /
    "urban_ai_master_intervention.csv"
)

OUTPUT_SUMMARY = (
    MODELING_DIR /
    "urban_ai_master_summary.csv"
)

OUTPUT_LAYER = "master_intervention"


# ============================================================
# UTILIDADES
# ============================================================

def fail(message):
    print(f"[ERROR] {message}")
    sys.exit(1)


def check_file(path, description):
    if not path.exists():
        fail(
            f"No existe {description}:\n"
            f"{path}"
        )


def validate_geometries(gdf):
    invalid = int((~gdf.geometry.is_valid).sum())
    empty = int(gdf.geometry.is_empty.sum())
    null = int(gdf.geometry.isna().sum())

    print(f"Geometrías inválidas: {invalid}")
    print(f"Geometrías vacías:    {empty}")
    print(f"Geometrías nulas:     {null}")

    if invalid > 0:
        fail("Existen geometrías inválidas.")

    if empty > 0:
        fail("Existen geometrías vacías.")

    if null > 0:
        fail("Existen geometrías nulas.")

    print("[OK] Geometrías válidas")


def require_columns(gdf, columns, dataset_name):
    missing = [
        column
        for column in columns
        if column not in gdf.columns
    ]

    if missing:
        fail(
            f"Faltan columnas en {dataset_name}: "
            f"{missing}"
        )

    print(
        f"[OK] Columnas requeridas presentes en "
        f"{dataset_name}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRIORITY INTERVENTION MASTER")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    # --------------------------------------------------------
    # ARCHIVOS
    # --------------------------------------------------------

    print("\n=== ARCHIVOS DE ENTRADA ===")

    check_file(
        INPUT_ZONES,
        "GeoPackage de zonas de intervención"
    )

    check_file(
        INPUT_RECOMMENDATIONS,
        "GeoPackage de recomendaciones"
    )

    print(
        f"Zonas:\n{INPUT_ZONES}"
    )

    print(
        f"Recomendaciones:\n{INPUT_RECOMMENDATIONS}"
    )

    # --------------------------------------------------------
    # CARGAR DATOS
    # --------------------------------------------------------

    print("\n=== CARGANDO DATOS ===")

    try:
        zones = gpd.read_file(
            INPUT_ZONES,
            layer="intervention_zones"
        )
    except Exception:
        zones = gpd.read_file(INPUT_ZONES)

    try:
        recommendations = gpd.read_file(
            INPUT_RECOMMENDATIONS
        )
    except Exception as exc:
        fail(
            "No fue posible cargar el GeoPackage "
            f"de recomendaciones: {exc}"
        )

    print(
        f"Zonas cargadas:            {len(zones):,}"
    )

    print(
        f"Recomendaciones cargadas:  "
        f"{len(recommendations):,}"
    )

    # --------------------------------------------------------
    # VALIDACIÓN ESTRUCTURAL
    # --------------------------------------------------------

    print("\n=== VALIDACIÓN ESTRUCTURAL ===")

    zone_columns = [
        "zone_id",
        "operational_rank",
        "hotspot_rank",
        "observations",
        "observation_percentage",
        "area_ha",
        "area_percentage",
        "mean_probability",
        "max_probability",
        "hotspot_score",
        "operational_score",
        "priority_density",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "dominant_condition",
        "density_level",
        "intervention_level",
        "priority_class",
        "intervention_type",
        "zone_description",
        "centroid_x",
        "centroid_y",
        "geometry",
    ]

    recommendation_columns = [
        "zone_id",
        "recommendation",
        "intervention_objective",
        "monitoring_indicator",
        "priority_timeframe",
        "priority_reason",
        "action_package",
    ]

    require_columns(
        zones,
        zone_columns,
        "zonas de intervención"
    )

    require_columns(
        recommendations,
        recommendation_columns,
        "recomendaciones"
    )

    # --------------------------------------------------------
    # CRS
    # --------------------------------------------------------

    print("\n=== CRS ===")

    print(
        f"CRS zonas:           {zones.crs}"
    )

    print(
        f"CRS recomendaciones: {recommendations.crs}"
    )

    if zones.crs is None:
        fail("Las zonas no tienen CRS.")

    if recommendations.crs is None:
        fail("Las recomendaciones no tienen CRS.")

    if zones.crs != recommendations.crs:
        print(
            "[INFO] CRS diferentes. "
            "Reproyectando recomendaciones..."
        )

        recommendations = recommendations.to_crs(
            zones.crs
        )

    print(
        f"[OK] CRS maestro: {zones.crs}"
    )

    # --------------------------------------------------------
    # GEOMETRÍAS
    # --------------------------------------------------------

    print("\n=== GEOMETRÍAS ===")

    validate_geometries(zones)
    validate_geometries(recommendations)

    # --------------------------------------------------------
    # CANTIDADES
    # --------------------------------------------------------

    print("\n=== CANTIDAD DE ZONAS ===")

    if len(zones) != len(recommendations):
        print(
            "[ADVERTENCIA] Las cantidades son diferentes."
        )

        print(
            f"Zonas: {len(zones):,}"
        )

        print(
            f"Recomendaciones: "
            f"{len(recommendations):,}"
        )

    else:
        print(
            f"[OK] Ambas capas contienen "
            f"{len(zones):,} zonas"
        )

    # --------------------------------------------------------
    # IDs
    # --------------------------------------------------------

    print("\n=== IDENTIFICADORES ===")

    if zones["zone_id"].isna().any():
        fail(
            "Existen zone_id nulos en las zonas."
        )

    if recommendations["zone_id"].isna().any():
        fail(
            "Existen zone_id nulos en las recomendaciones."
        )

    if zones["zone_id"].duplicated().any():
        fail(
            "Existen zone_id duplicados en las zonas."
        )

    if recommendations["zone_id"].duplicated().any():
        fail(
            "Existen zone_id duplicados en las recomendaciones."
        )

    zone_ids = set(zones["zone_id"])
    recommendation_ids = set(
        recommendations["zone_id"]
    )

    missing_recommendations = (
        zone_ids - recommendation_ids
    )

    extra_recommendations = (
        recommendation_ids - zone_ids
    )

    if missing_recommendations:
        fail(
            "Existen zonas sin recomendaciones: "
            f"{len(missing_recommendations)}"
        )

    if extra_recommendations:
        fail(
            "Existen recomendaciones sin zona "
            f"correspondiente: {len(extra_recommendations)}"
        )

    print("[OK] IDs de zonas únicos")
    print("[OK] IDs de recomendaciones únicos")
    print("[OK] IDs perfectamente coincidentes")

    # --------------------------------------------------------
    # PREPARAR RECOMENDACIONES
    # --------------------------------------------------------

    print("\n=== PREPARANDO RECOMENDACIONES ===")

    recommendation_fields = [
        "zone_id",
        "recommendation",
        "intervention_objective",
        "monitoring_indicator",
        "priority_timeframe",
        "priority_reason",
        "action_package",
    ]

    recommendations_table = (
        recommendations[
            recommendation_fields
        ]
        .copy()
    )

    # --------------------------------------------------------
    # UNIFICACIÓN
    # --------------------------------------------------------

    print("\n=== INTEGRACIÓN ===")

    master = zones.merge(
        recommendations_table,
        on="zone_id",
        how="left",
        validate="one_to_one",
    )

    print(
        f"Filas resultantes: {len(master):,}"
    )

    # --------------------------------------------------------
    # VALIDACIÓN DE INTEGRACIÓN
    # --------------------------------------------------------

    print("\n=== VALIDACIÓN DE INTEGRACIÓN ===")

    recommendation_fields_without_id = [
        column
        for column in recommendation_fields
        if column != "zone_id"
    ]

    for column in recommendation_fields_without_id:

        null_count = int(
            master[column].isna().sum()
        )

        if null_count > 0:
            fail(
                f"La columna {column} tiene "
                f"{null_count} valores nulos."
            )

        print(
            f"[OK] {column}: sin valores nulos"
        )

    if len(master) != len(zones):
        fail(
            "La integración modificó la cantidad "
            "de zonas."
        )

    print(
        "[OK] Cantidad de zonas preservada"
    )

    # --------------------------------------------------------
    # VALIDACIÓN NUMÉRICA
    # --------------------------------------------------------

    print("\n=== VALIDACIÓN NUMÉRICA ===")

    numeric_columns = [
        "observations",
        "area_ha",
        "mean_probability",
        "max_probability",
        "hotspot_score",
        "operational_score",
        "priority_density",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
    ]

    for column in numeric_columns:

        if not pd.api.types.is_numeric_dtype(
            master[column]
        ):
            fail(
                f"La columna {column} no es numérica."
            )

        if master[column].isna().any():
            fail(
                f"La columna {column} contiene "
                "valores nulos."
            )

    print(
        "[OK] Variables numéricas válidas"
    )

    # --------------------------------------------------------
    # VALIDACIÓN DE SCORES
    # --------------------------------------------------------

    score_columns = [
        "mean_probability",
        "max_probability",
        "hotspot_score",
        "operational_score",
    ]

    for column in score_columns:

        minimum = float(
            master[column].min()
        )

        maximum = float(
            master[column].max()
        )

        if minimum < 0 or maximum > 1:
            fail(
                f"{column} fuera del rango [0,1]: "
                f"{minimum} - {maximum}"
            )

        print(
            f"[OK] {column}: "
            f"{minimum:.6f} - {maximum:.6f}"
        )

    # --------------------------------------------------------
    # VALIDACIÓN DE OBSERVACIONES
    # --------------------------------------------------------

    print("\n=== OBSERVACIONES ===")

    total_observations = int(
        master["observations"].sum()
    )

    expected_observations = 17_434

    print(
        f"Observaciones integradas: "
        f"{total_observations:,}"
    )

    print(
        f"Observaciones esperadas:  "
        f"{expected_observations:,}"
    )

    if total_observations != expected_observations:
        print(
            "[ADVERTENCIA] La cantidad no coincide "
            "con el valor esperado del proyecto."
        )
    else:
        print(
            "[OK] Observaciones prioritarias "
            "completamente preservadas"
        )

    # --------------------------------------------------------
    # VALIDACIÓN DE ÁREA
    # --------------------------------------------------------

    print("\n=== ÁREA ===")

    total_area = float(
        master["area_ha"].sum()
    )

    print(
        f"Área total: {total_area:,.2f} ha"
    )

    if (master["area_ha"] <= 0).any():
        fail(
            "Existen zonas con área <= 0."
        )

    print(
        "[OK] Todas las áreas son positivas"
    )

    # --------------------------------------------------------
    # ORDEN FINAL DE COLUMNAS
    # --------------------------------------------------------

    print("\n=== ESTRUCTURA MAESTRA ===")

    preferred_order = [
        "zone_id",
        "operational_rank",
        "hotspot_rank",
        "observations",
        "observation_percentage",
        "area_ha",
        "area_percentage",
        "mean_probability",
        "max_probability",
        "hotspot_score",
        "operational_score",
        "priority_density",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "dominant_condition",
        "density_level",
        "intervention_level",
        "priority_class",
        "intervention_type",
        "zone_description",
        "recommendation",
        "intervention_objective",
        "monitoring_indicator",
        "priority_timeframe",
        "priority_reason",
        "action_package",
        "centroid_x",
        "centroid_y",
        "geometry",
    ]

    existing_order = [
        column
        for column in preferred_order
        if column in master.columns
    ]

    remaining_columns = [
        column
        for column in master.columns
        if column not in existing_order
    ]

    master = master[
        existing_order + remaining_columns
    ]

    print(
        f"Columnas finales: {len(master.columns)}"
    )

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    print("\n=== RESUMEN MAESTRO ===")

    weighted_probability = (
        (
            master["mean_probability"]
            * master["observations"]
        ).sum()
        /
        master["observations"].sum()
    )

    weighted_hotspot = (
        (
            master["hotspot_score"]
            * master["observations"]
        ).sum()
        /
        master["observations"].sum()
    )

    weighted_operational = (
        (
            master["operational_score"]
            * master["observations"]
        ).sum()
        /
        master["observations"].sum()
    )

    summary = pd.DataFrame(
        [
            {
                "zones": len(master),
                "observations": total_observations,
                "area_ha": total_area,
                "weighted_mean_probability":
                    weighted_probability,
                "weighted_mean_hotspot_score":
                    weighted_hotspot,
                "weighted_mean_operational_score":
                    weighted_operational,
            }
        ]
    )

    print(
        f"Zonas: {len(master):,}"
    )

    print(
        f"Observaciones: "
        f"{total_observations:,}"
    )

    print(
        f"Área total: "
        f"{total_area:,.2f} ha"
    )

    print(
        f"Probability media ponderada: "
        f"{weighted_probability:.6f}"
    )

    print(
        f"Hotspot score medio ponderado: "
        f"{weighted_hotspot:.6f}"
    )

    print(
        f"Operational score medio ponderado: "
        f"{weighted_operational:.6f}"
    )

    # --------------------------------------------------------
    # DISTRIBUCIÓN POR NIVEL
    # --------------------------------------------------------

    level_summary = (
        master
        .groupby("intervention_level")
        .agg(
            zones=("zone_id", "count"),
            observations=("observations", "sum"),
            area_ha=("area_ha", "sum"),
            mean_probability=(
                "mean_probability",
                "mean"
            ),
            mean_operational_score=(
                "operational_score",
                "mean"
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # DISTRIBUCIÓN POR TIPO
    # --------------------------------------------------------

    type_summary = (
        master
        .groupby("intervention_type")
        .agg(
            zones=("zone_id", "count"),
            observations=("observations", "sum"),
            area_ha=("area_ha", "sum"),
            mean_operational_score=(
                "operational_score",
                "mean"
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # DISTRIBUCIÓN POR PLAZO
    # --------------------------------------------------------

    timeframe_summary = (
        master
        .groupby("priority_timeframe")
        .agg(
            zones=("zone_id", "count"),
            observations=("observations", "sum"),
            area_ha=("area_ha", "sum"),
            mean_operational_score=(
                "operational_score",
                "mean"
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # EXPORTACIÓN
    # --------------------------------------------------------

    print("\n=== EXPORTANDO ===")

    MODELING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # GeoPackage
    master.to_file(
        OUTPUT_GPKG,
        layer=OUTPUT_LAYER,
        driver="GPKG",
    )

    print(
        f"GeoPackage:\n{OUTPUT_GPKG}"
    )

    # GeoJSON
    master.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    print(
        f"GeoJSON:\n{OUTPUT_GEOJSON}"
    )

    # CSV
    csv_master = master.drop(
        columns=["geometry"],
        errors="ignore"
    )

    csv_master.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"CSV:\n{OUTPUT_CSV}"
    )

    # Resumen
    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Resumen:\n{OUTPUT_SUMMARY}"
    )

    # --------------------------------------------------------
    # RESÚMENES ADICIONALES
    # --------------------------------------------------------

    level_path = (
        MODELING_DIR /
        "urban_ai_master_intervention_level_summary.csv"
    )

    type_path = (
        MODELING_DIR /
        "urban_ai_master_intervention_type_summary.csv"
    )

    timeframe_path = (
        MODELING_DIR /
        "urban_ai_master_timeframe_summary.csv"
    )

    level_summary.to_csv(
        level_path,
        index=False,
        encoding="utf-8-sig",
    )

    type_summary.to_csv(
        type_path,
        index=False,
        encoding="utf-8-sig",
    )

    timeframe_summary.to_csv(
        timeframe_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Resumen por nivel:\n{level_path}"
    )

    print(
        f"Resumen por tipo:\n{type_path}"
    )

    print(
        f"Resumen por plazo:\n{timeframe_path}"
    )

    # --------------------------------------------------------
    # VALIDACIÓN FINAL
    # --------------------------------------------------------

    print("\n=== VALIDACIÓN FINAL ===")

    checks = {
        "Zonas": len(master) == len(zones),
        "IDs únicos":
            master["zone_id"].is_unique,
        "Geometrías válidas":
            master.geometry.is_valid.all(),
        "Sin geometrías vacías":
            (~master.geometry.is_empty).all(),
        "Sin geometrías nulas":
            master.geometry.notna().all(),
        "Observaciones > 0":
            (master["observations"] > 0).all(),
        "Área > 0":
            (master["area_ha"] > 0).all(),
        "Probabilidades válidas":
            master["mean_probability"].between(
                0, 1
            ).all(),
        "Hotspot scores válidos":
            master["hotspot_score"].between(
                0, 1
            ).all(),
        "Operational scores válidos":
            master["operational_score"].between(
                0, 1
            ).all(),
        "Recomendaciones completas":
            master["recommendation"].notna().all(),
        "Objetivos completos":
            master["intervention_objective"].notna().all(),
        "Indicadores completos":
            master["monitoring_indicator"].notna().all(),
        "Plazos completos":
            master["priority_timeframe"].notna().all(),
        "Razones completas":
            master["priority_reason"].notna().all(),
        "Paquetes completos":
            master["action_package"].notna().all(),
    }

    errors = 0

    for name, result in checks.items():

        if result:
            print(f"[OK] {name}")
        else:
            print(f"[ERROR] {name}")
            errors += 1

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    if errors == 0:

        print(
            "CAPA MAESTRA GENERADA CORRECTAMENTE"
        )

        print(
            f"Zonas integradas: {len(master):,}"
        )

        print(
            f"Observaciones: {total_observations:,}"
        )

        print(
            f"Área: {total_area:,.2f} ha"
        )

        print(
            "Todos los controles fueron superados."
        )

    else:

        print(
            f"CAPA MAESTRA CON {errors} ERROR(ES)"
        )

        print(
            "Revisar las validaciones anteriores."
        )

        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()