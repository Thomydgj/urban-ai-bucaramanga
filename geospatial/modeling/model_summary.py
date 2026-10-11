from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "data" / "processed" / "modeling"
ANALYSIS_DIR = BASE_DIR / "data" / "processed" / "analysis"


def main() -> None:
    print("=" * 50)
    print("MODEL SUMMARY")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # =========================================================
    # CARGAR RESULTADOS
    # =========================================================

    evaluation_path = MODEL_DIR / "model_evaluation.csv"
    raster_validation_path = MODEL_DIR / "urban_raster_validation.csv"
    predictions_path = MODEL_DIR / "urban_model_predictions.csv"

    evaluation = pd.read_csv(evaluation_path)
    raster_validation = pd.read_csv(raster_validation_path)
    predictions = pd.read_csv(predictions_path)

    print("\n=== ARCHIVOS ===")
    print(f"Evaluación: {evaluation_path}")
    print(f"Validación raster: {raster_validation_path}")
    print(f"Predicciones: {predictions_path}")

    # =========================================================
    # DATASET
    # =========================================================

    print("\n=== DATASET ===")
    print(f"Observaciones: {len(predictions):,}")

    # =========================================================
    # MÉTRICAS DEL MODELO
    # =========================================================

    print("\n=== MÉTRICAS DEL MODELO ===")

    if "metric" in evaluation.columns and "value" in evaluation.columns:
        metrics = dict(
            zip(
                evaluation["metric"],
                evaluation["value"],
            )
        )

        for name, value in metrics.items():
            print(f"{name}: {value:.6f}")

    else:
        print(evaluation)

    # =========================================================
    # VALIDACIÓN ESPACIAL
    # =========================================================

    print("\n=== VALIDACIÓN ESPACIAL ===")

    if "metric" in raster_validation.columns and "value" in raster_validation.columns:
        spatial_metrics = dict(
            zip(
                raster_validation["metric"],
                raster_validation["value"],
            )
        )

        for name, value in spatial_metrics.items():
            print(f"{name}: {value:.6f}")

    else:
        print(raster_validation)

    # =========================================================
    # CLASIFICACIÓN
    # =========================================================

    print("\n=== CLASIFICACIÓN ===")

    if "high_priority" in predictions.columns:
        original_high = int(
            predictions["high_priority"].sum()
        )

        print(
            f"Alta prioridad original: "
            f"{original_high:,}"
        )

    if "model_prediction" in predictions.columns:
        predicted_high = int(
            predictions["model_prediction"].sum()
        )

        print(
            f"Alta prioridad predicha: "
            f"{predicted_high:,}"
        )

    if "model_prediction" in predictions.columns:
        agreement = (
            predictions["high_priority"]
            == predictions["model_prediction"]
        ).mean()

        print(
            f"Coincidencia: "
            f"{agreement:.6%}"
        )

    # =========================================================
    # PROBABILIDAD
    # =========================================================

    print("\n=== PROBABILIDAD ===")

    if "priority_probability" in predictions.columns:
        probability = predictions[
            "priority_probability"
        ]

        print(
            f"Mínimo: {probability.min():.6f}"
        )

        print(
            f"Máximo: {probability.max():.6f}"
        )

        print(
            f"Media: {probability.mean():.6f}"
        )

        print(
            f"Mediana: {probability.median():.6f}"
        )

    # =========================================================
    # CONSOLIDACIÓN
    # =========================================================

    summary = {
        "observations": len(predictions),
        "original_high_priority": int(
            predictions["high_priority"].sum()
        ),
        "predicted_high_priority": int(
            predictions["model_prediction"].sum()
        ),
        "classification_agreement": (
            predictions["high_priority"]
            == predictions["model_prediction"]
        ).mean(),
        "mean_priority_probability": (
            predictions["priority_probability"].mean()
        ),
    }

    summary_df = pd.DataFrame(
        [summary]
    )

    output_path = (
        MODEL_DIR / "model_final_summary.csv"
    )

    summary_df.to_csv(
        output_path,
        index=False,
    )

    print("\n=== RESULTADOS ===")
    print(
        f"Resumen guardado en:\n{output_path}"
    )

    print("\nProceso completado correctamente.")


if __name__ == "__main__":
    main()