from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


PROCESSED_DIR = Path("data/processed")
OUTPUT_DIR = Path("data/processed")

NDVI_PATH = PROCESSED_DIR / "ndvi_30m.tif"
NDBI_PATH = PROCESSED_DIR / "ndbi_30m.tif"
LST_PATH = PROCESSED_DIR / "lst_30m.tif"

OUTPUT_PATH = OUTPUT_DIR / "urban_features.csv"


def read_raster(path: Path) -> tuple[np.ndarray, dict]:
    """Read raster data and metadata."""

    with rasterio.open(path) as src:

        data = src.read(1).astype(np.float32)

        metadata = {
            "transform": src.transform,
            "crs": src.crs,
            "width": src.width,
            "height": src.height,
        }

    return data, metadata


def build_dataset() -> pd.DataFrame:

    ndvi, ndvi_meta = read_raster(NDVI_PATH)
    ndbi, ndbi_meta = read_raster(NDBI_PATH)
    lst, lst_meta = read_raster(LST_PATH)

    print("=== VALIDACIÓN ESPACIAL ===")

    print(f"NDVI: {ndvi.shape}")
    print(f"NDBI: {ndbi.shape}")
    print(f"LST:  {lst.shape}")

    if ndvi.shape != ndbi.shape or ndvi.shape != lst.shape:
        raise ValueError(
            "Los rasters no tienen las mismas dimensiones."
        )

    if ndvi_meta["crs"] != ndbi_meta["crs"]:
        raise ValueError(
            "NDVI y NDBI tienen CRS diferentes."
        )

    if ndvi_meta["crs"] != lst_meta["crs"]:
        raise ValueError(
            "NDVI y LST tienen CRS diferentes."
        )

    if ndvi_meta["transform"] != ndbi_meta["transform"]:
        raise ValueError(
            "NDVI y NDBI tienen transforms diferentes."
        )

    if ndvi_meta["transform"] != lst_meta["transform"]:
        raise ValueError(
            "NDVI y LST tienen transforms diferentes."
        )

    print("Grid espacial validada correctamente.")

    # --------------------------------------------------
    # Coordenadas
    # --------------------------------------------------

    height, width = lst.shape

    rows, cols = np.indices(
        (height, width)
    )

    xs, ys = rasterio.transform.xy(
        lst_meta["transform"],
        rows,
        cols,
    )

    x = np.asarray(xs)
    y = np.asarray(ys)

    # --------------------------------------------------
    # Construcción del dataset
    # --------------------------------------------------

    dataset = pd.DataFrame(
        {
            "x": x.ravel(),
            "y": y.ravel(),
            "ndvi": ndvi.ravel(),
            "ndbi": ndbi.ravel(),
            "lst": lst.ravel(),
        }
    )

    # --------------------------------------------------
    # Eliminar píxeles sin información
    # --------------------------------------------------

    valid_mask = (
        np.isfinite(dataset["ndvi"])
        & np.isfinite(dataset["ndbi"])
        & np.isfinite(dataset["lst"])
    )

    dataset = dataset.loc[
        valid_mask
    ].reset_index(drop=True)

    # --------------------------------------------------
    # Variables derivadas
    # --------------------------------------------------

    dataset["vegetation_signal"] = dataset["ndvi"]

    dataset["built_signal"] = dataset["ndbi"]

    # --------------------------------------------------
    # Guardar
    # --------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return dataset


def print_dataset_summary(
    dataset: pd.DataFrame,
) -> None:

    print("\n==============================================")
    print("DATASET URBAN AI BUCARAMANGA")
    print("==============================================")

    print(
        f"Observaciones válidas: "
        f"{len(dataset):,}"
    )

    print(
        f"Variables: "
        f"{len(dataset.columns)}"
    )

    print("\nColumnas:")

    for column in dataset.columns:
        print(f"  - {column}")

    print("\nEstadísticas:")

    print(
        dataset[
            [
                "ndvi",
                "ndbi",
                "lst",
            ]
        ].describe()
    )

    print("\nPrimeras observaciones:")

    print(
        dataset.head(10).to_string(
            index=False
        )
    )


def main() -> None:

    print("==============================================")
    print("FEATURE BUILDER")
    print("Urban AI Bucaramanga")
    print("==============================================")

    dataset = build_dataset()

    print_dataset_summary(
        dataset
    )

    print(
        f"\nDataset guardado en:\n"
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()