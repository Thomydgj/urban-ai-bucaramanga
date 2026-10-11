
from pathlib import Path
from xml.parsers.expat import model

import joblib
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import rowcol


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_model_dataset.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_priority_model.joblib"
)

REFERENCE_RASTER = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "lst_30m.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

PROBABILITY_RASTER = OUTPUT_DIR / "urban_priority_probability.tif"
CLASS_RASTER = OUTPUT_DIR / "urban_priority_class.tif"


FEATURES = [
    "x",
    "y",
    "ndvi",
    "ndbi",
    "lst",
    "vegetation_signal",
    "built_signal",
]


def main() -> None:

    print("=" * 50)
    print("MODEL RASTER PREDICTION")
    print("Urban AI Bucaramanga")
    print("=" * 50)

    # =========================================================
    # DATASET
    # =========================================================

    df = pd.read_csv(DATASET_PATH)

    print()
    print("=== DATASET ===")
    print(f"Observaciones: {len(df):,}")

    missing_features = [
        feature
        for feature in FEATURES
        if feature not in df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Faltan variables predictoras: {missing_features}"
        )

    # =========================================================
    # MODEL
    # =========================================================

    model_bundle = joblib.load(MODEL_PATH)

    model = model_bundle["model"]

    saved_features = model_bundle["features"]

    if saved_features != FEATURES:
        raise ValueError(
            "Las variables predictoras del modelo no coinciden "
            "con las variables esperadas.\n"
            f"Modelo: {saved_features}\n"
            f"Esperadas: {FEATURES}"
        )

    print("=== MODELO ===")
    print(f"Modelo: {type(model).__name__}")
    print(f"Variables predictoras: {len(saved_features)}")
    print(f"Target: {model_bundle['target']}")
    print(f"Random state: {model_bundle['random_state']}")

    # =========================================================
    # REFERENCE RASTER
    # =========================================================

    with rasterio.open(REFERENCE_RASTER) as src:

        height = src.height
        width = src.width
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
        profile = src.profile.copy()

    total_pixels = height * width

    print()
    print("=== RASTER DE REFERENCIA ===")
    print(f"Dimensiones: {height} x {width}")
    print(f"Píxeles totales: {total_pixels:,}")
    print(f"CRS: {crs}")
    print(f"Bounds: {bounds}")

    # =========================================================
    # VALIDATION
    # =========================================================

    print()
    print("=== VALIDACIÓN ===")
    print(f"Observaciones del dataset: {len(df):,}")
    print(f"Píxeles del raster:       {total_pixels:,}")

    if len(df) > total_pixels:
        raise ValueError(
            "El dataset contiene más observaciones que píxeles "
            "del raster de referencia."
        )

    # =========================================================
    # PREDICTION
    # =========================================================

    print()
    print("=== PREDICCIÓN ===")
    print("Generando probabilidades...")

    X = df[FEATURES]

    probabilities = model.predict_proba(X)[:, 1]

    print("Predicción completada.")

    print()
    print("=== PRIORITY PROBABILITY ===")
    print(f"Mínimo: {probabilities.min():.6f}")
    print(f"Máximo: {probabilities.max():.6f}")
    print(f"Media: {probabilities.mean():.6f}")
    print(f"Mediana: {np.median(probabilities):.6f}")

    # =========================================================
    # COORDINATE -> RASTER INDEX
    # =========================================================

    print()
    print("=== UBICACIÓN ESPACIAL ===")

    rows, cols = rowcol(
        transform,
        df["x"].to_numpy(),
        df["y"].to_numpy(),
    )

    rows = np.asarray(rows)
    cols = np.asarray(cols)

    valid_position = (
        (rows >= 0)
        & (rows < height)
        & (cols >= 0)
        & (cols < width)
    )

    invalid_positions = int((~valid_position).sum())

    print(
        f"Observaciones dentro del raster: "
        f"{valid_position.sum():,}"
    )

    print(
        f"Observaciones fuera del raster: "
        f"{invalid_positions:,}"
    )

    if invalid_positions > 0:
        raise ValueError(
            "Hay observaciones fuera de la extensión del raster "
            "de referencia."
        )

    # =========================================================
    # CREATE EMPTY RASTERS
    # =========================================================

    probability_array = np.full(
        (height, width),
        np.nan,
        dtype=np.float32,
    )

    class_array = np.full(
        (height, width),
        255,
        dtype=np.uint8,
    )

    # =========================================================
    # WRITE PREDICTIONS
    # =========================================================

    probability_array[rows, cols] = probabilities.astype(
        np.float32
    )

    classes = (probabilities >= 0.5).astype(np.uint8)

    class_array[rows, cols] = classes

    # =========================================================
    # COVERAGE VALIDATION
    # =========================================================

    probability_valid = np.isfinite(probability_array)

    valid_probability_pixels = int(
        probability_valid.sum()
    )

    nodata_probability_pixels = int(
        (~probability_valid).sum()
    )

    print()
    print("=== COBERTURA ===")
    print(
        f"Píxeles predichos: "
        f"{valid_probability_pixels:,}"
    )

    print(
        f"Píxeles NoData:    "
        f"{nodata_probability_pixels:,}"
    )

    print(
        f"Cobertura: "
        f"{valid_probability_pixels / total_pixels * 100:.2f}%"
    )

    # =========================================================
    # OUTPUT PROFILE
    # =========================================================

    probability_profile = profile.copy()

    probability_profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        height=height,
        width=width,
        crs=crs,
        transform=transform,
        nodata=np.nan,
        compress="deflate",
    )

    class_profile = profile.copy()

    class_profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        height=height,
        width=width,
        crs=crs,
        transform=transform,
        nodata=255,
        compress="deflate",
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =========================================================
    # SAVE PROBABILITY RASTER
    # =========================================================

    print()
    print("=== EXPORTANDO RASTERS ===")

    with rasterio.open(
        PROBABILITY_RASTER,
        "w",
        **probability_profile,
    ) as dst:

        dst.write(
            probability_array,
            1,
        )

    print(
        f"Probability raster:\n"
        f"{PROBABILITY_RASTER}"
    )

    # =========================================================
    # SAVE CLASS RASTER
    # =========================================================

    with rasterio.open(
        CLASS_RASTER,
        "w",
        **class_profile,
    ) as dst:

        dst.write(
            class_array,
            1,
        )

    print(
        f"Class raster:\n"
        f"{CLASS_RASTER}"
    )

    # =========================================================
    # FINAL STATISTICS
    # =========================================================

    high_priority_pixels = int(
        np.sum(
            probability_array >= 0.5
        )
    )

    low_priority_pixels = int(
        np.sum(
            (probability_array >= 0)
            & (probability_array < 0.5)
        )
    )

    print()
    print("=== CLASIFICACIÓN ESPACIAL ===")
    print(
        f"Alta prioridad: "
        f"{high_priority_pixels:,}"
    )

    print(
        f"Baja prioridad: "
        f"{low_priority_pixels:,}"
    )

    print(
        f"NoData: "
        f"{nodata_probability_pixels:,}"
    )

    print()
    print("=== VALIDACIÓN FINAL ===")

    print(
        f"[OK] Raster: {height} x {width}"
    )

    print(
        f"[OK] Píxeles totales: "
        f"{total_pixels:,}"
    )

    print(
        f"[OK] Predicciones: "
        f"{valid_probability_pixels:,}"
    )

    print(
        f"[OK] NoData: "
        f"{nodata_probability_pixels:,}"
    )

    print(
        f"[OK] CRS: {crs}"
    )

    print()
    print("Proceso completado correctamente.")


if __name__ == "__main__":
    main()
