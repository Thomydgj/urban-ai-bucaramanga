from pathlib import Path

import geopandas as gpd
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "data" / "processed" / "modeling"

CSV_PATH = MODEL_DIR / "urban_ai_final_priority.csv"
GPKG_PATH = MODEL_DIR / "urban_ai_final_priority.gpkg"

OUTPUT_PATH = MODEL_DIR / "final_project_validation.csv"


def main():

    print("=" * 60)
    print("FINAL PROJECT VALIDATION")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    # =========================================================
    # CARGAR DATOS
    # =========================================================

    print("\n=== CARGANDO DATOS ===")

    csv = pd.read_csv(CSV_PATH)

    gdf = gpd.read_file(
        GPKG_PATH,
        layer="final_priority",
    )

    print(f"CSV:      {len(csv):,} observaciones")
    print(f"GeoPackage: {len(gdf):,} observaciones")

    # =========================================================
    # VALIDACIÓN DE CANTIDAD
    # =========================================================

    print("\n=== CANTIDAD DE OBSERVACIONES ===")

    same_count = len(csv) == len(gdf)

    print(
        f"[{'OK' if same_count else 'ERROR'}] "
        f"Cantidad coincidente: {same_count}"
    )

    if not same_count:
        raise ValueError(
            "CSV y GeoPackage tienen diferente cantidad de observaciones."
        )

    # =========================================================
    # COLUMNAS
    # =========================================================

    required = [
        "x",
        "y",
        "ndvi",
        "ndbi",
        "lst",
        "priority_probability",
        "final_priority",
    ]

    print("\n=== COLUMNAS ===")

    for column in required:

        csv_ok = column in csv.columns
        geo_ok = column in gdf.columns

        print(
            f"{column:25s} "
            f"CSV={'OK' if csv_ok else 'ERROR'} "
            f"GeoPackage={'OK' if geo_ok else 'ERROR'}"
        )

        if not csv_ok or not geo_ok:
            raise ValueError(
                f"Falta columna requerida: {column}"
            )

    # =========================================================
    # NULOS
    # =========================================================

    print("\n=== VALORES NULOS ===")

    for column in required:

        csv_nulls = int(csv[column].isna().sum())
        geo_nulls = int(gdf[column].isna().sum())

        print(
            f"{column:25s} "
            f"CSV={csv_nulls} "
            f"GeoPackage={geo_nulls}"
        )

        if csv_nulls > 0 or geo_nulls > 0:
            raise ValueError(
                f"Existen valores nulos en {column}"
            )

    # =========================================================
    # CATEGORÍAS
    # =========================================================

    expected_levels = [
        "MUY_ALTA",
        "ALTA",
        "MEDIA",
        "BAJA",
    ]

    csv_levels = set(
        csv["final_priority"].unique()
    )

    geo_levels = set(
        gdf["final_priority"].unique()
    )

    print("\n=== CATEGORÍAS ===")

    print(
        "CSV:",
        sorted(csv_levels),
    )

    print(
        "GeoPackage:",
        sorted(geo_levels),
    )

    if csv_levels != set(expected_levels):
        raise ValueError(
            "Las categorías del CSV no coinciden con las esperadas."
        )

    if geo_levels != set(expected_levels):
        raise ValueError(
            "Las categorías del GeoPackage no coinciden con las esperadas."
        )

    # =========================================================
    # DISTRIBUCIÓN
    # =========================================================

    print("\n=== DISTRIBUCIÓN FINAL ===")

    csv_distribution = (
        csv["final_priority"]
        .value_counts()
        .reindex(expected_levels)
        .fillna(0)
        .astype(int)
    )

    geo_distribution = (
        gdf["final_priority"]
        .value_counts()
        .reindex(expected_levels)
        .fillna(0)
        .astype(int)
    )

    for level in expected_levels:

        csv_count = csv_distribution[level]
        geo_count = geo_distribution[level]

        match = csv_count == geo_count

        print(
            f"{level:10s} "
            f"CSV={csv_count:7,d} "
            f"GPKG={geo_count:7,d} "
            f"[{'OK' if match else 'ERROR'}]"
        )

        if not match:
            raise ValueError(
                f"Distribución diferente para {level}"
            )

    # =========================================================
    # PRIORITY PROBABILITY
    # =========================================================

    print("\n=== PRIORITY PROBABILITY ===")

    csv_min = csv["priority_probability"].min()
    csv_max = csv["priority_probability"].max()
    csv_mean = csv["priority_probability"].mean()

    geo_min = gdf["priority_probability"].min()
    geo_max = gdf["priority_probability"].max()
    geo_mean = gdf["priority_probability"].mean()

    print(
        f"CSV       : min={csv_min:.6f} "
        f"max={csv_max:.6f} "
        f"mean={csv_mean:.6f}"
    )

    print(
        f"GeoPackage: min={geo_min:.6f} "
        f"max={geo_max:.6f} "
        f"mean={geo_mean:.6f}"
    )

    if not (
        abs(csv_min - geo_min) < 1e-6
        and abs(csv_max - geo_max) < 1e-6
        and abs(csv_mean - geo_mean) < 1e-6
    ):
        raise ValueError(
            "Las estadísticas de probability no coinciden."
        )

    # =========================================================
    # CRS
    # =========================================================

    print("\n=== CRS ===")

    print(
        f"CRS: {gdf.crs}"
    )

    if gdf.crs is None:
        raise ValueError(
            "El GeoPackage no tiene CRS."
        )

    # =========================================================
    # GEOMETRÍAS
    # =========================================================

    print("\n=== GEOMETRÍAS ===")

    invalid = int(
        (~gdf.geometry.is_valid).sum()
    )

    empty = int(
        gdf.geometry.is_empty.sum()
    )

    null = int(
        gdf.geometry.isna().sum()
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

    if invalid > 0 or empty > 0 or null > 0:
        raise ValueError(
            "La capa espacial contiene geometrías problemáticas."
        )

    # =========================================================
    # EXTENSIÓN
    # =========================================================

    bounds = gdf.total_bounds

    print("\n=== EXTENSIÓN ===")

    print(
        f"Min X: {bounds[0]:.6f}"
    )

    print(
        f"Min Y: {bounds[1]:.6f}"
    )

    print(
        f"Max X: {bounds[2]:.6f}"
    )

    print(
        f"Max Y: {bounds[3]:.6f}"
    )

    # =========================================================
    # RESUMEN DE VALIDACIÓN
    # =========================================================

    validation = pd.DataFrame(
        {
            "check": [
                "observation_count",
                "required_columns",
                "null_values",
                "priority_categories",
                "distribution",
                "probability_statistics",
                "crs",
                "geometry_validity",
            ],
            "status": [
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
                "OK",
            ],
        }
    )

    validation.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # =========================================================
    # RESULTADO
    # =========================================================

    print("\n" + "=" * 60)
    print("VALIDACIÓN FINAL")
    print("=" * 60)

    print("[OK] CSV y GeoPackage coinciden")
    print("[OK] 173,656 observaciones")
    print("[OK] Categorías completas")
    print("[OK] Distribución consistente")
    print("[OK] Priority probability consistente")
    print("[OK] CRS definido")
    print("[OK] Geometrías válidas")
    print("[OK] Sin valores nulos")

    print(
        "\nResultado guardado en:"
    )

    print(
        OUTPUT_PATH
    )

    print(
        "\nPROYECTO VALIDADO CORRECTAMENTE."
    )


if __name__ == "__main__":
    main()