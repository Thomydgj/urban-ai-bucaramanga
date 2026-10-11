from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FEATURES = Path(
    "data/processed/urban_features.csv"
)

INPUT_PRIORITY = Path(
    "data/processed/analysis/urban_priority.csv"
)

OUTPUT_DIR = Path(
    "data/processed/modeling"
)

OUTPUT_FILE = OUTPUT_DIR / "urban_model_dataset.csv"


FEATURE_COLUMNS = [
    "x",
    "y",
    "ndvi",
    "ndbi",
    "lst",
    "vegetation_signal",
    "built_signal",
]


def main() -> None:
    print("=" * 50)
    print("MODEL DATASET")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==================================================
    # CARGA
    # ==================================================

    features = pd.read_csv(INPUT_FEATURES)
    priority = pd.read_csv(INPUT_PRIORITY)

    print("\n=== DATASETS ===")

    print(
        f"Features: {len(features):,} observaciones"
    )

    print(
        f"Priority: {len(priority):,} observaciones"
    )

    # ==================================================
    # VALIDACIÓN DE COLUMNAS
    # ==================================================

    required_features = [
        "x",
        "y",
        "ndvi",
        "ndbi",
        "lst",
        "vegetation_signal",
        "built_signal",
    ]

    missing_features = [
        column
        for column in required_features
        if column not in features.columns
    ]

    if missing_features:
        raise ValueError(
            f"Faltan columnas en features: "
            f"{missing_features}"
        )

    if "priority_score" not in priority.columns:
        raise ValueError(
            "No existe la columna priority_score."
        )

    # ==================================================
    # CONSTRUCCIÓN DEL TARGET
    # ==================================================

    threshold = priority["priority_score"].quantile(
        0.90
    )

    priority_target = priority[
        ["x", "y", "priority_score"]
    ].copy()

    priority_target["high_priority"] = (
        priority_target["priority_score"]
        >= threshold
    ).astype(int)

    # ==================================================
    # UNIÓN
    # ==================================================

    df = features.merge(
        priority_target,
        on=["x", "y"],
        how="inner",
        validate="one_to_one",
    )

    print("\n=== DATASET UNIFICADO ===")

    print(
        f"Observaciones: {len(df):,}"
    )

    # ==================================================
    # VALIDACIÓN DE DATOS
    # ==================================================

    print("\n=== VALORES NULOS ===")

    nulls = df[
        FEATURE_COLUMNS
        + ["priority_score", "high_priority"]
    ].isna().sum()

    print(nulls)

    # ==================================================
    # INFINITOS
    # ==================================================

    numeric_columns = (
        FEATURE_COLUMNS
        + ["priority_score"]
    )

    infinite_count = np.isinf(
        df[numeric_columns]
    ).sum().sum()

    print(
        f"\nValores infinitos: {infinite_count}"
    )

    # ==================================================
    # DUPLICADOS
    # ==================================================

    duplicates = df.duplicated(
        subset=["x", "y"]
    ).sum()

    print(
        f"Duplicados espaciales: {duplicates}"
    )

    # ==================================================
    # ELIMINAR FILAS PROBLEMÁTICAS
    # ==================================================

    before = len(df)

    df = df.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    df = df.dropna(
        subset=FEATURE_COLUMNS
    ).copy()

    removed = before - len(df)

    print(
        f"Observaciones eliminadas: {removed}"
    )

    # ==================================================
    # VALIDACIÓN DEL TARGET
    # ==================================================

    print("\n=== TARGET ===")

    print(
        f"Umbral P90: {threshold:.6f}"
    )

    class_counts = (
        df["high_priority"]
        .value_counts()
        .sort_index()
    )

    class_percentages = (
        df["high_priority"]
        .value_counts(
            normalize=True
        )
        .sort_index()
        * 100
    )

    for class_value in class_counts.index:
        print(
            f"Clase {class_value}: "
            f"{class_counts[class_value]:,} "
            f"({class_percentages[class_value]:.2f}%)"
        )

    # ==================================================
    # VARIABLES DEL MODELO
    # ==================================================

    model_columns = FEATURE_COLUMNS + [
        "priority_score",
        "high_priority",
    ]

    model_df = df[model_columns].copy()

    # ==================================================
    # VALIDACIÓN FINAL
    # ==================================================

    if model_df.empty:
        raise ValueError(
            "El dataset final está vacío."
        )

    if model_df["high_priority"].nunique() < 2:
        raise ValueError(
            "El target solamente contiene una clase."
        )

    # ==================================================
    # GUARDADO
    # ==================================================

    model_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n=== DATASET FINAL ===")

    print(
        f"Observaciones: "
        f"{len(model_df):,}"
    )

    print(
        f"Variables predictoras: "
        f"{len(FEATURE_COLUMNS)}"
    )

    print(
        "Target: high_priority"
    )

    print(
        "\nPredictoras:"
    )

    for column in FEATURE_COLUMNS:
        print(f"  - {column}")

    print(
        "\nVariables excluidas del modelo:"
    )

    print(
        "  - priority_score"
    )

    print(
        "  - cluster"
    )

    print(
        "\nDataset guardado en:"
    )

    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()