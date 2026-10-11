from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "urban_priority.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "priority_spatial_summary.csv"
)

GRID_SIZE = 0.002


def main() -> None:
    print("=" * 50)
    print("PRIORITY SPATIAL SUMMARY")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    df = pd.read_csv(INPUT_FILE)

    print(f"\nObservaciones: {len(df):,}")

    required_columns = {
        "x",
        "y",
        "ndvi",
        "ndbi",
        "lst",
        "priority_score",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(missing)}"
        )

    # --------------------------------------------------
    # IDENTIFICACIÓN P90
    # --------------------------------------------------

    threshold = df["priority_score"].quantile(0.90)

    df["priority_p90"] = (
        df["priority_score"] >= threshold
    )

    priority = df[df["priority_p90"]].copy()

    print("\n=== P90 ===")
    print(f"Umbral: {threshold:.6f}")
    print(f"Observaciones: {len(priority):,}")
    print(
        f"Porcentaje: "
        f"{len(priority) / len(df) * 100:.2f}%"
    )

    # --------------------------------------------------
    # CREACIÓN DE GRID ESPACIAL
    # --------------------------------------------------

    min_x = df["x"].min()
    min_y = df["y"].min()

    priority["grid_x"] = np.floor(
        (priority["x"] - min_x) / GRID_SIZE
    ).astype(int)

    priority["grid_y"] = np.floor(
        (priority["y"] - min_y) / GRID_SIZE
    ).astype(int)

    # --------------------------------------------------
    # AGRUPACIÓN ESPACIAL
    # --------------------------------------------------

    summary = (
        priority
        .groupby(["grid_x", "grid_y"])
        .agg(
            observations=("priority_score", "size"),
            mean_priority=("priority_score", "mean"),
            max_priority=("priority_score", "max"),
            mean_ndvi=("ndvi", "mean"),
            mean_ndbi=("ndbi", "mean"),
            mean_lst=("lst", "mean"),
            mean_x=("x", "mean"),
            mean_y=("y", "mean"),
        )
        .reset_index()
    )

    # --------------------------------------------------
    # DENSIDAD RELATIVA
    # --------------------------------------------------

    summary["priority_density"] = (
        summary["observations"]
        / summary["observations"].max()
    )

    # --------------------------------------------------
    # ORDEN DE CONCENTRACIÓN
    # --------------------------------------------------

    summary = summary.sort_values(
        "observations",
        ascending=False,
    ).reset_index(drop=True)

    summary["spatial_rank"] = (
        np.arange(len(summary)) + 1
    )

    # --------------------------------------------------
    # GUARDAR
    # --------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------

    print("\n=== RESUMEN ESPACIAL ===")

    print(
        f"Zonas espaciales: "
        f"{len(summary):,}"
    )

    print(
        f"Mayor concentración: "
        f"{summary.iloc[0]['observations']:.0f} "
        f"observaciones"
    )

    print("\n=== TOP 10 ZONAS ===")

    print(
        summary[
            [
                "spatial_rank",
                "observations",
                "mean_x",
                "mean_y",
                "mean_ndvi",
                "mean_ndbi",
                "mean_lst",
                "mean_priority",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\n=== RESULTADOS ===")

    print(
        f"Resumen guardado en:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()