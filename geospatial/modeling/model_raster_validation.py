
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_model_dataset.csv"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_model_predictions.csv"
)

PROBABILITY_RASTER = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_priority_probability.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "urban_raster_validation.csv"
)


def main() -> None:

    print("=" * 50)
    print("MODEL RASTER VALIDATION")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # =========================================================
    # LOAD DATA
    # =========================================================

    df = pd.read_csv(DATASET_PATH)
    predictions = pd.read_csv(PREDICTIONS_PATH)

    print()
    print("=== DATASETS ===")
    print(f"Dataset original: {len(df):,}")
    print(f"Predicciones:     {len(predictions):,}")

    if len(df) != len(predictions):
        raise ValueError(
            "El dataset original y el dataset de predicciones "
            "no tienen la misma cantidad de observaciones."
        )

    # =========================================================
    # VALIDATE COLUMNS
    # =========================================================

    required_dataset = [
        "x",
        "y",
        "high_priority",
    ]

    required_predictions = [
        "x",
        "y",
        "priority_probability",
        "model_prediction",
    ]

    for column in required_dataset:
        if column not in df.columns:
            raise ValueError(
                f"Falta columna en dataset: {column}"
            )

    for column in required_predictions:
        if column not in predictions.columns:
            raise ValueError(
                f"Falta columna en predicciones: {column}"
            )

    # =========================================================
    # MERGE BY COORDINATES
    # =========================================================

    print()
    print("=== UNIFICACIÓN ESPACIAL ===")

    validation = df[
        ["x", "y", "high_priority"]
    ].merge(
        predictions[
            [
                "x",
                "y",
                "priority_probability",
                "model_prediction",
            ]
        ],
        on=["x", "y"],
        how="inner",
        validate="one_to_one",
    )

    print(
        f"Observaciones coincidentes: "
        f"{len(validation):,}"
    )

    if len(validation) != len(df):
        raise ValueError(
            "No todas las observaciones pudieron "
            "ser emparejadas espacialmente."
        )

    # =========================================================
    # RASTER VALIDATION
    # =========================================================

    print()
    print("=== RASTER ===")

    with rasterio.open(PROBABILITY_RASTER) as src:

        probability = src.read(1)

        raster_crs = src.crs
        raster_shape = probability.shape
        raster_nodata = src.nodata

    valid_raster = np.isfinite(probability)

    print(
        f"Dimensiones: {raster_shape[0]} x "
        f"{raster_shape[1]}"
    )

    print(f"CRS: {raster_crs}")

    print(
        f"Píxeles válidos: "
        f"{valid_raster.sum():,}"
    )

    print(
        f"Píxeles NoData: "
        f"{(~valid_raster).sum():,}"
    )

    # =========================================================
    # CLASS COMPARISON
    # =========================================================

    actual = validation["high_priority"].astype(int)
    predicted = validation["model_prediction"].astype(int)

    tp = int(
        ((actual == 1) & (predicted == 1)).sum()
    )

    tn = int(
        ((actual == 0) & (predicted == 0)).sum()
    )

    fp = int(
        ((actual == 0) & (predicted == 1)).sum()
    )

    fn = int(
        ((actual == 1) & (predicted == 0)).sum()
    )

    total = len(validation)

    accuracy = (
        (tp + tn) / total
        if total > 0
        else 0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    print()
    print("=== MATRIZ ESPACIAL ===")

    print(f"True Positive:  {tp:,}")
    print(f"True Negative:  {tn:,}")
    print(f"False Positive: {fp:,}")
    print(f"False Negative: {fn:,}")

    print()
    print("=== MÉTRICAS ===")

    print(f"Accuracy:  {accuracy:.6f}")
    print(f"Precision: {precision:.6f}")
    print(f"Recall:    {recall:.6f}")
    print(f"F1:        {f1:.6f}")

    # =========================================================
    # ORIGINAL VS PREDICTED
    # =========================================================

    original_high = int(
        (actual == 1).sum()
    )

    predicted_high = int(
        (predicted == 1).sum()
    )

    disagreement = int(
        (actual != predicted).sum()
    )

    print()
    print("=== COMPARACIÓN ===")

    print(
        f"Alta prioridad original: "
        f"{original_high:,}"
    )

    print(
        f"Alta prioridad predicha: "
        f"{predicted_high:,}"
    )

    print(
        f"Discrepancias: "
        f"{disagreement:,}"
    )

    print(
        f"Coincidencia: "
        f"{(1 - disagreement / total) * 100:.4f}%"
    )

    # =========================================================
    # PROBABILITY STATISTICS
    # =========================================================

    probability_values = (
        validation["priority_probability"]
        .to_numpy()
    )

    print()
    print("=== PROBABILIDAD ===")

    print(
        f"Mínimo: "
        f"{probability_values.min():.6f}"
    )

    print(
        f"Máximo: "
        f"{probability_values.max():.6f}"
    )

    print(
        f"Media: "
        f"{probability_values.mean():.6f}"
    )

    print(
        f"Mediana: "
        f"{np.median(probability_values):.6f}"
    )

    # =========================================================
    # ERROR SPATIAL DATASET
    # =========================================================

    validation["error_type"] = "CORRECT"

    validation.loc[
        (actual == 0) & (predicted == 1),
        "error_type",
    ] = "FALSE_POSITIVE"

    validation.loc[
        (actual == 1) & (predicted == 0),
        "error_type",
    ] = "FALSE_NEGATIVE"

    validation.loc[
        (actual == 1) & (predicted == 1),
        "error_type",
    ] = "TRUE_POSITIVE"

    validation.loc[
        (actual == 0) & (predicted == 0),
        "error_type",
    ] = "TRUE_NEGATIVE"

    # =========================================================
    # SAVE RESULTS
    # =========================================================

    result = pd.DataFrame(
        {
            "metric": [
                "total_observations",
                "true_positive",
                "true_negative",
                "false_positive",
                "false_negative",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "original_high_priority",
                "predicted_high_priority",
                "disagreement",
                "agreement_percentage",
                "raster_valid_pixels",
                "raster_nodata_pixels",
            ],
            "value": [
                total,
                tp,
                tn,
                fp,
                fn,
                accuracy,
                precision,
                recall,
                f1,
                original_high,
                predicted_high,
                disagreement,
                (1 - disagreement / total) * 100,
                int(valid_raster.sum()),
                int((~valid_raster).sum()),
            ],
        }
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print()
    print("=== RESULTADOS ===")
    print(
        f"Validación guardada en:\n"
        f"{OUTPUT_CSV}"
    )

    print()
    print("Proceso completado correctamente.")


if __name__ == "__main__":
    main()
