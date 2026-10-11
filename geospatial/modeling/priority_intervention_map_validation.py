from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_GPKG = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_ai_intervention_zones.gpkg"
)

MAP_GPKG = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_ai_intervention_map.gpkg"
)

MAP_GEOJSON = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_ai_intervention_map.geojson"
)

OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "priority_intervention_map_validation.csv"
)

SOURCE_LAYER = "intervention_zones"
MAP_LAYER = "intervention_map"


# ============================================================
# COLUMNAS
# ============================================================

REQUIRED_COLUMNS = [
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


# ============================================================
# UTILIDADES
# ============================================================

validation_results = []


def register(name, status, detail=""):
    validation_results.append(
        {
            "validation": name,
            "status": status,
            "detail": detail,
        }
    )

    if status == "OK":
        print(f"[OK] {name}")
    else:
        print(f"[ERROR] {name}")

        if detail:
            print(f"       {detail}")


def validate_file(path, description):
    if path.exists():
        print(f"[OK] {description} existe")
        register(
            f"{description} existe",
            "OK",
            str(path),
        )
        return True

    print(f"[ERROR] {description} no existe")
    register(
        f"{description} existe",
        "ERROR",
        str(path),
    )
    return False


def compare_numeric(
    left,
    right,
    tolerance=1e-9,
):
    return abs(float(left) - float(right)) <= tolerance


# ============================================================
# VALIDACIÓN ESTRUCTURAL
# ============================================================

def validate_structure(source, mapped):

    print("\n=== ESTRUCTURA ===")

    missing_source = [
        col
        for col in REQUIRED_COLUMNS
        if col not in source.columns
    ]

    missing_map = [
        col
        for col in REQUIRED_COLUMNS
        if col not in mapped.columns
    ]

    if missing_source:
        register(
            "Columnas requeridas en fuente",
            "ERROR",
            str(missing_source),
        )
    else:
        register(
            "Columnas requeridas en fuente",
            "OK",
        )

    if missing_map:
        register(
            "Columnas requeridas en mapa",
            "ERROR",
            str(missing_map),
        )
    else:
        register(
            "Columnas requeridas en mapa",
            "OK",
        )

    if missing_source or missing_map:
        raise ValueError(
            "Faltan columnas requeridas."
        )


# ============================================================
# VALIDACIÓN DE CANTIDAD
# ============================================================

def validate_counts(source, mapped):

    print("\n=== CANTIDAD ===")

    source_count = len(source)
    map_count = len(mapped)

    print(
        f"Fuente: {source_count:,}"
    )

    print(
        f"Mapa:   {map_count:,}"
    )

    if source_count == map_count:
        register(
            "Cantidad de zonas coincide",
            "OK",
            f"{source_count:,}",
        )
    else:
        register(
            "Cantidad de zonas coincide",
            "ERROR",
            f"Fuente={source_count}, "
            f"Mapa={map_count}",
        )


# ============================================================
# VALIDACIÓN DE IDS
# ============================================================

def validate_ids(source, mapped):

    print("\n=== IDENTIFICADORES ===")

    source_ids = set(
        source["zone_id"]
        .astype(str)
    )

    map_ids = set(
        mapped["zone_id"]
        .astype(str)
    )

    if source["zone_id"].is_unique:
        register(
            "IDs fuente únicos",
            "OK",
        )
    else:
        register(
            "IDs fuente únicos",
            "ERROR",
        )

    if mapped["zone_id"].is_unique:
        register(
            "IDs mapa únicos",
            "OK",
        )
    else:
        register(
            "IDs mapa únicos",
            "ERROR",
        )

    missing = source_ids - map_ids
    extra = map_ids - source_ids

    if not missing and not extra:
        register(
            "IDs fuente y mapa coinciden",
            "OK",
        )
    else:
        register(
            "IDs fuente y mapa coinciden",
            "ERROR",
            f"Faltantes={len(missing)}, "
            f"extra={len(extra)}",
        )


# ============================================================
# VALIDACIÓN CRS
# ============================================================

def validate_crs(source, mapped):

    print("\n=== CRS ===")

    print(
        f"Fuente: {source.crs}"
    )

    print(
        f"Mapa:   {mapped.crs}"
    )

    if source.crs == mapped.crs:
        register(
            "CRS fuente y mapa coinciden",
            "OK",
            str(source.crs),
        )
    else:
        register(
            "CRS fuente y mapa coinciden",
            "ERROR",
            f"Fuente={source.crs}, "
            f"Mapa={mapped.crs}",
        )

    if mapped.crs is not None:
        register(
            "Mapa tiene CRS definido",
            "OK",
        )
    else:
        register(
            "Mapa tiene CRS definido",
            "ERROR",
        )


# ============================================================
# VALIDACIÓN GEOMETRÍAS
# ============================================================

def validate_geometries(mapped):

    print("\n=== GEOMETRÍAS ===")

    invalid = int(
        (~mapped.geometry.is_valid).sum()
    )

    empty = int(
        mapped.geometry.is_empty.sum()
    )

    null = int(
        mapped.geometry.isna().sum()
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

    register(
        "Geometrías válidas",
        "OK" if invalid == 0 else "ERROR",
        str(invalid),
    )

    register(
        "Sin geometrías vacías",
        "OK" if empty == 0 else "ERROR",
        str(empty),
    )

    register(
        "Sin geometrías nulas",
        "OK" if null == 0 else "ERROR",
        str(null),
    )


# ============================================================
# VALIDACIÓN DE ATRIBUTOS
# ============================================================

def validate_attributes(source, mapped):

    print("\n=== ATRIBUTOS ===")

    numeric_columns = [
        "observations",
        "area_ha",
        "mean_probability",
        "hotspot_score",
        "operational_score",
    ]

    for column in numeric_columns:

        source_values = pd.to_numeric(
            source[column],
            errors="coerce",
        )

        map_values = pd.to_numeric(
            mapped[column],
            errors="coerce",
        )

        source_nulls = int(
            source_values.isna().sum()
        )

        map_nulls = int(
            map_values.isna().sum()
        )

        if source_nulls == 0 and map_nulls == 0:
            register(
                f"{column} sin valores nulos",
                "OK",
            )
        else:
            register(
                f"{column} sin valores nulos",
                "ERROR",
                f"Fuente={source_nulls}, "
                f"Mapa={map_nulls}",
            )

        if (
            source_values.between(0, 1).all()
            and map_values.between(0, 1).all()
        ) and column in [
            "mean_probability",
            "hotspot_score",
            "operational_score",
        ]:
            register(
                f"{column} dentro de [0,1]",
                "OK",
            )

    # Comparación exacta por ID
    source_indexed = (
        source
        .set_index("zone_id")
        .sort_index()
    )

    map_indexed = (
        mapped
        .set_index("zone_id")
        .sort_index()
    )

    for column in [
        "observations",
        "area_ha",
        "mean_probability",
        "hotspot_score",
        "operational_score",
        "dominant_condition",
        "intervention_level",
        "intervention_type",
    ]:

        source_series = source_indexed[column]
        map_series = map_indexed[column]

        if pd.api.types.is_numeric_dtype(
            source_series
        ):

            source_numeric = pd.to_numeric(
                source_series,
                errors="coerce",
            )

            map_numeric = pd.to_numeric(
                map_series,
                errors="coerce",
            )

            difference = (
                source_numeric
                - map_numeric
            ).abs()

            max_difference = float(
                difference.max()
            )

            same = bool(
                (difference <= 1e-9).all()
            )

        else:

            same = bool(
                source_series.astype(str).equals(
                    map_series.astype(str)
                )
            )

            max_difference = 0.0

        register(
            f"Consistencia de {column}",
            "OK" if same else "ERROR",
            f"max_diff={max_difference:.12f}",
        )


# ============================================================
# DISTRIBUCIONES
# ============================================================

def validate_distributions(source, mapped):

    print("\n=== DISTRIBUCIONES ===")

    categorical_columns = [
        "intervention_level",
        "intervention_type",
        "dominant_condition",
    ]

    for column in categorical_columns:

        source_counts = (
            source[column]
            .value_counts()
            .sort_index()
        )

        map_counts = (
            mapped[column]
            .value_counts()
            .sort_index()
        )

        same = source_counts.equals(
            map_counts
        )

        print(f"\n{column}")

        print(
            pd.DataFrame(
                {
                    "source": source_counts,
                    "map": map_counts,
                }
            ).fillna(0)
        )

        register(
            f"Distribución de {column}",
            "OK" if same else "ERROR",
        )


# ============================================================
# OBSERVACIONES Y ÁREA
# ============================================================

def validate_totals(source, mapped):

    print("\n=== TOTALES ===")

    source_observations = int(
        source["observations"].sum()
    )

    map_observations = int(
        mapped["observations"].sum()
    )

    source_area = float(
        source["area_ha"].sum()
    )

    map_area = float(
        mapped["area_ha"].sum()
    )

    print(
        f"Observaciones fuente: {source_observations:,}"
    )

    print(
        f"Observaciones mapa:   {map_observations:,}"
    )

    print(
        f"Área fuente: {source_area:,.2f} ha"
    )

    print(
        f"Área mapa:   {map_area:,.2f} ha"
    )

    register(
        "Observaciones totales coinciden",
        "OK"
        if source_observations == map_observations
        else "ERROR",
    )

    register(
        "Área total coincide",
        "OK"
        if compare_numeric(
            source_area,
            map_area,
        )
        else "ERROR",
        f"diferencia={abs(source_area-map_area):.12f}",
    )


# ============================================================
# GEOJSON
# ============================================================

def validate_geojson(map_count):

    print("\n=== GEOJSON ===")

    if not MAP_GEOJSON.exists():
        register(
            "GeoJSON existe",
            "ERROR",
        )
        return

    register(
        "GeoJSON existe",
        "OK",
    )

    geojson = gpd.read_file(
        MAP_GEOJSON
    )

    print(
        f"GeoJSON: {len(geojson):,}"
    )

    register(
        "Cantidad GeoJSON coincide",
        "OK"
        if len(geojson) == map_count
        else "ERROR",
        f"{len(geojson):,}",
    )

    register(
        "GeoJSON CRS definido",
        "OK"
        if geojson.crs is not None
        else "ERROR",
        str(geojson.crs),
    )

    invalid = int(
        (~geojson.geometry.is_valid).sum()
    )

    register(
        "Geometrías GeoJSON válidas",
        "OK" if invalid == 0 else "ERROR",
        str(invalid),
    )


# ============================================================
# VALIDACIÓN FINAL
# ============================================================

def final_report():

    total = len(validation_results)

    correct = sum(
        result["status"] == "OK"
        for result in validation_results
    )

    errors = total - correct

    print("\n" + "=" * 60)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 60)

    print(
        f"Validaciones: {total}"
    )

    print(
        f"Correctas:    {correct}"
    )

    print(
        f"Errores:      {errors}"
    )

    validation_df = pd.DataFrame(
        validation_results
    )

    validation_df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    print(
        f"\nResultado guardado en:\n{OUTPUT_CSV}"
    )

    if errors == 0:

        print(
            "\n" + "=" * 60
        )

        print(
            "MAPA DE INTERVENCIÓN VALIDADO"
        )

        print(
            "Todos los controles fueron superados."
        )

        print(
            "=" * 60
        )

    else:

        print(
            "\n" + "=" * 60
        )

        print(
            "VALIDACIÓN CON ERRORES"
        )

        print(
            "Revisar las validaciones marcadas como ERROR."
        )

        print(
            "=" * 60
        )

        raise RuntimeError(
            f"La validación terminó con {errors} errores."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRIORITY INTERVENTION MAP VALIDATION")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    print("\n=== ARCHIVOS ===")

    validate_file(
        SOURCE_GPKG,
        "GeoPackage fuente",
    )

    validate_file(
        MAP_GPKG,
        "GeoPackage del mapa",
    )

    validate_file(
        MAP_GEOJSON,
        "GeoJSON del mapa",
    )

    if (
        not SOURCE_GPKG.exists()
        or not MAP_GPKG.exists()
        or not MAP_GEOJSON.exists()
    ):
        raise FileNotFoundError(
            "Faltan archivos necesarios para la validación."
        )

    print("\n=== CARGANDO CAPAS ===")

    source = gpd.read_file(
        SOURCE_GPKG,
        layer=SOURCE_LAYER,
    )

    mapped = gpd.read_file(
        MAP_GPKG,
        layer=MAP_LAYER,
    )

    print(
        f"Fuente: {len(source):,}"
    )

    print(
        f"Mapa:   {len(mapped):,}"
    )

    validate_structure(
        source,
        mapped,
    )

    validate_counts(
        source,
        mapped,
    )

    validate_ids(
        source,
        mapped,
    )

    validate_crs(
        source,
        mapped,
    )

    validate_geometries(
        mapped,
    )

    validate_attributes(
        source,
        mapped,
    )

    validate_distributions(
        source,
        mapped,
    )

    validate_totals(
        source,
        mapped,
    )

    validate_geojson(
        len(mapped)
    )

    final_report()


if __name__ == "__main__":
    main()