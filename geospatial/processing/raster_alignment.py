from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

NDVI_PATH = RAW_DIR / "urban_ai_bucaramanga_ndvi.tif"
NDBI_PATH = RAW_DIR / "urban_ai_bucaramanga_ndbi.tif"
LST_PATH = RAW_DIR / "urban_ai_bucaramanga_lst.tif"

NDVI_OUTPUT = PROCESSED_DIR / "ndvi_30m.tif"
NDBI_OUTPUT = PROCESSED_DIR / "ndbi_30m.tif"
LST_OUTPUT = PROCESSED_DIR / "lst_30m.tif"


def read_raster(path: Path):
    """Read the first band and metadata from a raster."""

    with rasterio.open(path) as src:
        data = src.read(1).astype(np.float32)

        return data, src.profile.copy()


def reproject_to_reference(
    source_path: Path,
    reference_path: Path,
    output_path: Path,
) -> None:
    """
    Reproject and resample a raster so it matches the
    spatial grid of the reference raster.
    """

    with rasterio.open(reference_path) as reference:
        reference_data = reference.read(1)

        destination = np.full(
            reference_data.shape,
            np.nan,
            dtype=np.float32,
        )

        with rasterio.open(source_path) as source:

            reproject(
                source=source.read(1).astype(np.float32),
                destination=destination,
                src_transform=source.transform,
                src_crs=source.crs,
                dst_transform=reference.transform,
                dst_crs=reference.crs,
                resampling=Resampling.average,
                src_nodata=np.nan,
                dst_nodata=np.nan,
            )

            profile = reference.profile.copy()

            profile.update(
                dtype="float32",
                count=1,
                nodata=np.nan,
                compress="deflate",
            )

            with rasterio.open(output_path, "w", **profile) as destination_file:
                destination_file.write(destination, 1)


def copy_reference_raster(
    source_path: Path,
    output_path: Path,
) -> None:
    """Copy the reference raster to the processed directory."""

    with rasterio.open(source_path) as source:

        profile = source.profile.copy()

        profile.update(
            dtype="float32",
            count=1,
            nodata=np.nan,
            compress="deflate",
        )

        data = source.read(1).astype(np.float32)

        with rasterio.open(output_path, "w", **profile) as destination:
            destination.write(data, 1)


def print_raster_info(label: str, path: Path) -> None:
    """Print basic raster information."""

    with rasterio.open(path) as src:

        data = src.read(1)

        finite = np.isfinite(data)

        print(f"\n=== {label} ===")
        print(f"Archivo: {path}")
        print(f"Dimensiones: {src.width} x {src.height}")
        print(f"CRS: {src.crs}")
        print(f"Resolución: {src.res}")
        print(f"Bounds: {src.bounds}")
        print(f"Píxeles finitos: {finite.sum()}")

        if finite.any():
            print(f"Mínimo: {np.nanmin(data)}")
            print(f"Máximo: {np.nanmax(data)}")
            print(f"Media: {np.nanmean(data)}")


def main() -> None:

    print("==============================================")
    print("ALINEACIÓN DE RASTERS")
    print("Urban AI Bucaramanga")
    print("==============================================")

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\n1. Alineando NDVI con la cuadrícula LST...")

    reproject_to_reference(
        NDVI_PATH,
        LST_PATH,
        NDVI_OUTPUT,
    )

    print("NDVI procesado.")

    print("\n2. Alineando NDBI con la cuadrícula LST...")

    reproject_to_reference(
        NDBI_PATH,
        LST_PATH,
        NDBI_OUTPUT,
    )

    print("NDBI procesado.")

    print("\n3. Copiando LST como referencia...")

    copy_reference_raster(
        LST_PATH,
        LST_OUTPUT,
    )

    print("LST procesado.")

    print("\n==============================================")
    print("RESULTADOS")
    print("==============================================")

    print_raster_info(
        "NDVI 30m",
        NDVI_OUTPUT,
    )

    print_raster_info(
        "NDBI 30m",
        NDBI_OUTPUT,
    )

    print_raster_info(
        "LST 30m",
        LST_OUTPUT,
    )

    print("\nAlineación completada correctamente.")


if __name__ == "__main__":
    main()