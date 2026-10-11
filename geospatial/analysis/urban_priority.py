from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/analysis/urban_features_clustered.csv"
)

OUTPUT_FILE = Path(
    "data/processed/analysis/urban_priority.csv"
)


FEATURES = [
    "ndvi",
    "ndbi",
    "lst",
]


def load_data() -> pd.DataFrame:
    """Load the clustered Urban AI dataset."""

    df = pd.read_csv(INPUT_FILE)

    required = {
        "x",
        "y",
        "cluster",
        *FEATURES,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    return df


def min_max_normalize(
    series: pd.Series,
) -> pd.Series:
    """Normalize a series to the [0, 1] interval."""

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            0.0,
            index=series.index,
        )

    return (series - minimum) / (maximum - minimum)


def build_priority_score(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a transparent urban priority score.

    Higher score means:
    - higher land surface temperature
    - higher built-up signal
    - lower vegetation signal
    """

    result = df.copy()

    # Higher NDVI means more vegetation,
    # therefore invert it for vegetation pressure.
    ndvi_normalized = min_max_normalize(
        result["ndvi"]
    )

    result["vegetation_pressure"] = (
        1.0 - ndvi_normalized
    )

    # Higher NDBI means stronger built-up signal.
    result["built_pressure"] = min_max_normalize(
        result["ndbi"]
    )

    # Higher LST means stronger thermal pressure.
    result["heat_pressure"] = min_max_normalize(
        result["lst"]
    )

    # Equal weights: 1/3 each.
    result["priority_score"] = (
        result["vegetation_pressure"]
        + result["built_pressure"]
        + result["heat_pressure"]
    ) / 3.0

    return result


def print_statistics(
    df: pd.DataFrame,
) -> None:
    """Print descriptive statistics for the priority score."""

    score = df["priority_score"]

    print("\n=== PRIORITY SCORE ===")

    print(
        f"Mínimo: {score.min():.6f}"
    )

    print(
        f"Máximo: {score.max():.6f}"
    )

    print(
        f"Media: {score.mean():.6f}"
    )

    print(
        f"Mediana: {score.median():.6f}"
    )

    print("\n=== PERCENTILES ===")

    percentiles = score.quantile(
        [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    )

    for percentile, value in percentiles.items():
        print(
            f"P{int(percentile * 100):02d}: "
            f"{value:.6f}"
        )

    threshold = score.quantile(0.90)

    high_priority = score >= threshold

    count = int(high_priority.sum())

    percentage = (
        count / len(score) * 100
    )

    print("\n=== ALTA PRIORIDAD ===")

    print(
        f"Umbral P90: {threshold:.6f}"
    )

    print(
        f"Observaciones: {count:,}"
    )

    print(
        f"Porcentaje: {percentage:.2f}%"
    )


def main() -> None:

    print("=" * 50)
    print("URBAN PRIORITY SCORE")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = load_data()

    print(
        f"\nObservaciones: {len(df):,}"
    )

    result = build_priority_score(df)

    print_statistics(result)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\n=== RESULTADOS ==="
    )

    print(
        f"Dataset guardado en: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()