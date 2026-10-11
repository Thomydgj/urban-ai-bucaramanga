from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_model_dataset.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_priority_model.joblib"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "urban_model_predictions.csv"
)


def main() -> None:
    print("=" * 50)
    print("MODEL PREDICTION")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # ==================================================
    # CARGAR DATASET
    # ==================================================

    df = pd.read_csv(DATASET_PATH)

    print("\n=== DATASET ===")
    print(f"Observaciones: {len(df):,}")

    # ==================================================
    # CARGAR MODELO
    # ==================================================

    artifact = joblib.load(MODEL_PATH)

    model = artifact["model"]
    features = artifact["features"]

    print("\n=== MODELO ===")
    print(type(model).__name__)
    print(f"Variables predictoras: {len(features)}")

    # ==================================================
    # PREPARAR FEATURES
    # ==================================================

    X = df[features]

    # ==================================================
    # PREDICCIÓN
    # ==================================================

    print("\n=== PREDICCIÓN ===")

    predictions = model.predict(X)

    probabilities = model.predict_proba(X)[:, 1]

    df["model_prediction"] = predictions
    df["priority_probability"] = probabilities

    # ==================================================
    # ESTADÍSTICAS
    # ==================================================

    print("\n=== PROBABILIDAD ===")
    print(
        f"Mínimo: {probabilities.min():.6f}"
    )
    print(
        f"Máximo: {probabilities.max():.6f}"
    )
    print(
        f"Media: {probabilities.mean():.6f}"
    )
    print(
        f"Mediana: {pd.Series(probabilities).median():.6f}"
    )

    # ==================================================
    # CLASIFICACIÓN
    # ==================================================

    predicted_high = int(
        (predictions == 1).sum()
    )

    predicted_low = int(
        (predictions == 0).sum()
    )

    print("\n=== CLASIFICACIÓN ===")
    print(
        f"Baja prioridad:  "
        f"{predicted_low:,} "
        f"({predicted_low / len(df) * 100:.2f}%)"
    )

    print(
        f"Alta prioridad:  "
        f"{predicted_high:,} "
        f"({predicted_high / len(df) * 100:.2f}%)"
    )

    # ==================================================
    # COMPARACIÓN CON TARGET ORIGINAL
    # ==================================================

    if "high_priority" in df.columns:
        agreement = (
            df["model_prediction"]
            == df["high_priority"]
        ).mean()

        print("\n=== CONSISTENCIA ===")
        print(
            f"Coincidencia con high_priority: "
            f"{agreement * 100:.4f}%"
        )

    # ==================================================
    # GUARDAR
    # ==================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\n=== RESULTADOS ===")
    print(
        f"Predicciones guardadas en:\n"
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()