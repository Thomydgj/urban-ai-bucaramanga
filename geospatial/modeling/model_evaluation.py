from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


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

RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

RESULTS_PATH = RESULTS_DIR / "model_evaluation.csv"


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
    print("MODEL EVALUATION")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # ==================================================
    # CARGAR DATASET
    # ==================================================

    df = pd.read_csv(DATASET_PATH)

    print("\n=== DATASET ===")
    print(f"Observaciones: {len(df):,}")

    X = df[FEATURES]
    y = df[TARGET].astype(int)

    # ==================================================
    # MISMO SPLIT DEL ENTRENAMIENTO
    # ==================================================

    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print(f"Train: {len(X_train):,}")
    print(f"Test:  {len(X_test):,}")

    # ==================================================
    # CARGAR MODELO
    # ==================================================

    artifact = joblib.load(MODEL_PATH)

    model = artifact["model"]

    print("\n=== MODELO ===")
    print(type(model).__name__)
    print(
        f"Árboles: "
        f"{model.n_estimators}"
    )

    # ==================================================
    # PREDICCIONES
    # ==================================================

    y_pred = model.predict(X_test)

    y_probability = model.predict_proba(
        X_test
    )[:, 1]

    # ==================================================
    # MÉTRICAS
    # ==================================================

    accuracy = accuracy_score(
        y_test,
        y_pred,
    )

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        y_probability,
    )

    print("\n=== MÉTRICAS ===")
    print(f"Accuracy:  {accuracy:.6f}")
    print(f"Precision: {precision:.6f}")
    print(f"Recall:    {recall:.6f}")
    print(f"F1:        {f1:.6f}")
    print(f"ROC-AUC:   {roc_auc:.6f}")

    # ==================================================
    # MATRIZ DE CONFUSIÓN
    # ==================================================

    matrix = confusion_matrix(
        y_test,
        y_pred,
    )

    print("\n=== MATRIZ DE CONFUSIÓN ===")
    print(
        "                Pred 0    Pred 1"
    )
    print(
        f"Real 0       {matrix[0, 0]:8d}"
        f" {matrix[0, 1]:9d}"
    )
    print(
        f"Real 1       {matrix[1, 0]:8d}"
        f" {matrix[1, 1]:9d}"
    )

    # ==================================================
    # REPORTE
    # ==================================================

    print("\n=== CLASSIFICATION REPORT ===")

    print(
        classification_report(
            y_test,
            y_pred,
            target_names=[
                "Baja prioridad",
                "Alta prioridad",
            ],
            zero_division=0,
        )
    )

    # ==================================================
    # RESULTADOS
    # ==================================================

    results = pd.DataFrame(
        {
            "metric": [
                "accuracy",
                "precision",
                "recall",
                "f1",
                "roc_auc",
            ],
            "value": [
                accuracy,
                precision,
                recall,
                f1,
                roc_auc,
            ],
        }
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        RESULTS_PATH,
        index=False,
    )

    print("=== RESULTADOS ===")
    print(
        f"Métricas guardadas en:\n"
        f"{RESULTS_PATH}"
    )


if __name__ == "__main__":
    main()