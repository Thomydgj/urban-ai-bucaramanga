from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "data" / "processed" / "modeling"


INPUT_GPKG = MODEL_DIR / "urban_ai_final_priority.gpkg"

OUTPUT_MAP = MODEL_DIR / "urban_ai_final_priority_map.png"
OUTPUT_CSV = MODEL_DIR / "urban_ai_final_priority_map_summary.csv"


def main() -> None:

    print("=" * 60)
    print("FINAL PRIORITY MAP")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    # =========================================================
    # CARGAR CAPA
    # =========================================================

    gdf = gpd.read_file(
        INPUT_GPKG,
        layer="final_priority",
    )

    print("\n=== CAPA ===")
    print(f"Observaciones: {len(gdf):,}")
    print(f"CRS: {gdf.crs}")

    # =========================================================
    # VALIDACIÓN
    # =========================================================

    if gdf.empty:
        raise ValueError(
            "La capa espacial está vacía."
        )

    if gdf.crs is None:
        raise ValueError(
            "La capa no tiene CRS definido."
        )

    invalid = (~gdf.geometry.is_valid).sum()
    empty = gdf.geometry.is_empty.sum()
    null = gdf.geometry.isna().sum()

    print("\n=== VALIDACIÓN ===")
    print(f"Geometrías inválidas: {invalid}")
    print(f"Geometrías vacías: {empty}")
    print(f"Geometrías nulas: {null}")

    if invalid > 0:
        raise ValueError(
            "Existen geometrías inválidas."
        )

    if empty > 0:
        raise ValueError(
            "Existen geometrías vacías."
        )

    if null > 0:
        raise ValueError(
            "Existen geometrías nulas."
        )

    # =========================================================
    # RESUMEN
    # =========================================================

    summary = (
        gdf.groupby("final_priority")
        .agg(
            observations=("final_priority", "size"),
            mean_probability=(
                "priority_probability",
                "mean",
            ),
            mean_ndvi=("ndvi", "mean"),
            mean_ndbi=("ndbi", "mean"),
            mean_lst=("lst", "mean"),
        )
        .reset_index()
    )

    summary["percentage"] = (
        summary["observations"]
        / len(gdf)
        * 100
    )

    order = [
        "MUY_ALTA",
        "ALTA",
        "MEDIA",
        "BAJA",
    ]

    summary["final_priority"] = pd.Categorical(
        summary["final_priority"],
        categories=order,
        ordered=True,
    )

    summary = summary.sort_values(
        "final_priority"
    )

    print("\n=== RESUMEN ===")
    print(summary.to_string(index=False))

    # =========================================================
    # MAPA
    # =========================================================

    print("\n=== GENERANDO MAPA ===")

    fig, ax = plt.subplots(
        figsize=(12, 10)
    )

    # Dibujar primero las zonas bajas
    colors = {
        "BAJA": "#d9d9d9",
        "MEDIA": "#ffd166",
        "ALTA": "#f77f00",
        "MUY_ALTA": "#d62828",
    }

    for level in [
        "BAJA",
        "MEDIA",
        "ALTA",
        "MUY_ALTA",
    ]:

        subset = gdf[
            gdf["final_priority"] == level
        ]

        if subset.empty:
            continue

        subset.plot(
            ax=ax,
            color=colors[level],
            markersize=2.5,
            alpha=0.70,
            label=level,
        )

    # =========================================================
    # CONFIGURACIÓN
    # =========================================================

    ax.set_title(
        "Urban AI Bucaramanga\n"
        "Mapa Final de Prioridad Urbana",
        fontsize=18,
        fontweight="bold",
        pad=15,
    )

    ax.set_xlabel(
        "Longitud (EPSG:4326)"
    )

    ax.set_ylabel(
        "Latitud (EPSG:4326)"
    )

    ax.legend(
        title="Nivel de prioridad",
        loc="upper right",
        frameon=True,
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    # =========================================================
    # INFORMACIÓN DEL MODELO
    # =========================================================

    total = len(gdf)

    high = int(
        gdf["final_high_priority"].sum()
    )

    mean_probability = (
        gdf["priority_probability"].mean()
    )

    text = (
        f"Observaciones: {total:,}\n"
        f"Alta prioridad: {high:,}\n"
        f"Probabilidad media: "
        f"{mean_probability:.4f}"
    )

    ax.text(
        0.02,
        0.02,
        text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="bottom",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.85,
        ),
    )

    plt.tight_layout()

    fig.savefig(
        OUTPUT_MAP,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    # =========================================================
    # EXPORTAR RESUMEN
    # =========================================================

    summary.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # =========================================================
    # RESULTADOS
    # =========================================================

    print("\n=== RESULTADOS ===")

    print(
        f"Mapa:\n{OUTPUT_MAP}"
    )

    print(
        f"\nResumen:\n{OUTPUT_CSV}"
    )

    print(
        "\nProceso completado correctamente."
    )


if __name__ == "__main__":
    main()