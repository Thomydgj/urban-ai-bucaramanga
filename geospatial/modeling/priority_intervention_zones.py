
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
    / "priority_hotspots_analysis.gpkg"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

OUTPUT_GPKG = (
    OUTPUT_DIR
    / "urban_ai_intervention_zones.gpkg"
)

OUTPUT_GEOJSON = (
    OUTPUT_DIR
    / "urban_ai_intervention_zones.geojson"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "urban_ai_intervention_zones.csv"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "urban_ai_intervention_summary.csv"
)


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
    "dominant_condition",
    "intervention_level",
    "density_level",
    "operational_score",
    "operational_rank",
]


def validate_input(gdf):
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


def validate_numeric(gdf):
    probability_columns = [
        "mean_probability",
        "max_probability",
        "hotspot_score",
        "operational_score",
    ]

    for column in probability_columns:

        values = pd.to_numeric(
            gdf[column],
            errors="coerce",
        )

        if values.isna().any():
            raise ValueError(
                f"Valores no numéricos en {column}"
            )

        if not values.between(0, 1).all():
            raise ValueError(
                f"Valores fuera de 0-1 en {column}"
            )

    positive_columns = [
        "observations",
        "area_ha",
        "priority_density",
    ]

    for column in positive_columns:

        values = pd.to_numeric(
            gdf[column],
            errors="coerce",
        )

        if values.isna().any():
            raise ValueError(
                f"Valores inválidos en {column}"
            )

        if not (values > 0).all():
            raise ValueError(
                f"Valores <= 0 encontrados en {column}"
            )


def main():

    print("=" * 60)
    print("PRIORITY INTERVENTION ZONES")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =========================================================
    # CARGA
    # =========================================================

    print("\n=== CARGANDO ANÁLISIS DE HOTSPOTS ===")

    if not INPUT_GPKG.exists():
        raise FileNotFoundError(
            f"No existe:\n{INPUT_GPKG}"
        )

    hotspots = gpd.read_file(
        INPUT_GPKG
    )

    print(
        f"Hotspots cargados: {len(hotspots):,}"
    )

    if hotspots.empty:
        raise ValueError(
            "La capa de hotspots está vacía."
        )

    # =========================================================
    # ESTRUCTURA
    # =========================================================

    print("\n=== ESTRUCTURA ===")

    validate_input(hotspots)

    print(
        "[OK] Todas las columnas requeridas existen"
    )

    # =========================================================
    # CRS
    # =========================================================

    print("\n=== CRS ===")

    print(
        f"CRS original: {hotspots.crs}"
    )

    if hotspots.crs is None:
        raise ValueError(
            "La capa no tiene CRS definido."
        )

    # =========================================================
    # GEOMETRÍAS
    # =========================================================

    print("\n=== GEOMETRÍAS ===")

    invalid = int(
        (~hotspots.geometry.is_valid).sum()
    )

    empty = int(
        hotspots.geometry.is_empty.sum()
    )

    null = int(
        hotspots.geometry.isna().sum()
    )

    print(
        f"Inválidas: {invalid}"
    )

    print(
        f"Vacías:    {empty}"
    )

    print(
        f"Nulas:     {null}"
    )

    if invalid > 0:
        raise ValueError(
            "Existen geometrías inválidas."
        )

    if empty > 0:
        raise ValueError(
            "Existen geometrías vacías."
        )

    if null > 0:
        raise ValueError(
            "Existen geometrías nulas."
        )

    print(
        "[OK] Geometrías válidas"
    )

    # =========================================================
    # VALIDACIÓN NUMÉRICA
    # =========================================================

    print("\n=== VARIABLES NUMÉRICAS ===")

    validate_numeric(
        hotspots
    )

    print(
        "[OK] Variables numéricas válidas"
    )

    # =========================================================
    # CREAR CAPA DE INTERVENCIÓN
    # =========================================================

    zones = hotspots.copy()

    # =========================================================
    # ID DE ZONA
    # =========================================================

    zones["zone_id"] = [
        f"IAZ-{i:04d}"
        for i in range(
            1,
            len(zones) + 1,
        )
    ]

    # =========================================================
    # ORDENAMIENTO OPERATIVO
    # =========================================================

    zones = zones.sort_values(
        [
            "operational_score",
            "hotspot_score",
            "observations",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    zones["operational_rank"] = (
        np.arange(
            1,
            len(zones) + 1,
        )
    )

    # =========================================================
    # PORCENTAJE DE OBSERVACIONES
    # =========================================================

    total_observations = int(
        zones["observations"].sum()
    )

    if total_observations <= 0:
        raise ValueError(
            "No existen observaciones prioritarias."
        )

    zones[
        "observation_percentage"
    ] = (
        zones["observations"]
        / total_observations
        * 100
    )

    # =========================================================
    # PORCENTAJE DE ÁREA
    # =========================================================

    total_area = float(
        zones["area_ha"].sum()
    )

    if total_area <= 0:
        raise ValueError(
            "El área total debe ser mayor que cero."
        )

    zones[
        "area_percentage"
    ] = (
        zones["area_ha"]
        / total_area
        * 100
    )

    # =========================================================
    # CENTROIDES
    # =========================================================

    print("\n=== CENTROIDES ===")

    # Se calcula primero en CRS métrico
    # para evitar el warning de centroides
    # en EPSG:4326.

    metric_crs = "EPSG:32618"

    zones_metric = zones.to_crs(
        metric_crs
    )

    centroids_metric = (
        zones_metric.geometry.centroid
    )

    centroids_wgs84 = (
        gpd.GeoSeries(
            centroids_metric,
            crs=metric_crs,
        )
        .to_crs("EPSG:4326")
    )

    zones["centroid_x"] = (
        centroids_wgs84.x.values
    )

    zones["centroid_y"] = (
        centroids_wgs84.y.values
    )

    print(
        "Centroides calculados correctamente."
    )

    # =========================================================
    # TIPO DE INTERVENCIÓN
    # =========================================================

    print("\n=== TIPO DE INTERVENCIÓN ===")

    def intervention_type(row):

        condition = row[
            "dominant_condition"
        ]

        if condition == "VEGETACION_BAJA":
            return "INFRAESTRUCTURA_VERDE"

        if condition == "SUPERFICIE_CONSTRUIDA":
            return "GESTION_SUPERFICIES"

        if condition == "CALOR_URBANO":
            return "MITIGACION_TERMICA"

        if condition == "MULTIFACTORIAL":
            return "INTERVENCION_INTEGRAL"

        return "DIAGNOSTICO_COMPLEMENTARIO"

    zones[
        "intervention_type"
    ] = zones.apply(
        intervention_type,
        axis=1,
    )

    print(
        zones[
            "intervention_type"
        ]
        .value_counts()
        .to_string()
    )

    # =========================================================
    # PRIORIDAD OPERATIVA
    # =========================================================

    print("\n=== PRIORIDAD OPERATIVA ===")

    # Esta clasificación conserva el nivel
    # previamente definido y agrega una etiqueta
    # operacional explícita.

    zones[
        "priority_class"
    ] = zones[
        "intervention_level"
    ]

    print(
        zones[
            "priority_class"
        ]
        .value_counts()
        .to_string()
    )

    # =========================================================
    # DESCRIPCIÓN DE ZONA
    # =========================================================

    def build_description(row):

        return (
            f"{row['priority_class']} - "
            f"{row['intervention_type']} - "
            f"{row['dominant_condition']}"
        )

    zones[
        "zone_description"
    ] = zones.apply(
        build_description,
        axis=1,
    )

    # =========================================================
    # SELECCIÓN FINAL DE CAMPOS
    # =========================================================

    final_columns = [
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

    zones = zones[
        final_columns
    ]

    # =========================================================
    # TOP 10
    # =========================================================

    print("\n=== TOP 10 ZONAS DE INTERVENCIÓN ===")

    display_columns = [
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

    print(
        zones[
            display_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    # =========================================================
    # RESUMEN POR NIVEL
    # =========================================================

    print("\n=== RESUMEN POR NIVEL ===")

    summary = (
        zones
        .groupby(
            "intervention_level",
            as_index=False,
        )
        .agg(
            zones=(
                "zone_id",
                "count",
            ),
            observations=(
                "observations",
                "sum",
            ),
            area_ha=(
                "area_ha",
                "sum",
            ),
            mean_probability=(
                "mean_probability",
                "mean",
            ),
            mean_hotspot_score=(
                "hotspot_score",
                "mean",
            ),
            mean_operational_score=(
                "operational_score",
                "mean",
            ),
            mean_ndvi=(
                "mean_ndvi",
                "mean",
            ),
            mean_ndbi=(
                "mean_ndbi",
                "mean",
            ),
            mean_lst=(
                "mean_lst",
                "mean",
            ),
        )
    )

    level_order = {
        "CRITICA": 1,
        "ALTA": 2,
        "MEDIA": 3,
    }

    summary[
        "order"
    ] = summary[
        "intervention_level"
    ].map(level_order)

    summary = (
        summary
        .sort_values("order")
        .drop(
            columns="order"
        )
    )

    print(
        summary.to_string(
            index=False
        )
    )

    # =========================================================
    # RESUMEN POR TIPO
    # =========================================================

    print("\n=== RESUMEN POR TIPO ===")

    type_summary = (
        zones
        .groupby(
            "intervention_type",
            as_index=False,
        )
        .agg(
            zones=(
                "zone_id",
                "count",
            ),
            observations=(
                "observations",
                "sum",
            ),
            area_ha=(
                "area_ha",
                "sum",
            ),
            mean_operational_score=(
                "operational_score",
                "mean",
            ),
        )
        .sort_values(
            "mean_operational_score",
            ascending=False,
        )
    )

    print(
        type_summary.to_string(
            index=False
        )
    )

    # =========================================================
    # VALIDACIÓN DE COBERTURA
    # =========================================================

    print("\n=== COBERTURA ===")

    print(
        "Observaciones:",
        f"{total_observations:,}",
    )

    print(
        "Área total:",
        f"{total_area:.2f} ha",
    )

    print(
        "Zonas:",
        f"{len(zones):,}",
    )

    # =========================================================
    # EXPORTAR CSV
    # =========================================================

    print("\n=== EXPORTANDO ===")

    csv_zones = zones.drop(
        columns="geometry"
    )

    csv_zones.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    print(
        f"CSV:\n{OUTPUT_CSV}"
    )

    # =========================================================
    # EXPORTAR GEOPACKAGE
    # =========================================================

    zones.to_file(
        OUTPUT_GPKG,
        layer="intervention_zones",
        driver="GPKG",
    )

    print(
        f"GeoPackage:\n{OUTPUT_GPKG}"
    )

    # =========================================================
    # EXPORTAR GEOJSON
    # =========================================================

    zones.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    print(
        f"GeoJSON:\n{OUTPUT_GEOJSON}"
    )

    # =========================================================
    # EXPORTAR RESUMEN
    # =========================================================

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Resumen:\n{OUTPUT_SUMMARY}"
    )

    # =========================================================
    # VALIDACIÓN FINAL
    # =========================================================

    print("\n=== VALIDACIÓN FINAL ===")

    checks = {
        "Zonas > 0": (
            len(zones) > 0
        ),

        "IDs únicos": (
            zones["zone_id"].is_unique
        ),

        "Ranking único": (
            zones[
                "operational_rank"
            ].is_unique
        ),

        "Ranking completo": (
            set(
                zones[
                    "operational_rank"
                ]
            )
            == set(
                range(
                    1,
                    len(zones) + 1,
                )
            )
        ),

        "Observaciones > 0": (
            zones[
                "observations"
            ] > 0
        ).all(),

        "Área > 0": (
            zones[
                "area_ha"
            ] > 0
        ).all(),

        "Densidad > 0": (
            zones[
                "priority_density"
            ] > 0
        ).all(),

        "Probability válida": (
            zones[
                "mean_probability"
            ].between(0, 1).all()
        ),

        "Hotspot score válido": (
            zones[
                "hotspot_score"
            ].between(0, 1).all()
        ),

        "Operational score válido": (
            zones[
                "operational_score"
            ].between(0, 1).all()
        ),

        "Porcentaje observaciones válido": (
            zones[
                "observation_percentage"
            ].ge(0).all()
            and
            zones[
                "observation_percentage"
            ].le(100).all()
        ),

        "Porcentaje área válido": (
            zones[
                "area_percentage"
            ].ge(0).all()
            and
            zones[
                "area_percentage"
            ].le(100).all()
        ),

        "Centroides válidos": (
            zones[
                [
                    "centroid_x",
                    "centroid_y",
                ]
            ]
            .notna()
            .all()
            .all()
        ),

        "Geometrías válidas": (
            zones.geometry.is_valid.all()
        ),

        "Sin geometrías vacías": (
            (~zones.geometry.is_empty).all()
        ),

        "Sin geometrías nulas": (
            zones.geometry.notna().all()
        ),

        "CRS definido": (
            zones.crs is not None
        ),
    }

    errors = 0

    for name, result in checks.items():

        if result:
            print(
                f"[OK] {name}"
            )
        else:
            print(
                f"[ERROR] {name}"
            )
            errors += 1

    # =========================================================
    # CONSISTENCIA DE OBSERVACIONES
    # =========================================================

    print(
        "\n=== CONSISTENCIA DE OBSERVACIONES ==="
    )

    grouped_observations = int(
        zones[
            "observations"
        ].sum()
    )

    expected_observations = 17_434

    print(
        "Observaciones agrupadas:",
        f"{grouped_observations:,}",
    )

    print(
        "Observaciones esperadas:",
        f"{expected_observations:,}",
    )

    if (
        grouped_observations
        == expected_observations
    ):
        print(
            "[OK] Cobertura completa"
        )
    else:
        print(
            "[ERROR] Diferencia en observaciones"
        )
        errors += 1

    # =========================================================
    # CONSISTENCIA DE ÁREA
    # =========================================================

    print(
        "\n=== CONSISTENCIA DE ÁREA ==="
    )

    if total_area > 0:
        print(
            "[OK] Área total válida"
        )
    else:
        print(
            "[ERROR] Área total inválida"
        )
        errors += 1

    # =========================================================
    # RESULTADO
    # =========================================================

    print("\n" + "=" * 60)

    if errors == 0:

        print(
            "ZONAS DE INTERVENCIÓN VALIDADAS"
        )

        print(
            "Todas las validaciones fueron superadas."
        )

    else:

        print(
            "ZONAS DE INTERVENCIÓN CON ERRORES"
        )

        print(
            f"Errores detectados: {errors}"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
    