from pathlib import Path

import numpy as np
import rasterio


DATA_DIR = Path("data/raw")


RASTERS = {
    "NDVI": DATA_DIR / "urban_ai_bucaramanga_ndvi.tif",
    "NDBI": DATA_DIR / "urban_ai_bucaramanga_ndbi.tif",
    "LST": DATA_DIR / "urban_ai_bucaramanga_lst.tif",
}


def inspect_raster(name: str, path: Path) -> None:
    print("\n" + "=" * 60)
    print(f"RASTER: {name}")
    print("=" * 60)

    if not path.exists():
        print(f"ERROR: No existe el archivo: {path}")
        return

    with rasterio.open(path) as src:

        print(f"Archivo: {path}")
        print(f"Driver: {src.driver}")
        print(f"Bandas: {src.count}")

        print(
            f"Dimensiones: "
            f"{src.width} x {src.height}"
        )

        print(
            f"Resolución: "
            f"{src.res[0]} x {src.res[1]}"
        )

        print(f"CRS: {src.crs}")
        print(f"NoData declarado: {src.nodata}")

        print(f"Bounds: {src.bounds}")

        data = src.read(1)

        total_pixels = data.size

        nan_mask = np.isnan(data)
        inf_mask = np.isinf(data)

        finite_mask = np.isfinite(data)

        finite_data = data[finite_mask]

        nan_count = int(nan_mask.sum())
        inf_count = int(inf_mask.sum())
        finite_count = int(finite_mask.sum())

        print("\n--- Calidad de datos ---")

        print(
            f"Píxeles totales: "
            f"{total_pixels}"
        )

        print(
            f"Píxeles finitos: "
            f"{finite_count}"
        )

        print(
            f"NaN: "
            f"{nan_count}"
        )

        print(
            f"Inf: "
            f"{inf_count}"
        )

        valid_percentage = (
            finite_count / total_pixels
        ) * 100

        print(
            f"Píxeles finitos: "
            f"{valid_percentage:.2f}%"
        )

        if finite_count == 0:
            print(
                "\nERROR: "
                "No existen valores numéricos válidos."
            )
            return

        print("\n--- Estadísticas ---")

        print(
            f"Mínimo: "
            f"{finite_data.min()}"
        )

        print(
            f"Máximo: "
            f"{finite_data.max()}"
        )

        print(
            f"Media: "
            f"{finite_data.mean()}"
        )

        print(
            f"Mediana: "
            f"{np.median(finite_data)}"
        )

        print(
            f"Desviación estándar: "
            f"{finite_data.std()}"
        )


def main() -> None:
    print("INSPECTOR DE RASTER")
    print("Proyecto Urban AI Bucaramanga")

    for name, path in RASTERS.items():
        inspect_raster(name, path)


if __name__ == "__main__":
    main()