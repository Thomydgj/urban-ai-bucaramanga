from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/analysis/urban_features_clustered.csv"
)

OUTPUT_FILE = Path(
    "data/processed/analysis/cluster_profiles.csv"
)


FEATURES = [
    "ndvi",
    "ndbi",
    "lst",
]


def load_data() -> pd.DataFrame:
    """Load clustered Urban AI dataset."""

    df = pd.read_csv(INPUT_FILE)

    required = {"cluster", *FEATURES}

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    return df


def build_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Build quantitative profiles for each cluster."""

    profiles = (
        df.groupby("cluster")[FEATURES]
        .agg(
            [
                "count",
                "mean",
                "std",
                "min",
                "median",
                "max",
            ]
        )
    )

    return profiles


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a compact cluster summary."""

    summary = (
        df.groupby("cluster")[FEATURES]
        .mean()
        .reset_index()
    )

    counts = (
        df["cluster"]
        .value_counts()
        .sort_index()
        .rename("observations")
    )

    summary = summary.merge(
        counts,
        left_on="cluster",
        right_index=True,
    )

    summary["percentage"] = (
        summary["observations"]
        / len(df)
        * 100
    )

    return summary


def main() -> None:

    print("=" * 50)
    print("CLUSTER PROFILER")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = load_data()

    profiles = build_profiles(df)
    summary = build_summary(df)

    print("\n=== RESUMEN DE CLUSTERS ===")
    print(summary.to_string(index=False))

    print("\n=== PERFILES ESTADÍSTICOS ===")
    print(profiles)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nPerfil guardado en: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()