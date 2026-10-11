"""
PRIORITY INTERVENTION SUMMARY
Urban AI Bucaramanga

Genera un resumen ejecutivo de las zonas de intervención
a partir de:

    data/processed/modeling/urban_ai_intervention_zones.gpkg

Salidas:

    data/processed/modeling/priority_intervention_summary.csv
    data/processed/modeling/priority_intervention_type_summary.csv
    data/processed/modeling/priority_intervention_condition_summary.csv
    data/processed/modeling/priority_intervention_level_summary.csv
"""

from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_GPKG = (
    BASE_DIR
    / "data"
    / "processed"
    / "modeling"
    / "urban_ai_intervention_zones.gpkg"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "modeling"
)

OUTPUT_SUMMARY = OUTPUT_DIR / "priority_intervention_summary.csv"
OUTPUT_TYPE = OUTPUT_DIR / "priority_intervention_type_summary.csv"
OUTPUT_CONDITION = OUTPUT_DIR / "priority_intervention_condition_summary.csv"
OUTPUT_LEVEL = OUTPUT_DIR / "priority_intervention_level_summary.csv"


# ============================================================
# UTILIDADES
# ============================================================

def fail(message: str):
    print()
    print("=" * 60)
    print("ERROR")
    print("=" * 60)
    print(message)
    print()
    sys.exit(1)


def require_columns(gdf, columns):
    missing = [c for c in columns if c not in gdf.columns]

    if missing:
        fail(
            "Faltan columnas requeridas:\n"
            + "\n".join(f"  - {c}" for c in missing)
        )


def safe_numeric(gdf, columns):
    for column in columns:
        gdf[column] = pd.to_numeric(
            gdf[column],
            errors="coerce"
        )


def weighted_mean(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)

    mask = (
        np.isfinite(values)
        & np.isfinite(weights)
        & (weights >= 0)
    )

    values = values[mask]
    weights = weights[mask]

    if len(values) == 0 or weights.sum() == 0:
        return np.nan

    return float(np.average(values, weights=weights))


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRIORITY INTERVENTION SUMMARY")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CARGAR DATOS
    # --------------------------------------------------------

    print()
    print("=== ARCHIVO DE ENTRADA ===")

    print(f"GeoPackage:")
    print(INPUT_GPKG)

    if not INPUT_GPKG.exists():
        fail(
            "No existe el GeoPackage de zonas de intervención."
        )

    gdf = gpd.read_file(INPUT_GPKG)

    print()
    print("=== DATASET ===")
    print(f"Zonas cargadas: {len(gdf):,}")

    if len(gdf) == 0:
        fail("El GeoPackage no contiene zonas.")

    # --------------------------------------------------------
    # COLUMNAS
    # --------------------------------------------------------

    required_columns = [
        "zone_id",
        "operational_rank",
        "observations",
        "area_ha",
        "mean_probability",
        "hotspot_score",
        "operational_score",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "priority_density",
        "dominant_condition",
        "intervention_level",
        "intervention_type",
        "observation_percentage",
        "area_percentage",
    ]

    print()
    print("=== ESTRUCTURA ===")

    require_columns(
        gdf,
        required_columns
    )

    print("[OK] Todas las columnas requeridas existen")

    # --------------------------------------------------------
    # CRS
    # --------------------------------------------------------

    print()
    print("=== CRS ===")

    print(f"CRS: {gdf.crs}")

    if gdf.crs is None:
        fail("La capa no tiene CRS definido.")

    # --------------------------------------------------------
    # GEOMETRÍAS
    # --------------------------------------------------------

    print()
    print("=== GEOMETRÍAS ===")

    invalid = int((~gdf.geometry.is_valid).sum())
    empty = int(gdf.geometry.is_empty.sum())
    null = int(gdf.geometry.isna().sum())

    print(f"Inválidas: {invalid}")
    print(f"Vacías:    {empty}")
    print(f"Nulas:     {null}")

    if invalid > 0:
        fail("Existen geometrías inválidas.")

    if empty > 0:
        fail("Existen geometrías vacías.")

    if null > 0:
        fail("Existen geometrías nulas.")

    print("[OK] Geometrías válidas")

    # --------------------------------------------------------
    # CONVERSIÓN NUMÉRICA
    # --------------------------------------------------------

    numeric_columns = [
        "operational_rank",
        "observations",
        "area_ha",
        "mean_probability",
        "hotspot_score",
        "operational_score",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "priority_density",
        "observation_percentage",
        "area_percentage",
    ]

    safe_numeric(
        gdf,
        numeric_columns
    )

    # --------------------------------------------------------
    # VALIDACIÓN NUMÉRICA
    # --------------------------------------------------------

    print()
    print("=== VALIDACIÓN NUMÉRICA ===")

    for column in numeric_columns:

        null_count = int(
            gdf[column].isna().sum()
        )

        if null_count > 0:
            fail(
                f"La variable {column} contiene "
                f"{null_count} valores nulos."
            )

        infinite_count = int(
            np.isinf(
                gdf[column].to_numpy(dtype=float)
            ).sum()
        )

        if infinite_count > 0:
            fail(
                f"La variable {column} contiene "
                f"{infinite_count} valores infinitos."
            )

    print("[OK] Variables numéricas válidas")

    # --------------------------------------------------------
    # VALIDACIÓN DE IDS
    # --------------------------------------------------------

    print()
    print("=== IDENTIFICADORES ===")

    duplicated_ids = int(
        gdf["zone_id"].duplicated().sum()
    )

    if duplicated_ids > 0:
        fail(
            f"Existen {duplicated_ids} zone_id duplicados."
        )

    print("[OK] IDs únicos")

    # --------------------------------------------------------
    # VALIDACIÓN DE RANKING
    # --------------------------------------------------------

    expected_ranks = set(
        range(
            1,
            len(gdf) + 1
        )
    )

    actual_ranks = set(
        gdf["operational_rank"].astype(int)
    )

    if actual_ranks != expected_ranks:
        fail(
            "El ranking operacional no es continuo "
            "desde 1 hasta el número de zonas."
        )

    print("[OK] Ranking operacional completo")

    # --------------------------------------------------------
    # VARIABLES PRINCIPALES
    # --------------------------------------------------------

    total_zones = len(gdf)

    total_observations = int(
        gdf["observations"].sum()
    )

    total_area = float(
        gdf["area_ha"].sum()
    )

    total_probability_weighted = weighted_mean(
        gdf["mean_probability"],
        gdf["observations"]
    )

    total_hotspot_weighted = weighted_mean(
        gdf["hotspot_score"],
        gdf["observations"]
    )

    total_operational_weighted = weighted_mean(
        gdf["operational_score"],
        gdf["observations"]
    )

    mean_ndvi_weighted = weighted_mean(
        gdf["mean_ndvi"],
        gdf["observations"]
    )

    mean_ndbi_weighted = weighted_mean(
        gdf["mean_ndbi"],
        gdf["observations"]
    )

    mean_lst_weighted = weighted_mean(
        gdf["mean_lst"],
        gdf["observations"]
    )

    mean_density = float(
        gdf["priority_density"].mean()
    )

    # --------------------------------------------------------
    # DISTRIBUCIONES
    # --------------------------------------------------------

    print()
    print("=== DISTRIBUCIÓN POR NIVEL ===")

    level_counts = (
        gdf["intervention_level"]
        .value_counts()
        .sort_index()
    )

    print(level_counts.to_string())

    print()
    print("=== DISTRIBUCIÓN POR TIPO ===")

    type_counts = (
        gdf["intervention_type"]
        .value_counts()
        .sort_values(
            ascending=False
        )
    )

    print(type_counts.to_string())

    print()
    print("=== CONDICIONES DOMINANTES ===")

    condition_counts = (
        gdf["dominant_condition"]
        .value_counts()
        .sort_values(
            ascending=False
        )
    )

    print(condition_counts.to_string())

    # --------------------------------------------------------
    # TOP 10
    # --------------------------------------------------------

    print()
    print("=== TOP 10 ZONAS ===")

    top10 = (
        gdf
        .sort_values(
            "operational_rank"
        )
        .head(10)
        [
            [
                "zone_id",
                "operational_rank",
                "observations",
                "area_ha",
                "mean_probability",
                "hotspot_score",
                "operational_score",
                "dominant_condition",
                "intervention_level",
                "intervention_type",
            ]
        ]
    )

    print(
        top10.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # RESUMEN GENERAL
    # --------------------------------------------------------

    summary = pd.DataFrame(
        [
            {
                "metric": "total_zones",
                "value": total_zones,
            },
            {
                "metric": "total_observations",
                "value": total_observations,
            },
            {
                "metric": "total_area_ha",
                "value": total_area,
            },
            {
                "metric": "mean_probability_weighted",
                "value": total_probability_weighted,
            },
            {
                "metric": "mean_hotspot_score_weighted",
                "value": total_hotspot_weighted,
            },
            {
                "metric": "mean_operational_score_weighted",
                "value": total_operational_weighted,
            },
            {
                "metric": "mean_ndvi_weighted",
                "value": mean_ndvi_weighted,
            },
            {
                "metric": "mean_ndbi_weighted",
                "value": mean_ndbi_weighted,
            },
            {
                "metric": "mean_lst_weighted",
                "value": mean_lst_weighted,
            },
            {
                "metric": "mean_priority_density",
                "value": mean_density,
            },
            {
                "metric": "min_operational_score",
                "value": float(
                    gdf["operational_score"].min()
                ),
            },
            {
                "metric": "max_operational_score",
                "value": float(
                    gdf["operational_score"].max()
                ),
            },
        ]
    )

    # --------------------------------------------------------
    # RESUMEN POR NIVEL
    # --------------------------------------------------------

    level_summary = (
        gdf
        .groupby(
            "intervention_level",
            dropna=False
        )
        .apply(
            lambda group: pd.Series(
                {
                    "zones": len(group),
                    "observations": group[
                        "observations"
                    ].sum(),
                    "area_ha": group[
                        "area_ha"
                    ].sum(),
                    "observation_percentage": group[
                        "observation_percentage"
                    ].sum(),
                    "area_percentage": group[
                        "area_percentage"
                    ].sum(),
                    "mean_probability": weighted_mean(
                        group["mean_probability"],
                        group["observations"]
                    ),
                    "mean_hotspot_score": weighted_mean(
                        group["hotspot_score"],
                        group["observations"]
                    ),
                    "mean_operational_score": weighted_mean(
                        group["operational_score"],
                        group["observations"]
                    ),
                    "mean_ndvi": weighted_mean(
                        group["mean_ndvi"],
                        group["observations"]
                    ),
                    "mean_ndbi": weighted_mean(
                        group["mean_ndbi"],
                        group["observations"]
                    ),
                    "mean_lst": weighted_mean(
                        group["mean_lst"],
                        group["observations"]
                    ),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # RESUMEN POR TIPO
    # --------------------------------------------------------

    type_summary = (
        gdf
        .groupby(
            "intervention_type",
            dropna=False
        )
        .apply(
            lambda group: pd.Series(
                {
                    "zones": len(group),
                    "observations": group[
                        "observations"
                    ].sum(),
                    "area_ha": group[
                        "area_ha"
                    ].sum(),
                    "observation_percentage": group[
                        "observation_percentage"
                    ].sum(),
                    "area_percentage": group[
                        "area_percentage"
                    ].sum(),
                    "mean_probability": weighted_mean(
                        group["mean_probability"],
                        group["observations"]
                    ),
                    "mean_hotspot_score": weighted_mean(
                        group["hotspot_score"],
                        group["observations"]
                    ),
                    "mean_operational_score": weighted_mean(
                        group["operational_score"],
                        group["observations"]
                    ),
                    "mean_ndvi": weighted_mean(
                        group["mean_ndvi"],
                        group["observations"]
                    ),
                    "mean_ndbi": weighted_mean(
                        group["mean_ndbi"],
                        group["observations"]
                    ),
                    "mean_lst": weighted_mean(
                        group["mean_lst"],
                        group["observations"]
                    ),
                }
            ),
            include_groups=False,
        )
        .reset_index()
        .sort_values(
            "mean_operational_score",
            ascending=False
        )
    )

    # --------------------------------------------------------
    # RESUMEN POR CONDICIÓN
    # --------------------------------------------------------

    condition_summary = (
        gdf
        .groupby(
            "dominant_condition",
            dropna=False
        )
        .apply(
            lambda group: pd.Series(
                {
                    "zones": len(group),
                    "observations": group[
                        "observations"
                    ].sum(),
                    "area_ha": group[
                        "area_ha"
                    ].sum(),
                    "observation_percentage": group[
                        "observation_percentage"
                    ].sum(),
                    "area_percentage": group[
                        "area_percentage"
                    ].sum(),
                    "mean_probability": weighted_mean(
                        group["mean_probability"],
                        group["observations"]
                    ),
                    "mean_hotspot_score": weighted_mean(
                        group["hotspot_score"],
                        group["observations"]
                    ),
                    "mean_operational_score": weighted_mean(
                        group["operational_score"],
                        group["observations"]
                    ),
                    "mean_ndvi": weighted_mean(
                        group["mean_ndvi"],
                        group["observations"]
                    ),
                    "mean_ndbi": weighted_mean(
                        group["mean_ndbi"],
                        group["observations"]
                    ),
                    "mean_lst": weighted_mean(
                        group["mean_lst"],
                        group["observations"]
                    ),
                }
            ),
            include_groups=False,
        )
        .reset_index()
        .sort_values(
            "observations",
            ascending=False
        )
    )

    # --------------------------------------------------------
    # EXPORTAR
    # --------------------------------------------------------

    print()
    print("=== EXPORTANDO ===")

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8-sig"
    )

    level_summary.to_csv(
        OUTPUT_LEVEL,
        index=False,
        encoding="utf-8-sig"
    )

    type_summary.to_csv(
        OUTPUT_TYPE,
        index=False,
        encoding="utf-8-sig"
    )

    condition_summary.to_csv(
        OUTPUT_CONDITION,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("Resumen general:")
    print(OUTPUT_SUMMARY)

    print()
    print("Resumen por nivel:")
    print(OUTPUT_LEVEL)

    print()
    print("Resumen por tipo:")
    print(OUTPUT_TYPE)

    print()
    print("Resumen por condición:")
    print(OUTPUT_CONDITION)

    # --------------------------------------------------------
    # VALIDACIÓN FINAL
    # --------------------------------------------------------

    print()
    print("=== VALIDACIÓN FINAL ===")

    errors = []

    if total_zones != 224:
        errors.append(
            f"Número inesperado de zonas: {total_zones}"
        )

    if total_observations != 17434:
        errors.append(
            "Las observaciones no coinciden con "
            "la capa prioritaria esperada."
        )

    if total_area <= 0:
        errors.append(
            "El área total debe ser mayor que cero."
        )

    if not (
        0 <= total_probability_weighted <= 1
    ):
        errors.append(
            "Probability ponderada fuera de rango."
        )

    if not (
        0 <= total_hotspot_weighted <= 1
    ):
        errors.append(
            "Hotspot score fuera de rango."
        )

    if not (
        0 <= total_operational_weighted <= 1
    ):
        errors.append(
            "Operational score fuera de rango."
        )

    if len(level_summary) == 0:
        errors.append(
            "No existen niveles de intervención."
        )

    if len(type_summary) == 0:
        errors.append(
            "No existen tipos de intervención."
        )

    if len(condition_summary) == 0:
        errors.append(
            "No existen condiciones dominantes."
        )

    if errors:

        for error in errors:
            print(f"[ERROR] {error}")

        fail(
            "El resumen no superó la validación final."
        )

    print("[OK] Número de zonas")
    print("[OK] Observaciones prioritarias")
    print("[OK] Área total")
    print("[OK] Probability válida")
    print("[OK] Hotspot score válido")
    print("[OK] Operational score válido")
    print("[OK] Niveles de intervención")
    print("[OK] Tipos de intervención")
    print("[OK] Condiciones dominantes")

    # --------------------------------------------------------
    # RESUMEN EJECUTIVO
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RESUMEN EJECUTIVO")
    print("=" * 60)

    print(
        f"Zonas de intervención: {total_zones:,}"
    )

    print(
        f"Observaciones prioritarias: "
        f"{total_observations:,}"
    )

    print(
        f"Área total: {total_area:,.2f} ha"
    )

    print(
        f"Probability media ponderada: "
        f"{total_probability_weighted:.6f}"
    )

    print(
        f"Hotspot score medio ponderado: "
        f"{total_hotspot_weighted:.6f}"
    )

    print(
        f"Operational score medio ponderado: "
        f"{total_operational_weighted:.6f}"
    )

    print()
    print("=== NIVEL DE INTERVENCIÓN ===")

    print(
        level_summary[
            [
                "intervention_level",
                "zones",
                "observations",
                "area_ha",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("=== TIPO DE INTERVENCIÓN ===")

    print(
        type_summary[
            [
                "intervention_type",
                "zones",
                "observations",
                "area_ha",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("=" * 60)
    print("RESUMEN DE INTERVENCIÓN GENERADO")
    print("Todos los controles fueron superados.")
    print("=" * 60)


if __name__ == "__main__":
    main()