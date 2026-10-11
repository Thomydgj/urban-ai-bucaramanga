from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_FILE = Path(
    "data/processed/analysis/urban_priority.csv"
)

OUTPUT_DIR = Path(
    "data/processed/analysis"
)

MAP_FILE = OUTPUT_DIR / "urban_priority.png"
HIGH_PRIORITY_FILE = OUTPUT_DIR / "urban_priority_p90.png"


def load_data() -> pd.DataFrame:
    """Load the Urban AI priority dataset."""

    df = pd.read_csv(INPUT_FILE)

    required = {
        "x",
        "y",
        "cluster",
        "ndvi",
        "ndbi",
        "lst",
        "vegetation_pressure",
        "built_pressure",
        "heat_pressure",
        "priority_score",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    return df


def build_priority_map(
    df: pd.DataFrame,
) -> None:
    """Generate continuous priority score map."""

    plt.figure(figsize=(10, 10))

    scatter = plt.scatter(
        df["x"],
        df["y"],
        c=df["priority_score"],
        s=1,
        alpha=0.6,
    )

    plt.colorbar(
        scatter,
        label="Urban Priority Score",
    )

    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.title(
        "Urban AI Bucaramanga - Priority Score"
    )

    plt.axis("equal")
    plt.tight_layout()

    plt.savefig(
        MAP_FILE,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()


def build_high_priority_map(
    df: pd.DataFrame,
) -> None:
    """Generate map showing only the P90 priority observations."""

    threshold = df["priority_score"].quantile(0.90)

    high_priority = df[
        df["priority_score"] >= threshold
    ]

    plt.figure(figsize=(10, 10))

    plt.scatter(
        df["x"],
        df["y"],
        s=0.5,
        alpha=0.15,
    )

    plt.scatter(
        high_priority["x"],
        high_priority["y"],
        c=high_priority["priority_score"],
        s=2,
        alpha=0.8,
    )

    plt.xlabel("Longitud")
    plt.ylabel("Latitud")

    plt.title(
        "Urban AI Bucaramanga - Alta Prioridad (P90)"
    )

    plt.axis("equal")
    plt.tight_layout()

    plt.savefig(
        HIGH_PRIORITY_FILE,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()


def print_statistics(
    df: pd.DataFrame,
) -> None:
    """Print spatial statistics for high-priority observations."""

    threshold = df["priority_score"].quantile(0.90)

    high_priority = df[
        df["priority_score"] >= threshold
    ]

    print("\n=== PRIORITY SCORE ===")

    print(
        f"Umbral P90: {threshold:.6f}"
    )

    print(
        f"Observaciones P90: "
        f"{len(high_priority):,}"
    )

    print(
        f"Porcentaje: "
        f"{len(high_priority) / len(df) * 100:.2f}%"
    )

    print("\n=== EXTENSIÓN ESPACIAL P90 ===")

    print(
        f"Longitud mínima: "
        f"{high_priority['x'].min():.6f}"
    )

    print(
        f"Longitud máxima: "
        f"{high_priority['x'].max():.6f}"
    )

    print(
        f"Latitud mínima: "
        f"{high_priority['y'].min():.6f}"
    )

    print(
        f"Latitud máxima: "
        f"{high_priority['y'].max():.6f}"
    )

    print("\n=== CENTROIDE P90 ===")

    print(
        f"Longitud media: "
        f"{high_priority['x'].mean():.6f}"
    )

    print(
        f"Latitud media: "
        f"{high_priority['y'].mean():.6f}"
    )

    print("\n=== VARIABLES P90 ===")

    print(
        f"NDVI medio: "
        f"{high_priority['ndvi'].mean():.6f}"
    )

    print(
        f"NDBI medio: "
        f"{high_priority['ndbi'].mean():.6f}"
    )

    print(
        f"LST media: "
        f"{high_priority['lst'].mean():.6f}"
    )

    print(
        f"Priority Score medio: "
        f"{high_priority['priority_score'].mean():.6f}"
    )


def main() -> None:

    print("=" * 50)
    print("PRIORITY MAPPING")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = load_data()

    print(
        f"\nObservaciones: {len(df):,}"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    build_priority_map(df)

    build_high_priority_map(df)

    print_statistics(df)

    print("\n=== RESULTADOS ===")

    print(
        f"Mapa completo: {MAP_FILE}"
    )

    print(
        f"Mapa P90: {HIGH_PRIORITY_FILE}"
    )


if __name__ == "__main__":
    main()