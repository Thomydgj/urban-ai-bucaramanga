"""
PRIORITY INTERVENTION MASTER VALIDATION
Urban AI Bucaramanga

Valida la capa maestra final de intervención.
"""

from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODELING_DIR = (
    PROJECT_ROOT /
    "data" /
    "processed" /
    "modeling"
)

MASTER_GPKG = (
    MODELING_DIR /
    "urban_ai_master_intervention.gpkg"
)

MASTER_GEOJSON = (
    MODELING_DIR /
    "urban_ai_master_intervention.geojson"
)

MASTER_CSV = (
    MODELING_DIR /
    "urban_ai_master_intervention.csv"
)

OUTPUT_VALIDATION = (
    MODELING_DIR /
    "urban_ai_master_validation.csv"
)

EXPECTED_ZONES = 224
EXPECTED_OBSERVATIONS = 17434
EXPECTED_AREA_HA = 5600.0


# ============================================================
# UTILIDADES
# ============================================================

validation_results = []


def check(name, condition, details=""):
    status = "OK" if condition else "ERROR"

    validation_results.append(
        {
            "validation": name,
            "status": status,
            "details": details,
        }
    )

    if condition:
        print(f"[OK] {name}")
    else:
        print(f"[ERROR] {name}")

        if details:
            print(f"       {details}")


def fail(message):
    print(f"\n[ERROR] {message}")
    sys.exit(1)


def check_file(path, name):
    exists = path.exists()

    check(
        f"{name} existe",
        exists,
        str(path),
    )

    if not exists:
        fail(
            f"No existe el archivo requerido: {path}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRIORITY INTERVENTION MASTER VALIDATION")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    # --------------------------------------------------------
    # ARCHIVOS
    # --------------------------------------------------------

    print("\n=== ARCHIVOS ===")

    check_file(
        MASTER_GPKG,
        "GeoPackage maestro",
    )

    check_file(
        MASTER_GEOJSON,
        "GeoJSON maestro",
    )

    check_file(
        MASTER_CSV,
        "CSV maestro",
    )

    # --------------------------------------------------------
    # CARGAR DATOS
    # --------------------------------------------------------

    print("\n=== CARGANDO CAPA MAESTRA ===")

    try:
        master = gpd.read_file(
            MASTER_GPKG,
            layer="master_intervention",
        )
    except Exception:
        master = gpd.read_file(
            MASTER_GPKG
        )

    print(
        f"Zonas cargadas: {len(master):,}"
    )

    # --------------------------------------------------------
    # ESTRUCTURA
    # --------------------------------------------------------

    print("\n=== ESTRUCTURA ===")

    required_columns = [
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

    missing = [
        column
        for column in required_columns
        if column not in master.columns
    ]

    check(
        "Todas las columnas requeridas existen",
        len(missing) == 0,
        f"Faltantes: {missing}",
    )

    if missing:
        fail(
            f"Faltan columnas: {missing}"
        )

    # --------------------------------------------------------
    # CANTIDAD
    # --------------------------------------------------------

    print("\n=== CANTIDAD ===")

    check(
        "Cantidad de zonas",
        len(master) == EXPECTED_ZONES,
        (
            f"Encontradas: {len(master):,}; "
            f"esperadas: {EXPECTED_ZONES:,}"
        ),
    )

    # --------------------------------------------------------
    # IDS
    # --------------------------------------------------------

    print("\n=== IDENTIFICADORES ===")

    check(
        "IDs no nulos",
        master["zone_id"].notna().all(),
    )

    check(
        "IDs únicos",
        master["zone_id"].is_unique,
    )

    # --------------------------------------------------------
    # CRS
    # --------------------------------------------------------

    print("\n=== CRS ===")

    print(
        f"CRS: {master.crs}"
    )

    check(
        "CRS definido",
        master.crs is not None,
    )

    check(
        "CRS correcto",
        (
            master.crs is not None
            and master.crs.to_epsg() == 4326
        ),
        f"CRS detectado: {master.crs}",
    )

    # --------------------------------------------------------
    # GEOMETRÍAS
    # --------------------------------------------------------

    print("\n=== GEOMETRÍAS ===")

    invalid = int(
        (~master.geometry.is_valid).sum()
    )

    empty = int(
        master.geometry.is_empty.sum()
    )

    null = int(
        master.geometry.isna().sum()
    )

    print(
        f"Geometrías inválidas: {invalid}"
    )

    print(
        f"Geometrías vacías:    {empty}"
    )

    print(
        f"Geometrías nulas:     {null}"
    )

    check(
        "Geometrías válidas",
        invalid == 0,
    )

    check(
        "Sin geometrías vacías",
        empty == 0,
    )

    check(
        "Sin geometrías nulas",
        null == 0,
    )

    # --------------------------------------------------------
    # VARIABLES NUMÉRICAS
    # --------------------------------------------------------

    print("\n=== VARIABLES NUMÉRICAS ===")

    numeric_columns = [
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
        "centroid_x",
        "centroid_y",
    ]

    numeric_ok = True

    for column in numeric_columns:

        if not pd.api.types.is_numeric_dtype(
            master[column]
        ):
            numeric_ok = False
            print(
                f"[ERROR] {column} no es numérica"
            )

        if master[column].isna().any():
            numeric_ok = False
            print(
                f"[ERROR] {column} contiene nulos"
            )

    check(
        "Variables numéricas válidas",
        numeric_ok,
    )

    # --------------------------------------------------------
    # SCORES
    # --------------------------------------------------------

    print("\n=== SCORES ===")

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

        print(
            f"{column}: "
            f"min={minimum:.6f} "
            f"max={maximum:.6f}"
        )

        check(
            f"{column} dentro de [0,1]",
            minimum >= 0
            and maximum <= 1,
        )

    check(
        "Max probability >= mean probability",
        (
            master["max_probability"]
            >= master["mean_probability"]
        ).all(),
    )

    # --------------------------------------------------------
    # OBSERVACIONES
    # --------------------------------------------------------

    print("\n=== OBSERVACIONES ===")

    total_observations = int(
        master["observations"].sum()
    )

    print(
        f"Observaciones: {total_observations:,}"
    )

    check(
        "Observaciones prioritarias",
        total_observations
        == EXPECTED_OBSERVATIONS,
        (
            f"Encontradas: {total_observations:,}; "
            f"esperadas: {EXPECTED_OBSERVATIONS:,}"
        ),
    )

    check(
        "Todas las zonas tienen observaciones",
        (
            master["observations"] > 0
        ).all(),
    )

    # --------------------------------------------------------
    # ÁREA
    # --------------------------------------------------------

    print("\n=== ÁREA ===")

    total_area = float(
        master["area_ha"].sum()
    )

    print(
        f"Área total: {total_area:,.2f} ha"
    )

    area_error = abs(
        total_area - EXPECTED_AREA_HA
    )

    print(
        f"Error de área: "
        f"{area_error:.8f} ha"
    )

    check(
        "Área total correcta",
        area_error < 0.01,
    )

    check(
        "Todas las áreas son positivas",
        (
            master["area_ha"] > 0
        ).all(),
    )

    # --------------------------------------------------------
    # RANKINGS
    # --------------------------------------------------------

    print("\n=== RANKINGS ===")

    operational_ranks = sorted(
        master["operational_rank"]
        .astype(int)
        .tolist()
    )

    expected_ranks = list(
        range(1, EXPECTED_ZONES + 1)
    )

    check(
        "Operational rank completo",
        operational_ranks == expected_ranks,
    )

    check(
        "Operational rank único",
        master["operational_rank"].is_unique,
    )

    hotspot_ranks = sorted(
        master["hotspot_rank"]
        .astype(int)
        .tolist()
    )

    expected_hotspot_ranks = list(
        range(1, EXPECTED_ZONES + 1)
    )

    check(
        "Hotspot rank completo",
        hotspot_ranks == expected_hotspot_ranks,
    )

    check(
        "Hotspot rank único",
        master["hotspot_rank"].is_unique,
    )

    # --------------------------------------------------------
    # CATEGORÍAS
    # --------------------------------------------------------

    print("\n=== CATEGORÍAS ===")

    valid_levels = {
        "ALTA",
        "CRITICA",
        "MEDIA",
    }

    valid_types = {
        "DIAGNOSTICO_COMPLEMENTARIO",
        "INFRAESTRUCTURA_VERDE",
        "GESTION_SUPERFICIES",
        "INTERVENCION_INTEGRAL",
        "MITIGACION_TERMICA",
    }

    valid_timeframes = {
        "INMEDIATO",
        "CORTO_PLAZO",
        "MEDIANO_PLAZO",
    }

    actual_levels = set(
        master["intervention_level"]
        .dropna()
        .unique()
    )

    actual_types = set(
        master["intervention_type"]
        .dropna()
        .unique()
    )

    actual_timeframes = set(
        master["priority_timeframe"]
        .dropna()
        .unique()
    )

    print(
        "Niveles:",
        sorted(actual_levels),
    )

    print(
        "Tipos:",
        sorted(actual_types),
    )

    print(
        "Plazos:",
        sorted(actual_timeframes),
    )

    check(
        "Niveles de intervención válidos",
        actual_levels.issubset(valid_levels),
    )

    check(
        "Tipos de intervención válidos",
        actual_types.issubset(valid_types),
    )

    check(
        "Plazos de intervención válidos",
        actual_timeframes.issubset(
            valid_timeframes
        ),
    )

    # --------------------------------------------------------
    # TEXTOS
    # --------------------------------------------------------

    print("\n=== RECOMENDACIONES ===")

    text_columns = [
        "recommendation",
        "intervention_objective",
        "monitoring_indicator",
        "priority_timeframe",
        "priority_reason",
        "action_package",
    ]

    for column in text_columns:

        non_null = (
            master[column]
            .notna()
            .all()
        )

        non_empty = (
            master[column]
            .astype(str)
            .str.strip()
            .ne("")
            .all()
        )

        check(
            f"{column} completo",
            non_null and non_empty,
        )

    # --------------------------------------------------------
    # PORCENTAJES
    # --------------------------------------------------------

    print("\n=== PORCENTAJES ===")

    observation_percentage_sum = float(
        master["observation_percentage"].sum()
    )

    area_percentage_sum = float(
        master["area_percentage"].sum()
    )

    print(
        "Suma porcentaje observaciones:",
        f"{observation_percentage_sum:.6f}",
    )

    print(
        "Suma porcentaje área:",
        f"{area_percentage_sum:.6f}",
    )

    check(
        "Porcentaje de observaciones suma 100",
        abs(
            observation_percentage_sum - 100
        ) < 0.01,
    )

    check(
        "Porcentaje de área suma 100",
        abs(
            area_percentage_sum - 100
        ) < 0.01,
    )

    # --------------------------------------------------------
    # CENTROIDES
    # --------------------------------------------------------

    print("\n=== CENTROIDES ===")

    centroid_x_valid = (
        master["centroid_x"].notna().all()
    )

    centroid_y_valid = (
        master["centroid_y"].notna().all()
    )

    check(
        "Centroides X válidos",
        centroid_x_valid,
    )

    check(
        "Centroides Y válidos",
        centroid_y_valid,
    )

    # Comparación aproximada con geometría
    geometric_centroids = (
        master.geometry.centroid
    )

    x_error = (
        geometric_centroids.x
        - master["centroid_x"]
    ).abs().max()

    y_error = (
        geometric_centroids.y
        - master["centroid_y"]
    ).abs().max()

    print(
        f"Error máximo X: {x_error:.8f}"
    )

    print(
        f"Error máximo Y: {y_error:.8f}"
    )

    check(
        "Centroides X consistentes",
        x_error < 1e-6,
    )

    check(
        "Centroides Y consistentes",
        y_error < 1e-6,
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    print("\n=== CONSISTENCIA CSV ===")

    csv = pd.read_csv(
        MASTER_CSV
    )

    print(
        f"CSV: {len(csv):,} registros"
    )

    check(
        "CSV y GeoPackage tienen misma cantidad",
        len(csv) == len(master),
    )

    check(
        "CSV contiene zone_id",
        "zone_id" in csv.columns,
    )

    if "zone_id" in csv.columns:

        check(
            "IDs CSV coinciden",
            set(csv["zone_id"])
            == set(master["zone_id"]),
        )

    # --------------------------------------------------------
    # GEOJSON
    # --------------------------------------------------------

    print("\n=== CONSISTENCIA GEOJSON ===")

    try:
        geojson = gpd.read_file(
            MASTER_GEOJSON
        )

        print(
            f"GeoJSON: {len(geojson):,} registros"
        )

        check(
            "GeoJSON y GeoPackage tienen "
            "misma cantidad",
            len(geojson) == len(master),
        )

        check(
            "GeoJSON CRS definido",
            geojson.crs is not None,
        )

        check(
            "GeoJSON geometrías válidas",
            geojson.geometry.is_valid.all(),
        )

    except Exception as exc:

        check(
            "GeoJSON legible",
            False,
            str(exc),
        )

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 60)

    total_checks = len(
        validation_results
    )

    passed = sum(
        item["status"] == "OK"
        for item in validation_results
    )

    errors = (
        total_checks - passed
    )

    print(
        f"Validaciones: {total_checks}"
    )

    print(
        f"Correctas:    {passed}"
    )

    print(
        f"Errores:      {errors}"
    )

    # --------------------------------------------------------
    # EXPORTAR RESULTADOS
    # --------------------------------------------------------

    validation_df = pd.DataFrame(
        validation_results
    )

    validation_df.to_csv(
        OUTPUT_VALIDATION,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\nResultado guardado en:"
    )

    print(
        OUTPUT_VALIDATION
    )

    # --------------------------------------------------------
    # RESULTADO FINAL
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    if errors == 0:

        print(
            "CAPA MAESTRA VALIDADA CORRECTAMENTE"
        )

        print(
            "Todos los controles fueron superados."
        )

    else:

        print(
            "VALIDACIÓN CON ERRORES"
        )

        print(
            "Revisar las validaciones marcadas "
            "como ERROR."
        )

        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()