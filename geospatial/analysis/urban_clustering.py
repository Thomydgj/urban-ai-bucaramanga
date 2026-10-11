from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


INPUT_FILE = Path("data/processed/urban_features.csv")
OUTPUT_DIR = Path("data/processed/analysis")

FEATURES = [
    "ndvi",
    "ndbi",
    "lst",
]


def load_dataset() -> pd.DataFrame:
    """Load the Urban AI dataset."""

    df = pd.read_csv(INPUT_FILE)

    missing = set(FEATURES) - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    return df


def prepare_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, StandardScaler]:
    """Standardize the clustering variables."""

    scaler = StandardScaler()

    X = scaler.fit_transform(
        df[FEATURES]
    )

    return pd.DataFrame(
        X,
        columns=FEATURES,
        index=df.index,
    ), scaler


def evaluate_clusters(
    X: pd.DataFrame,
) -> dict[int, float]:
    """Evaluate K-Means configurations using silhouette score."""

    scores = {}

    print("\n=== EVALUACIÓN DE CLUSTERS ===")

    for k in range(2, 9):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10,
        )

        labels = model.fit_predict(X)

        score = silhouette_score(
            X,
            labels,
        )

        scores[k] = score

        print(
            f"k={k}: "
            f"silhouette={score:.4f}"
        )

    return scores


def fit_final_model(
    X: pd.DataFrame,
    k: int,
) -> KMeans:
    """Fit the final K-Means model."""

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10,
    )

    model.fit(X)

    return model


def describe_clusters(
    df: pd.DataFrame,
) -> None:
    """Print the characteristics of each cluster."""

    print("\n=== CARACTERÍSTICAS DE LOS CLUSTERS ===")

    summary = (
        df.groupby("cluster")[FEATURES]
        .agg(
            [
                "count",
                "mean",
                "std",
                "min",
                "max",
            ]
        )
    )

    print(summary)


def create_cluster_map(
    df: pd.DataFrame,
) -> None:
    """Create a spatial visualization of the clusters."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(10, 8)
    )

    scatter = plt.scatter(
        df["x"],
        df["y"],
        c=df["cluster"],
        s=3,
        alpha=0.6,
    )

    plt.colorbar(
        scatter,
        label="Cluster",
    )

    plt.xlabel("Longitud")
    plt.ylabel("Latitud")

    plt.title(
        "Clustering urbano - Urban AI Bucaramanga"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "urban_clusters.png",
        dpi=200,
    )

    plt.close()


def main() -> None:

    print("=" * 50)
    print("URBAN CLUSTERING")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = load_dataset()

    print(
        f"\nObservaciones: {len(df):,}"
    )

    X, _ = prepare_features(df)

    scores = evaluate_clusters(X)

    best_k = max(
        scores,
        key=scores.get,
    )

    print(
        f"\nMejor k según silhouette: "
        f"{best_k}"
    )

    model = fit_final_model(
        X,
        best_k,
    )

    df["cluster"] = model.labels_

    describe_clusters(df)

    create_cluster_map(df)

    output_file = (
        OUTPUT_DIR
        / "urban_features_clustered.csv"
    )

    df.to_csv(
        output_file,
        index=False,
    )

    print(
        "\n=== RESULTADOS ==="
    )

    print(
        f"Dataset guardado en: "
        f"{output_file}"
    )

    print(
        "Mapa guardado en: "
        f"{OUTPUT_DIR / 'urban_clusters.png'}"
    )


if __name__ == "__main__":
    main()