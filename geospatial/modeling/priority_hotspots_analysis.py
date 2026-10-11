from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_GPKG = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_priority_hotspots.gpkg"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

OUTPUT_CSV = OUTPUT_DIR / "priority_hotspots_analysis.csv"
OUTPUT_GPKG = OUTPUT_DIR / "priority_hotspots_analysis.gpkg"
OUTPUT_GEOJSON = OUTPUT_DIR / "priority_hotspots_analysis.geojson"
OUTPUT_SUMMARY = OUTPUT_DIR / "priority_hotspots_analysis_summary.csv"


REQUIRED_COLUMNS = [
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
]


def classify_condition(row):
    """
    Determina el factor ambiental dominante del hotspot.

    La clasificación es descriptiva:
    - VEGETACION_BAJA: NDVI bajo.
    - SUPERFICIE_CONSTRUIDA: NDBI alto.
    - CALOR_URBANO: LST alta.
    - MULTIFACTORIAL: más de un factor presenta condición elevada.
    - MIXTA: no existe un factor claramente dominante.
    """

    ndvi = row["mean_ndvi"]
    ndbi = row["mean_ndbi"]
    lst = row["mean_lst"]

    vegetation = ndvi <= 0.10
    built = ndbi >= 0.20
    heat = lst >= 43.0

    active = int(vegetation) + int(built) + int(heat)

    if active >= 2:
        return "MULTIFACTORIAL"

    if vegetation:
        return "VEGETACION_BAJA"

    if built:
        return "SUPERFICIE_CONSTRUIDA"

    if heat:
        return "CALOR_URBANO"

    return "MIXTA"


def classify_intervention(row):
    """
    Clasificación operativa basada en hotspot_score.
    """

    score = row["hotspot_score"]

    if score >= 0.85:
        return "CRITICA"

    if score >= 0.70:
        return "ALTA"

    return "MEDIA"


def classify_density(row):
    """
    Clasificación descriptiva de densidad de observaciones prioritarias.
    """

    density = row["priority_density"]

    if density >= 8:
        return "MUY_ALTA"

    if density >= 4:
        return "ALTA"

    if density >= 1:
        return "MEDIA"

    return "BAJA"


def validate_numeric_ranges(gdf):
    errors = []

    probability_columns = [
        "mean_probability",
        "max_probability",
        "hotspot_score",
    ]

    for column in probability_columns:
        invalid = (
            (~np.isfinite(gdf[column]))
            | (gdf[column] < 0)
            | (gdf[column] > 1)
        )

        count = int(invalid.sum())

        if count > 0:
            errors.append(
                f"{column}: {count} valores fuera del rango 0-1"
            )

    for column in [
        "observations",
        "area_ha",
        "priority_density",
    ]:
        invalid = (
            ~np.isfinite(gdf[column])
            | (gdf[column] <= 0)
        )

        count = int(invalid.sum())

        if count > 0:
            errors.append(
                f"{column}: {count} valores inválidos"
            )

    return errors


def main():

    print("=" * 60)
    print("PRIORITY HOTSPOTS ANALYSIS")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # CARGA
    # ---------------------------------------------------------

    if not INPUT_GPKG.exists():
        raise FileNotFoundError(
            f"No existe el GeoPackage:\n{INPUT_GPKG}"
        )

    print("\n=== CARGANDO HOTSPOTS ===")

    gdf = gpd.read_file(INPUT_GPKG)

    print(f"Hotspots: {len(gdf):,}")

    if gdf.empty:
        raise ValueError("El GeoPackage no contiene hotspots.")

    # ---------------------------------------------------------
    # ESTRUCTURA
    # ---------------------------------------------------------

    print("\n=== VALIDACIÓN ESTRUCTURAL ===")

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in gdf.columns
    ]

    if missing:
        raise ValueError(
            "Faltan columnas requeridas:\n"
            + "\n".join(missing)
        )

    print("[OK] Todas las columnas requeridas existen")

    # ---------------------------------------------------------
    # CRS
    # ---------------------------------------------------------

    print("\n=== CRS ===")
    print(f"CRS: {gdf.crs}")

    if gdf.crs is None:
        raise ValueError("La capa no tiene CRS definido.")

    # ---------------------------------------------------------
    # GEOMETRÍAS
    # ---------------------------------------------------------

    print("\n=== GEOMETRÍAS ===")

    invalid = int((~gdf.geometry.is_valid).sum())
    empty = int(gdf.geometry.is_empty.sum())
    null = int(gdf.geometry.isna().sum())

    print(f"Inválidas: {invalid}")
    print(f"Vacías:    {empty}")
    print(f"Nulas:     {null}")

    if invalid > 0:
        raise ValueError("Existen geometrías inválidas.")

    if empty > 0:
        raise ValueError("Existen geometrías vacías.")

    if null > 0:
        raise ValueError("Existen geometrías nulas.")

    print("[OK] Geometrías válidas")

    # ---------------------------------------------------------
    # VALIDACIÓN NUMÉRICA
    # ---------------------------------------------------------

    print("\n=== VALIDACIÓN NUMÉRICA ===")

    numeric_errors = validate_numeric_ranges(gdf)

    if numeric_errors:
        raise ValueError(
            "Errores numéricos:\n"
            + "\n".join(numeric_errors)
        )

    print("[OK] Variables numéricas válidas")

    # ---------------------------------------------------------
    # COPIA DE TRABAJO
    # ---------------------------------------------------------

    analysis = gdf.copy()

    # ---------------------------------------------------------
    # FACTOR DOMINANTE
    # ---------------------------------------------------------

    print("\n=== FACTOR DOMINANTE ===")

    analysis["dominant_condition"] = analysis.apply(
        classify_condition,
        axis=1,
    )

    condition_counts = (
        analysis["dominant_condition"]
        .value_counts()
        .sort_index()
    )

    print(condition_counts.to_string())

    # ---------------------------------------------------------
    # NIVEL DE INTERVENCIÓN
    # ---------------------------------------------------------

    print("\n=== NIVEL DE INTERVENCIÓN ===")

    analysis["intervention_level"] = analysis.apply(
        classify_intervention,
        axis=1,
    )

    intervention_counts = (
        analysis["intervention_level"]
        .value_counts()
        .reindex(
            ["CRITICA", "ALTA", "MEDIA"],
            fill_value=0,
        )
    )

    print(intervention_counts.to_string())

    # ---------------------------------------------------------
    # DENSIDAD
    # ---------------------------------------------------------

    print("\n=== DENSIDAD ===")

    analysis["density_level"] = analysis.apply(
        classify_density,
        axis=1,
    )

    density_counts = (
        analysis["density_level"]
        .value_counts()
        .reindex(
            ["MUY_ALTA", "ALTA", "MEDIA", "BAJA"],
            fill_value=0,
        )
    )

    print(density_counts.to_string())

    # ---------------------------------------------------------
    # ÍNDICE OPERATIVO
    # ---------------------------------------------------------

    print("\n=== ÍNDICE OPERATIVO ===")

    # Combinación normalizada de:
    # - hotspot_score
    # - densidad
    # - probabilidad media
    #
    # Se mantiene entre 0 y 1.

    density_max = analysis["priority_density"].max()

    if density_max > 0:
        density_norm = (
            analysis["priority_density"]
            / density_max
        )
    else:
        density_norm = 0.0

    analysis["operational_score"] = (
        0.50 * analysis["hotspot_score"]
        + 0.30 * analysis["mean_probability"]
        + 0.20 * density_norm
    )

    analysis["operational_score"] = (
        analysis["operational_score"]
        .clip(0, 1)
    )

    print(
        "Mínimo:",
        f"{analysis['operational_score'].min():.6f}",
    )

    print(
        "Máximo:",
        f"{analysis['operational_score'].max():.6f}",
    )

    print(
        "Media:",
        f"{analysis['operational_score'].mean():.6f}",
    )

    # ---------------------------------------------------------
    # RANKING OPERATIVO
    # ---------------------------------------------------------

    analysis = analysis.sort_values(
        [
            "operational_score",
            "hotspot_score",
            "observations",
        ],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    analysis["operational_rank"] = (
        np.arange(len(analysis)) + 1
    )

    # ---------------------------------------------------------
    # PORCENTAJES
    # ---------------------------------------------------------

    total_observations = analysis["observations"].sum()

    if total_observations > 0:
        analysis["observation_percentage"] = (
            analysis["observations"]
            / total_observations
            * 100
        )
    else:
        analysis["observation_percentage"] = 0.0

    # ---------------------------------------------------------
    # TOP 10
    # ---------------------------------------------------------

    print("\n=== TOP 10 ZONAS OPERATIVAS ===")

    top_columns = [
        "operational_rank",
        "hotspot_rank",
        "observations",
        "mean_probability",
        "hotspot_score",
        "operational_score",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "priority_density",
        "dominant_condition",
        "intervention_level",
        "density_level",
    ]

    print(
        analysis[top_columns]
        .head(10)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # RESUMEN
    # ---------------------------------------------------------

    print("\n=== RESUMEN ===")

    summary_rows = []

    for level in [
        "CRITICA",
        "ALTA",
        "MEDIA",
    ]:

        subset = analysis[
            analysis["intervention_level"] == level
        ]

        summary_rows.append(
            {
                "intervention_level": level,
                "hotspots": len(subset),
                "observations": int(
                    subset["observations"].sum()
                ),
                "area_ha": float(
                    subset["area_ha"].sum()
                ),
                "mean_probability": float(
                    subset["mean_probability"].mean()
                )
                if len(subset)
                else 0.0,
                "mean_hotspot_score": float(
                    subset["hotspot_score"].mean()
                )
                if len(subset)
                else 0.0,
                "mean_operational_score": float(
                    subset["operational_score"].mean()
                )
                if len(subset)
                else 0.0,
                "mean_ndvi": float(
                    subset["mean_ndvi"].mean()
                )
                if len(subset)
                else 0.0,
                "mean_ndbi": float(
                    subset["mean_ndbi"].mean()
                )
                if len(subset)
                else 0.0,
                "mean_lst": float(
                    subset["mean_lst"].mean()
                )
                if len(subset)
                else 0.0,
            }
        )

    summary = pd.DataFrame(summary_rows)

    print(summary.to_string(index=False))

    # ---------------------------------------------------------
    # RESUMEN POR CONDICIÓN
    # ---------------------------------------------------------

    condition_summary = (
        analysis
        .groupby("dominant_condition", as_index=False)
        .agg(
            hotspots=("hotspot_rank", "count"),
            observations=("observations", "sum"),
            area_ha=("area_ha", "sum"),
            mean_probability=("mean_probability", "mean"),
            mean_hotspot_score=("hotspot_score", "mean"),
            mean_operational_score=(
                "operational_score",
                "mean",
            ),
            mean_ndvi=("mean_ndvi", "mean"),
            mean_ndbi=("mean_ndbi", "mean"),
            mean_lst=("mean_lst", "mean"),
        )
        .sort_values(
            "mean_operational_score",
            ascending=False,
        )
    )

    # ---------------------------------------------------------
    # EXPORTAR CSV
    # ---------------------------------------------------------

    print("\n=== EXPORTANDO ===")

    csv_data = analysis.drop(
        columns="geometry"
    )

    csv_data.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    print(f"CSV:\n{OUTPUT_CSV}")

    # ---------------------------------------------------------
    # EXPORTAR GEOPACKAGE
    # ---------------------------------------------------------

    analysis.to_file(
        OUTPUT_GPKG,
        layer="priority_hotspots_analysis",
        driver="GPKG",
    )

    print(f"GeoPackage:\n{OUTPUT_GPKG}")

    # ---------------------------------------------------------
    # EXPORTAR GEOJSON
    # ---------------------------------------------------------

    analysis.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    print(f"GeoJSON:\n{OUTPUT_GEOJSON}")

    # ---------------------------------------------------------
    # EXPORTAR RESUMEN
    # ---------------------------------------------------------

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8",
    )

    print(f"Resumen:\n{OUTPUT_SUMMARY}")

    # ---------------------------------------------------------
    # EXPORTAR RESUMEN DE CONDICIONES
    # ---------------------------------------------------------

    condition_summary_path = (
        OUTPUT_DIR
        / "priority_hotspots_condition_summary.csv"
    )

    condition_summary.to_csv(
        condition_summary_path,
        index=False,
        encoding="utf-8",
    )

    print(
        "Resumen por condición:\n"
        f"{condition_summary_path}"
    )

    # ---------------------------------------------------------
    # VALIDACIÓN FINAL
    # ---------------------------------------------------------

    print("\n=== VALIDACIÓN FINAL ===")

    checks = {
        "Hotspots > 0": len(analysis) > 0,
        "Ranking completo": (
            analysis["operational_rank"].nunique()
            == len(analysis)
        ),
        "Operational score válido": (
            analysis["operational_score"]
            .between(0, 1)
            .all()
        ),
        "Probabilidades válidas": (
            analysis["mean_probability"]
            .between(0, 1)
            .all()
        ),
        "Scores válidos": (
            analysis["hotspot_score"]
            .between(0, 1)
            .all()
        ),
        "Observaciones > 0": (
            analysis["observations"] > 0
        ).all(),
        "Áreas > 0": (
            analysis["area_ha"] > 0
        ).all(),
        "Densidades > 0": (
            analysis["priority_density"] > 0
        ).all(),
        "Geometrías válidas": (
            analysis.geometry.is_valid.all()
        ),
        "Sin geometrías vacías": (
            ~analysis.geometry.is_empty
        ).all(),
        "Sin geometrías nulas": (
            analysis.geometry.notna().all()
        ),
    }

    errors = 0

    for name, result in checks.items():

        if result:
            print(f"[OK] {name}")
        else:
            print(f"[ERROR] {name}")
            errors += 1

    # ---------------------------------------------------------
    # CONSISTENCIA
    # ---------------------------------------------------------

    original_observations = int(
        analysis["observations"].sum()
    )

    print("\n=== CONSISTENCIA ===")

    print(
        "Observaciones agrupadas:",
        f"{original_observations:,}",
    )

    print(
        "Hotspots:",
        f"{len(analysis):,}",
    )

    if original_observations <= 0:
        errors += 1
        print("[ERROR] No existen observaciones agrupadas")
    else:
        print("[OK] Observaciones agrupadas")

    # ---------------------------------------------------------
    # RESULTADO
    # ---------------------------------------------------------

    print("\n" + "=" * 60)

    if errors == 0:
        print("ANÁLISIS DE HOTSPOTS COMPLETADO")
        print("Todos los controles fueron superados.")
    else:
        print("ANÁLISIS COMPLETADO CON ERRORES")
        print(f"Errores detectados: {errors}")

    print("=" * 60)


if __name__ == "__main__":
    main()
    