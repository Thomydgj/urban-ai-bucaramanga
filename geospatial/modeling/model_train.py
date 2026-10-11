from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_model_dataset.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

MODEL_PATH = MODEL_DIR / "urban_priority_model.joblib"


FEATURES = [
    "x",
    "y",
    "ndvi",
    "ndbi",
    "lst",
    "vegetation_signal",
    "built_signal",
]

TARGET = "high_priority"


def main() -> None:
    print("=" * 50)
    print("MODEL TRAIN")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # ==================================================
    # CARGA DEL DATASET
    # ==================================================

    df = pd.read_csv(DATASET_PATH)

    print("\n=== DATASET ===")
    print(f"Observaciones: {len(df):,}")
    print(f"Variables: {len(df.columns)}")

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    missing_features = [
        column
        for column in FEATURES
        if column not in df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Faltan variables predictoras: {missing_features}"
        )

    if TARGET not in df.columns:
        raise ValueError(
            f"No existe la variable target: {TARGET}"
        )

    if df[FEATURES + [TARGET]].isnull().any().any():
        raise ValueError(
            "El dataset contiene valores nulos."
        )

    # ==================================================
    # X / Y
    # ==================================================

    X = df[FEATURES]
    y = df[TARGET].astype(int)

    print("\n=== TARGET ===")
    print(y.value_counts().sort_index())

    # ==================================================
    # TRAIN / TEST
    # ==================================================

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print("\n=== TRAIN / TEST ===")
    print(f"Train: {len(X_train):,}")
    print(f"Test:  {len(X_test):,}")

    print("\nDistribución TRAIN:")
    print(y_train.value_counts(normalize=True).sort_index())

    print("\nDistribución TEST:")
    print(y_test.value_counts(normalize=True).sort_index())

    # ==================================================
    # RANDOM FOREST
    # ==================================================

    print("\n=== RANDOM FOREST ===")

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    print("Entrenando modelo...")

    model.fit(X_train, y_train)

    print("Entrenamiento completado.")

    # ==================================================
    # IMPORTANCIA DE VARIABLES
    # ==================================================

    importance = pd.Series(
        model.feature_importances_,
        index=FEATURES,
    ).sort_values(ascending=False)

    print("\n=== IMPORTANCIA DE VARIABLES ===")

    for feature, value in importance.items():
        print(f"{feature:20s}: {value:.6f}")

    # ==================================================
    # GUARDAR MODELO
    # ==================================================

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "model": model,
        "features": FEATURES,
        "target": TARGET,
        "random_state": 42,
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
    )

    print("\n=== RESULTADOS ===")
    print(f"Modelo guardado en:")
    print(MODEL_PATH)


if __name__ == "__main__":
    main()