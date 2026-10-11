from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "priority_zones.gpkg"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
)

OUTPUT_PLOT = OUTPUT_DIR / "priority_geospatial_check.png"

LAYER_NAME = "priority_zones"


def main() -> None:

    print("=" * 50)
    print("PRIORITY GEOSPATIAL CHECK")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # --------------------------------------------------
    # CARGA
    # --------------------------------------------------

    gdf = gpd.read_file(
        INPUT_FILE,
        layer=LAYER_NAME,
    )

    print(f"\nZonas cargadas: {len(gdf):,}")

    # --------------------------------------------------
    # CRS
    # --------------------------------------------------

    print("\n=== CRS ===")
    print(gdf.crs)

    if gdf.crs is None:
        raise ValueError(
            "La capa no tiene CRS definido."
        )

    # --------------------------------------------------
    # GEOMETRÍAS
    # --------------------------------------------------

    print("\n=== GEOMETRÍAS ===")

    valid_count = gdf.geometry.is_valid.sum()
    empty_count = gdf.geometry.is_empty.sum()
    null_count = gdf.geometry.isna().sum()

    print(
        f"Geometrías válidas: "
        f"{valid_count:,}"
    )

    print(
        f"Geometrías inválidas: "
        f"{len(gdf) - valid_count:,}"
    )

    print(
        f"Geometrías vacías: "
        f"{empty_count:,}"
    )

    print(
        f"Geometrías nulas: "
        f"{null_count:,}"
    )

    if not gdf.geometry.is_valid.all():
        print(
            "\nADVERTENCIA: existen geometrías inválidas."
        )

    # --------------------------------------------------
    # EXTENSIÓN
    # --------------------------------------------------

    bounds = gdf.total_bounds

    min_x, min_y, max_x, max_y = bounds

    print("\n=== EXTENSIÓN ESPACIAL ===")

    print(f"Longitud mínima: {min_x:.6f}")
    print(f"Longitud máxima: {max_x:.6f}")
    print(f"Latitud mínima: {min_y:.6f}")
    print(f"Latitud máxima: {max_y:.6f}")

    # --------------------------------------------------
    # SOLAPAMIENTOS
    # --------------------------------------------------

    print("\n=== SOLAPAMIENTOS ===")

    overlaps = 0

    spatial_index = gdf.sindex

    for index, geometry in enumerate(gdf.geometry):

        candidates = list(
            spatial_index.query(
                geometry,
                predicate="intersects",
            )
        )

        for candidate in candidates:

            if candidate <= index:
                continue

            if geometry.overlaps(
                gdf.geometry.iloc[candidate]
            ):
                overlaps += 1

    print(
        f"Solapamientos detectados: {overlaps}"
    )

    # --------------------------------------------------
    # CENTROIDES
    # --------------------------------------------------

    centroids = gdf.geometry.centroid

    centroid_x = centroids.x
    centroid_y = centroids.y

    print("\n=== CENTROIDES ===")

    print(
        f"Longitud media: "
        f"{centroid_x.mean():.6f}"
    )

    print(
        f"Latitud media: "
        f"{centroid_y.mean():.6f}"
    )

    # --------------------------------------------------
    # VARIABLES
    # --------------------------------------------------

    print("\n=== VARIABLES ===")

    numeric_columns = [
        "observations",
        "mean_priority",
        "max_priority",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "priority_density",
    ]

    print(
        gdf[numeric_columns]
        .describe()
        .round(6)
        .to_string()
    )

    # --------------------------------------------------
    # CONSISTENCIA CENTROIDE
    # --------------------------------------------------

    if "mean_x" in gdf.columns:
        centroid_x_error = (
            centroid_x - gdf["mean_x"]
        ).abs()

        centroid_y_error = (
            centroid_y - gdf["mean_y"]
        ).abs()

        print("\n=== CONSISTENCIA ESPACIAL ===")

        print(
            "Error medio longitud: "
            f"{centroid_x_error.mean():.8f}"
        )

        print(
            "Error máximo longitud: "
            f"{centroid_x_error.max():.8f}"
        )

        print(
            "Error medio latitud: "
            f"{centroid_y_error.mean():.8f}"
        )

        print(
            "Error máximo latitud: "
            f"{centroid_y_error.max():.8f}"
        )

    # --------------------------------------------------
    # DISTRIBUCIÓN DE PRIORIDAD
    # --------------------------------------------------

    print("\n=== PRIORITY SCORE ===")

    print(
        f"Mínimo: "
        f"{gdf['mean_priority'].min():.6f}"
    )

    print(
        f"Máximo: "
        f"{gdf['mean_priority'].max():.6f}"
    )

    print(
        f"Media: "
        f"{gdf['mean_priority'].mean():.6f}"
    )

    print(
        f"Mediana: "
        f"{gdf['mean_priority'].median():.6f}"
    )

    # --------------------------------------------------
    # MAPA DE CONTROL
    # --------------------------------------------------

    print("\n=== GENERANDO MAPA ===")

    fig, ax = plt.subplots(
        figsize=(10, 10)
    )

    gdf.plot(
        ax=ax,
        column="mean_priority",
        legend=True,
        edgecolor="black",
        linewidth=0.2,
    )

    ax.set_title(
        "Urban AI Bucaramanga - Priority Zones"
    )

    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")

    ax.set_aspect("equal")

    plt.tight_layout()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.savefig(
        OUTPUT_PLOT,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Mapa guardado en:\n"
        f"{OUTPUT_PLOT}"
    )

    # --------------------------------------------------
    # VALIDACIÓN FINAL
    # --------------------------------------------------

    print("\n=== VALIDACIÓN FINAL ===")

    checks = {
        "Cantidad de zonas > 0":
            len(gdf) > 0,

        "CRS definido":
            gdf.crs is not None,

        "Todas las geometrías válidas":
            valid_count == len(gdf),

        "Sin geometrías vacías":
            empty_count == 0,

        "Sin geometrías nulas":
            null_count == 0,

        "Sin solapamientos":
            overlaps == 0,

        "Priority score válido":
            gdf["mean_priority"].notna().all(),
    }

    all_passed = True

    for name, result in checks.items():

        status = "OK" if result else "ERROR"

        print(
            f"[{status}] {name}"
        )

        if not result:
            all_passed = False

    print("\n=== RESULTADO ===")

    if all_passed:
        print(
            "VALIDACIÓN GEOESPACIAL COMPLETADA "
            "CORRECTAMENTE."
        )
    else:
        print(
            "VALIDACIÓN GEOESPACIAL CON "
            "ADVERTENCIAS."
        )


if __name__ == "__main__":
    main()