from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/analysis/urban_features_clustered.csv"
)

OUTPUT_FILE = Path(
    "data/processed/analysis/spatial_cluster_summary.csv"
)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE)

    required = {
        "x",
        "y",
        "cluster",
        "ndvi",
        "ndbi",
        "lst",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    return df


def build_spatial_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("cluster")
        .agg(
            observations=("cluster", "size"),
            mean_x=("x", "mean"),
            mean_y=("y", "mean"),
            min_x=("x", "min"),
            max_x=("x", "max"),
            min_y=("y", "min"),
            max_y=("y", "max"),
            mean_ndvi=("ndvi", "mean"),
            mean_ndbi=("ndbi", "mean"),
            mean_lst=("lst", "mean"),
        )
        .reset_index()
    )

    summary["percentage"] = (
        summary["observations"]
        / len(df)
        * 100
    )

    return summary


def main() -> None:

    print("=" * 50)
    print("SPATIAL CLUSTER ANALYSIS")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = load_data()

    print(f"\nObservaciones: {len(df):,}")

    summary = build_spatial_summary(df)

    print("\n=== RESUMEN ESPACIAL ===")
    print(summary.to_string(index=False))

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nResultado guardado en: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()