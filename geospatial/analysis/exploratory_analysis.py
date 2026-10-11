from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_FILE = Path("data/processed/urban_features.csv")
OUTPUT_DIR = Path("data/processed/analysis")


def load_dataset() -> pd.DataFrame:
    """Load the Urban AI feature dataset."""
    df = pd.read_csv(INPUT_FILE)

    required_columns = {
        "x",
        "y",
        "ndvi",
        "ndbi",
        "lst",
        "vegetation_signal",
        "built_signal",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print basic dataset information."""

    print("=" * 50)
    print("ANÁLISIS EXPLORATORIO")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    print("\n=== DATASET ===")
    print(f"Observaciones: {len(df):,}")
    print(f"Variables: {len(df.columns)}")

    print("\n=== VALORES NULOS ===")
    print(df.isna().sum())

    print("\n=== ESTADÍSTICAS ===")
    print(
        df[
            [
                "ndvi",
                "ndbi",
                "lst",
                "vegetation_signal",
                "built_signal",
            ]
        ].describe()
    )


def calculate_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlations between urban variables."""

    columns = [
        "ndvi",
        "ndbi",
        "lst",
    ]

    correlations = df[columns].corr()

    print("\n=== CORRELACIONES ===")
    print(correlations)

    return correlations


def create_scatter_plots(df: pd.DataFrame) -> None:
    """Create scatter plots for the main relationships."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 6))
    plt.scatter(
        df["ndvi"],
        df["lst"],
        s=2,
        alpha=0.15,
    )

    plt.xlabel("NDVI")
    plt.ylabel("LST (°C)")
    plt.title("Vegetación vs temperatura superficial")
    plt.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "ndvi_vs_lst.png",
        dpi=200,
    )
    plt.close()

    plt.figure(figsize=(8, 6))
    plt.scatter(
        df["ndbi"],
        df["lst"],
        s=2,
        alpha=0.15,
    )

    plt.xlabel("NDBI")
    plt.ylabel("LST (°C)")
    plt.title("Superficie construida vs temperatura superficial")
    plt.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "ndbi_vs_lst.png",
        dpi=200,
    )
    plt.close()


def create_temperature_map(df: pd.DataFrame) -> None:
    """Create a spatial map of surface temperature."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 8))

    scatter = plt.scatter(
        df["x"],
        df["y"],
        c=df["lst"],
        s=3,
        alpha=0.6,
    )

    plt.colorbar(
        scatter,
        label="LST (°C)",
    )

    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.title("Temperatura superficial - Bucaramanga")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "lst_map.png",
        dpi=200,
    )

    plt.close()


def main() -> None:
    df = load_dataset()

    print_summary(df)

    calculate_correlations(df)

    create_scatter_plots(df)

    create_temperature_map(df)

    print("\n=== RESULTADOS ===")
    print(f"Gráficos guardados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()