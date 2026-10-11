from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/analysis/urban_priority.csv"
)

OUTPUT_FILE = Path(
    "data/processed/analysis/priority_validation.csv"
)


FEATURES = [
    "ndvi",
    "ndbi",
    "lst",
    "priority_score",
]


def load_data() -> pd.DataFrame:
    """Load the Urban AI priority dataset."""

    df = pd.read_csv(INPUT_FILE)

    required = {
        *FEATURES,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    return df


def classify_priority(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Classify observations into P90 and the remaining 90%."""

    result = df.copy()

    threshold = result["priority_score"].quantile(0.90)

    result["priority_group"] = (
        result["priority_score"] >= threshold
    ).map(
        {
            True: "P90",
            False: "RESTO",
        }
    )

    return result


def build_validation_table(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Compare P90 against the rest of the observations."""

    summary = (
        df.groupby("priority_group")[FEATURES]
        .agg(
            [
                "count",
                "mean",
                "median",
                "std",
                "min",
                "max",
            ]
        )
    )

    return summary


def print_comparison(
    df: pd.DataFrame,
) -> None:
    """Print direct P90 vs RESTO comparison."""

    grouped = (
        df.groupby("priority_group")[FEATURES]
        .mean()
    )

    print("\n=== COMPARACIÓN P90 VS RESTO ===")

    print(grouped.to_string())

    print("\n=== DIFERENCIAS ===")

    p90 = grouped.loc["P90"]
    rest = grouped.loc["RESTO"]

    differences = p90 - rest

    print(
        f"NDVI diferencia: "
        f"{differences['ndvi']:.6f}"
    )

    print(
        f"NDBI diferencia: "
        f"{differences['ndbi']:.6f}"
    )

    print(
        f"LST diferencia: "
        f"{differences['lst']:.6f}"
    )

    print(
        f"Priority Score diferencia: "
        f"{differences['priority_score']:.6f}"
    )


def print_expected_relationships(
    df: pd.DataFrame,
) -> None:
    """Check whether the score behaves according to its construction."""

    correlations = df[
        FEATURES
    ].corr(method="pearson")

    print("\n=== CORRELACIONES ===")

    print(
        correlations[
            ["priority_score"]
        ].to_string()
    )

    print("\n=== VALIDACIÓN DE DIRECCIÓN ===")

    priority_ndvi = correlations.loc[
        "priority_score",
        "ndvi",
    ]

    priority_ndbi = correlations.loc[
        "priority_score",
        "ndbi",
    ]

    priority_lst = correlations.loc[
        "priority_score",
        "lst",
    ]

    print(
        f"Priority Score ↔ NDVI: "
        f"{priority_ndvi:.6f}"
    )

    print(
        f"Priority Score ↔ NDBI: "
        f"{priority_ndbi:.6f}"
    )

    print(
        f"Priority Score ↔ LST: "
        f"{priority_lst:.6f}"
    )


def main() -> None:

    print("=" * 50)
    print("PRIORITY SCORE VALIDATION")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = load_data()

    print(
        f"\nObservaciones: {len(df):,}"
    )

    df = classify_priority(df)

    print_comparison(df)

    print_expected_relationships(df)

    validation = build_validation_table(df)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    validation.to_csv(
        OUTPUT_FILE,
    )

    print("\n=== RESULTADOS ===")

    print(
        f"Validación guardada en: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()