from pathlib import Path

import geopandas as gpd
import pandas as pd


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

OUTPUT_CSV = OUTPUT_DIR / "urban_ai_intervention_recommendations.csv"
OUTPUT_GPKG = OUTPUT_DIR / "urban_ai_intervention_recommendations.gpkg"
OUTPUT_GEOJSON = OUTPUT_DIR / "urban_ai_intervention_recommendations.geojson"
OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "urban_ai_intervention_recommendations_summary.csv"
)


# ============================================================
# CONSTANTES
# ============================================================

REQUIRED_COLUMNS = [
    "zone_id",
    "operational_rank",
    "observations",
    "area_ha",
    "mean_probability",
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
    "geometry",
]


# ============================================================
# REGLAS DE RECOMENDACIÓN
# ============================================================

INTERVENTION_RULES = {
    "INTERVENCION_INTEGRAL": {
        "recommendation": (
            "Implementar una intervención integral que combine "
            "mitigación térmica, infraestructura verde y gestión "
            "de superficies urbanas."
        ),
        "objective": (
            "Reducir simultáneamente la presión térmica y la "
            "concentración de superficies construidas."
        ),
        "indicator": (
            "Reducción de LST y aumento de NDVI en el área intervenida."
        ),
        "timeframe": "CORTO_PLAZO",
    },
    "MITIGACION_TERMICA": {
        "recommendation": (
            "Priorizar medidas de mitigación térmica mediante "
            "sombra, arborización, superficies permeables y "
            "reducción de superficies con alta absorción térmica."
        ),
        "objective": (
            "Reducir la temperatura superficial y mejorar el confort térmico."
        ),
        "indicator": (
            "Reducción de LST media posterior a la intervención."
        ),
        "timeframe": "CORTO_PLAZO",
    },
    "INFRAESTRUCTURA_VERDE": {
        "recommendation": (
            "Priorizar infraestructura verde mediante arborización, "
            "conectividad vegetal, recuperación de cobertura y "
            "espacios verdes."
        ),
        "objective": (
            "Incrementar la cobertura vegetal y reducir la exposición térmica."
        ),
        "indicator": (
            "Incremento de NDVI y reducción de LST."
        ),
        "timeframe": "MEDIANO_PLAZO",
    },
    "GESTION_SUPERFICIES": {
        "recommendation": (
            "Gestionar las superficies construidas mediante "
            "materiales de menor absorción térmica, superficies "
            "permeables y estrategias de enfriamiento urbano."
        ),
        "objective": (
            "Reducir la contribución de superficies construidas "
            "a la acumulación de calor."
        ),
        "indicator": (
            "Reducción de NDBI y LST en áreas intervenidas."
        ),
        "timeframe": "MEDIANO_PLAZO",
    },
    "DIAGNOSTICO_COMPLEMENTARIO": {
        "recommendation": (
            "Realizar diagnóstico complementario en campo y "
            "verificación de las condiciones urbanas antes de "
            "definir una intervención específica."
        ),
        "objective": (
            "Precisar las condiciones locales que explican la prioridad."
        ),
        "indicator": (
            "Diagnóstico de campo completado y condición dominante confirmada."
        ),
        "timeframe": "CORTO_PLAZO",
    },
}


# ============================================================
# REGLAS DE CONDICIÓN DOMINANTE
# ============================================================

CONDITION_ACTIONS = {
    "CALOR_URBANO": (
        "Enfocar la intervención en reducción de temperatura "
        "superficial, sombra y cobertura vegetal."
    ),
    "VEGETACION_BAJA": (
        "Priorizar recuperación de cobertura vegetal, arborización "
        "y conectividad de espacios verdes."
    ),
    "SUPERFICIE_CONSTRUIDA": (
        "Priorizar manejo de superficies construidas, materiales "
        "reflectivos/permeables y reducción de absorción térmica."
    ),
    "MULTIFACTORIAL": (
        "Aplicar una estrategia combinada considerando vegetación, "
        "superficies construidas y comportamiento térmico."
    ),
    "MIXTA": (
        "Realizar diagnóstico complementario para determinar la "
        "combinación específica de medidas requerida."
    ),
}


# ============================================================
# FUNCIONES
# ============================================================

def validate_input(gdf):
    """Valida la estructura básica del GeoPackage."""

    print("\n=== VALIDACIÓN DE ENTRADA ===")

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in gdf.columns
    ]

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {missing}"
        )

    print("[OK] Todas las columnas requeridas existen")

    if len(gdf) == 0:
        raise ValueError("El dataset está vacío.")

    print(f"[OK] Zonas: {len(gdf):,}")

    if gdf.crs is None:
        raise ValueError("La capa no tiene CRS definido.")

    print(f"[OK] CRS: {gdf.crs}")

    invalid = (~gdf.geometry.is_valid).sum()
    empty = gdf.geometry.is_empty.sum()
    null = gdf.geometry.isna().sum()

    print(f"Geometrías inválidas: {invalid:,}")
    print(f"Geometrías vacías:    {empty:,}")
    print(f"Geometrías nulas:     {null:,}")

    if invalid > 0:
        raise ValueError("Existen geometrías inválidas.")

    if empty > 0:
        raise ValueError("Existen geometrías vacías.")

    if null > 0:
        raise ValueError("Existen geometrías nulas.")

    print("[OK] Geometrías válidas")


def validate_numeric(gdf):
    """Valida variables numéricas."""

    print("\n=== VALIDACIÓN NUMÉRICA ===")

    numeric_columns = [
        "operational_rank",
        "observations",
        "area_ha",
        "mean_probability",
        "hotspot_score",
        "operational_score",
        "priority_density",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
    ]

    for column in numeric_columns:
        values = pd.to_numeric(
            gdf[column],
            errors="coerce",
        )

        if values.isna().any():
            raise ValueError(
                f"La columna {column} contiene valores no numéricos."
            )

    score_columns = [
        "mean_probability",
        "hotspot_score",
        "operational_score",
    ]

    for column in score_columns:
        if not gdf[column].between(0, 1).all():
            raise ValueError(
                f"La columna {column} contiene valores fuera de [0,1]."
            )

    if (gdf["observations"] <= 0).any():
        raise ValueError(
            "Existen zonas sin observaciones."
        )

    if (gdf["area_ha"] <= 0).any():
        raise ValueError(
            "Existen zonas con área <= 0."
        )

    print("[OK] Variables numéricas válidas")
    print("[OK] Scores dentro del rango [0,1]")


def build_recommendation(row):
    """Construye recomendación según tipo de intervención."""

    intervention_type = str(
        row["intervention_type"]
    ).strip()

    condition = str(
        row["dominant_condition"]
    ).strip()

    rule = INTERVENTION_RULES.get(
        intervention_type,
        INTERVENTION_RULES["DIAGNOSTICO_COMPLEMENTARIO"],
    )

    condition_action = CONDITION_ACTIONS.get(
        condition,
        "Verificar condiciones locales mediante diagnóstico complementario.",
    )

    return (
        f"{rule['recommendation']} "
        f"{condition_action}"
    )


def build_objective(row):
    intervention_type = str(
        row["intervention_type"]
    ).strip()

    rule = INTERVENTION_RULES.get(
        intervention_type,
        INTERVENTION_RULES["DIAGNOSTICO_COMPLEMENTARIO"],
    )

    return rule["objective"]


def build_indicator(row):
    intervention_type = str(
        row["intervention_type"]
    ).strip()

    rule = INTERVENTION_RULES.get(
        intervention_type,
        INTERVENTION_RULES["DIAGNOSTICO_COMPLEMENTARIO"],
    )

    return rule["indicator"]


def build_timeframe(row):
    intervention_type = str(
        row["intervention_type"]
    ).strip()

    intervention_level = str(
        row["intervention_level"]
    ).strip()

    rule = INTERVENTION_RULES.get(
        intervention_type,
        INTERVENTION_RULES["DIAGNOSTICO_COMPLEMENTARIO"],
    )

    timeframe = rule["timeframe"]

    if intervention_level == "CRITICA":
        return "INMEDIATO"

    return timeframe


def build_priority_reason(row):
    """Genera una justificación basada exclusivamente en variables existentes."""

    reasons = []

    probability = float(row["mean_probability"])
    operational_score = float(row["operational_score"])
    density = float(row["priority_density"])
    lst = float(row["mean_lst"])
    ndvi = float(row["mean_ndvi"])
    ndbi = float(row["mean_ndbi"])

    if probability >= 0.90:
        reasons.append("alta probabilidad de prioridad")

    if operational_score >= 0.80:
        reasons.append("alto score operacional")

    if density >= 5:
        reasons.append("alta densidad de observaciones prioritarias")

    if lst >= 40:
        reasons.append("temperatura superficial elevada")

    if ndvi <= 0.15:
        reasons.append("baja cobertura vegetal")

    if ndbi >= 0.15:
        reasons.append("alta señal de superficie construida")

    if not reasons:
        reasons.append(
            "combinación de variables ambientales y espaciales prioritarias"
        )

    return "; ".join(reasons)


def build_action_package(row):
    """Construye un paquete de acciones recomendado."""

    intervention_type = str(
        row["intervention_type"]
    ).strip()

    condition = str(
        row["dominant_condition"]
    ).strip()

    actions = []

    if intervention_type == "INTERVENCION_INTEGRAL":
        actions.extend([
            "Arborización",
            "Superficies de menor absorción térmica",
            "Superficies permeables",
            "Generación de sombra",
            "Monitoreo térmico",
        ])

    elif intervention_type == "MITIGACION_TERMICA":
        actions.extend([
            "Arborización",
            "Generación de sombra",
            "Superficies de menor absorción térmica",
            "Monitoreo térmico",
        ])

    elif intervention_type == "INFRAESTRUCTURA_VERDE":
        actions.extend([
            "Arborización",
            "Recuperación de cobertura vegetal",
            "Conectividad verde",
            "Monitoreo de NDVI",
        ])

    elif intervention_type == "GESTION_SUPERFICIES":
        actions.extend([
            "Superficies permeables",
            "Materiales de menor absorción térmica",
            "Gestión de superficies construidas",
            "Monitoreo de NDBI y LST",
        ])

    else:
        actions.extend([
            "Visita de campo",
            "Verificación de cobertura vegetal",
            "Verificación de superficies construidas",
            "Medición o validación térmica",
        ])

    if condition == "VEGETACION_BAJA":
        actions.append("Priorización de cobertura vegetal")

    elif condition == "SUPERFICIE_CONSTRUIDA":
        actions.append("Priorización de superficies urbanas")

    elif condition == "CALOR_URBANO":
        actions.append("Priorización de mitigación térmica")

    elif condition == "MULTIFACTORIAL":
        actions.append("Coordinación multisectorial")

    return " | ".join(dict.fromkeys(actions))


def build_outputs(gdf):
    """Construye todos los campos derivados."""

    print("\n=== GENERANDO RECOMENDACIONES ===")

    gdf["recommendation"] = gdf.apply(
        build_recommendation,
        axis=1,
    )

    gdf["intervention_objective"] = gdf.apply(
        build_objective,
        axis=1,
    )

    gdf["monitoring_indicator"] = gdf.apply(
        build_indicator,
        axis=1,
    )

    gdf["priority_timeframe"] = gdf.apply(
        build_timeframe,
        axis=1,
    )

    gdf["priority_reason"] = gdf.apply(
        build_priority_reason,
        axis=1,
    )

    gdf["action_package"] = gdf.apply(
        build_action_package,
        axis=1,
    )

    print("[OK] Recomendaciones generadas")
    print("[OK] Objetivos generados")
    print("[OK] Indicadores generados")
    print("[OK] Paquetes de acción generados")


def validate_outputs(gdf):
    """Validación final."""

    print("\n=== VALIDACIÓN FINAL ===")

    required_outputs = [
        "recommendation",
        "intervention_objective",
        "monitoring_indicator",
        "priority_timeframe",
        "priority_reason",
        "action_package",
    ]

    for column in required_outputs:
        if column not in gdf.columns:
            raise ValueError(
                f"Falta columna generada: {column}"
            )

        if gdf[column].isna().any():
            raise ValueError(
                f"La columna {column} contiene valores nulos."
            )

        if (gdf[column].astype(str).str.strip() == "").any():
            raise ValueError(
                f"La columna {column} contiene valores vacíos."
            )

        print(f"[OK] {column}")

    if len(gdf) != 224:
        print(
            f"[AVISO] Número de zonas diferente de 224: "
            f"{len(gdf)}"
        )
    else:
        print("[OK] 224 zonas procesadas")

    if gdf["zone_id"].duplicated().any():
        raise ValueError("Existen zone_id duplicados.")

    print("[OK] IDs únicos")

    valid_timeframes = {
        "INMEDIATO",
        "CORTO_PLAZO",
        "MEDIANO_PLAZO",
    }

    invalid_timeframes = set(
        gdf["priority_timeframe"]
    ) - valid_timeframes

    if invalid_timeframes:
        raise ValueError(
            f"Plazos inválidos: {invalid_timeframes}"
        )

    print("[OK] Plazos de intervención válidos")


def export_results(gdf):
    """Exporta CSV, GeoPackage, GeoJSON y resumen."""

    print("\n=== EXPORTANDO ===")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # CSV sin geometría
    csv_df = pd.DataFrame(
        gdf.drop(columns="geometry")
    )

    csv_df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    # GeoPackage
    gdf.to_file(
        OUTPUT_GPKG,
        layer="intervention_recommendations",
        driver="GPKG",
    )

    # GeoJSON
    gdf.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    # Resumen
    summary = (
        gdf.groupby(
            [
                "intervention_level",
                "intervention_type",
                "dominant_condition",
            ],
            dropna=False,
        )
        .agg(
            zones=("zone_id", "count"),
            observations=("observations", "sum"),
            area_ha=("area_ha", "sum"),
            mean_probability=("mean_probability", "mean"),
            mean_hotspot_score=("hotspot_score", "mean"),
            mean_operational_score=("operational_score", "mean"),
            mean_ndvi=("mean_ndvi", "mean"),
            mean_ndbi=("mean_ndbi", "mean"),
            mean_lst=("mean_lst", "mean"),
        )
        .reset_index()
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"CSV:\n{OUTPUT_CSV}")
    print(f"GeoPackage:\n{OUTPUT_GPKG}")
    print(f"GeoJSON:\n{OUTPUT_GEOJSON}")
    print(f"Resumen:\n{OUTPUT_SUMMARY}")


def print_summary(gdf):
    """Muestra resumen ejecutivo."""

    print("\n============================================================")
    print("RESUMEN DE RECOMENDACIONES")
    print("============================================================")

    print(
        f"Zonas procesadas: {len(gdf):,}"
    )

    print(
        f"Observaciones prioritarias: "
        f"{gdf['observations'].sum():,}"
    )

    print(
        f"Área total: "
        f"{gdf['area_ha'].sum():,.2f} ha"
    )

    print(
        f"Probability media ponderada: "
        f"{gdf['mean_probability'].mean():.6f}"
    )

    print(
        f"Operational score medio: "
        f"{gdf['operational_score'].mean():.6f}"
    )

    print("\n=== PLAZO ===")

    print(
        gdf["priority_timeframe"]
        .value_counts()
        .to_string()
    )

    print("\n=== TIPO DE INTERVENCIÓN ===")

    print(
        gdf["intervention_type"]
        .value_counts()
        .to_string()
    )

    print("\n=== TOP 10 RECOMENDACIONES ===")

    columns = [
        "zone_id",
        "operational_rank",
        "intervention_level",
        "intervention_type",
        "dominant_condition",
        "operational_score",
        "priority_timeframe",
    ]

    print(
        gdf.sort_values(
            "operational_rank"
        )[columns]
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRIORITY INTERVENTION RECOMMENDATIONS")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    print("\n=== ARCHIVO DE ENTRADA ===")
    print(f"GeoPackage: {INPUT_GPKG}")

    if not INPUT_GPKG.exists():
        raise FileNotFoundError(
            f"No existe el archivo:\n{INPUT_GPKG}"
        )

    print("\n=== CARGANDO DATOS ===")

    gdf = gpd.read_file(
        INPUT_GPKG,
        layer="intervention_zones",
    )

    print(
        f"Zonas cargadas: {len(gdf):,}"
    )

    validate_input(gdf)
    validate_numeric(gdf)
    build_outputs(gdf)
    validate_outputs(gdf)
    export_results(gdf)
    print_summary(gdf)

    print("\n============================================================")
    print("RECOMENDACIONES DE INTERVENCIÓN GENERADAS")
    print("Todos los controles fueron superados.")
    print("============================================================")


if __name__ == "__main__":
    main()