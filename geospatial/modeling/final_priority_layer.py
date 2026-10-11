from pathlib import Path

import geopandas as gpd
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "data" / "processed" / "modeling"
ANALYSIS_DIR = BASE_DIR / "data" / "processed" / "analysis"


def classify_priority(probability: float) -> str:
    if probability >= 0.75:
        return "MUY_ALTA"
    elif probability >= 0.50:
        return "ALTA"
    elif probability >= 0.25:
        return "MEDIA"
    else:
        return "BAJA"


def main() -> None:

    print("=" * 60)
    print("FINAL PRIORITY LAYER")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    # =========================================================
    # CARGAR PREDICCIONES
    # =========================================================

    predictions_path = (
        MODEL_DIR / "urban_model_predictions.csv"
    )

    df = pd.read_csv(predictions_path)

    print("\n=== DATASET ===")
    print(f"Observaciones: {len(df):,}")

    # =========================================================
    # VALIDACIÓN
    # =========================================================

    required_columns = [
        "x",
        "y",
        "ndvi",
        "ndbi",
        "lst",
        "priority_score",
        "high_priority",
        "model_prediction",
        "priority_probability",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Faltan columnas: {missing}"
        )

    # =========================================================
    # CLASIFICACIÓN FINAL
    # =========================================================

    df["final_priority"] = df[
        "priority_probability"
    ].apply(classify_priority)

    # Indicador final de prioridad
    df["final_high_priority"] = (
        df["model_prediction"].astype(int)
    )

    # =========================================================
    # GEOMETRÍA
    # =========================================================

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["x"],
            df["y"],
        ),
        crs="EPSG:4326",
    )

    print("\n=== CAPA ESPACIAL ===")
    print(f"Geometrías: {len(gdf):,}")
    print(f"CRS: {gdf.crs}")

    # =========================================================
    # VALIDACIÓN GEOMÉTRICA
    # =========================================================

    valid = gdf.geometry.is_valid
    empty = gdf.geometry.is_empty
    null = gdf.geometry.isna()

    print("\n=== VALIDACIÓN ===")
    print(
        f"Geometrías válidas: {valid.sum():,}"
    )
    print(
        f"Geometrías inválidas: {(~valid).sum():,}"
    )
    print(
        f"Geometrías vacías: {empty.sum():,}"
    )
    print(
        f"Geometrías nulas: {null.sum():,}"
    )

    if (~valid).any():
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

    # =========================================================
    # RESUMEN
    # =========================================================

    print("\n=== NIVELES FINALES ===")

    summary = (
        gdf.groupby("final_priority")
        .agg(
            observations=("final_priority", "size"),
            mean_probability=(
                "priority_probability",
                "mean",
            ),
            mean_ndvi=("ndvi", "mean"),
            mean_ndbi=("ndbi", "mean"),
            mean_lst=("lst", "mean"),
        )
        .sort_values(
            "mean_probability",
            ascending=False,
        )
    )

    summary["percentage"] = (
        summary["observations"]
        / len(gdf)
        * 100
    )

    print(summary)

    # =========================================================
    # EXPORTACIÓN GEOESPACIAL
    # =========================================================

    geopackage_path = (
        MODEL_DIR / "urban_ai_final_priority.gpkg"
    )

    geojson_path = (
        MODEL_DIR / "urban_ai_final_priority.geojson"
    )

    gdf.to_file(
        geopackage_path,
        layer="final_priority",
        driver="GPKG",
    )

    gdf.to_file(
        geojson_path,
        driver="GeoJSON",
    )

    # =========================================================
    # CSV
    # =========================================================

    csv_path = (
        MODEL_DIR / "urban_ai_final_priority.csv"
    )

    export_columns = [
        "x",
        "y",
        "ndvi",
        "ndbi",
        "lst",
        "priority_score",
        "priority_probability",
        "high_priority",
        "model_prediction",
        "final_high_priority",
        "final_priority",
    ]

    df[export_columns].to_csv(
        csv_path,
        index=False,
    )

    # =========================================================
    # RESUMEN FINAL
    # =========================================================

    summary_path = (
        MODEL_DIR / "urban_ai_final_priority_summary.csv"
    )

    summary.reset_index().to_csv(
        summary_path,
        index=False,
    )

    print("\n=== RESULTADOS ===")

    print(
        f"GeoPackage:\n{geopackage_path}"
    )

    print(
        f"\nGeoJSON:\n{geojson_path}"
    )

    print(
        f"\nCSV:\n{csv_path}"
    )

    print(
        f"\nResumen:\n{summary_path}"
    )

    print("\nProceso completado correctamente.")


if __name__ == "__main__":
    main()