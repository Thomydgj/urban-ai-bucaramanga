
from pathlib import Path
import json

import numpy as np
from PIL import Image

from ml.segmentation.config import DEVICE
from ml.segmentation.dataset import (
    BUILT_UP,
    IGNORE_INDEX,
    OTHER,
    ROADS,
    VEGETATION,
)
from ml.segmentation.predict_trained import (
    load_trained_model,
    predict,
    create_visualization,
)


# --------------------------------------------------
# PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "loveda"
    / "train"
    / "Train"
    / "Rural"
    / "images_png"
    / "22.png"
)

MASK_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "loveda"
    / "train"
    / "Train"
    / "Rural"
    / "masks_png"
    / "22.png"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "segmentation"
    / "outputs"
    / "evaluation_rural_22"
)

PREDICTION_PATH = OUTPUT_DIR / "predicted_mask.png"
REFERENCE_PATH = OUTPUT_DIR / "reference_mask.png"
OVERLAY_PATH = OUTPUT_DIR / "prediction_overlay.png"
METRICS_PATH = OUTPUT_DIR / "metrics.json"


# --------------------------------------------------
# CLASS MAPPING
# --------------------------------------------------

CLASS_NAMES = {
    VEGETATION: "vegetacion",
    BUILT_UP: "construido",
    ROADS: "vias",
    OTHER: "otros",
}

# Original LoveDA labels:
# 0 = no-data
# 1 = background
# 2 = building
# 3 = road
# 4 = water
# 5 = barren
# 6 = forest
# 7 = agriculture

LOVE_DA_TO_URBAN = {
    0: IGNORE_INDEX,
    1: OTHER,
    2: BUILT_UP,
    3: ROADS,
    4: OTHER,
    5: OTHER,
    6: VEGETATION,
    7: VEGETATION,
}


def map_reference_mask(mask: np.ndarray) -> np.ndarray:
    """Convert original LoveDA labels to Urban AI classes."""

    mapped = np.full(
        mask.shape,
        IGNORE_INDEX,
        dtype=np.uint8,
    )

    for original_id, urban_id in LOVE_DA_TO_URBAN.items():
        mapped[mask == original_id] = urban_id

    unknown = ~np.isin(
        mask,
        list(LOVE_DA_TO_URBAN.keys()),
    )

    if np.any(unknown):
        values = np.unique(mask[unknown]).tolist()
        raise ValueError(
            f"Etiquetas LoveDA desconocidas: {values}"
        )

    return mapped


# --------------------------------------------------
# METRICS
# --------------------------------------------------

def evaluate_masks(
    prediction: np.ndarray,
    reference: np.ndarray,
) -> dict:
    """Calculate per-class IoU and mean IoU."""

    if prediction.shape != reference.shape:
        raise ValueError(
            f"Dimensiones diferentes: "
            f"predicción={prediction.shape}, "
            f"referencia={reference.shape}"
        )

    valid = reference != IGNORE_INDEX

    if not np.any(valid):
        raise ValueError(
            "La máscara no contiene píxeles válidos."
        )

    results = {}
    valid_ious = []

    for class_id, class_name in CLASS_NAMES.items():
        pred_class = (prediction == class_id) & valid
        ref_class = (reference == class_id) & valid

        intersection = int(
            np.count_nonzero(pred_class & ref_class)
        )

        union = int(
            np.count_nonzero(pred_class | ref_class)
        )

        pred_pixels = int(np.count_nonzero(pred_class))
        reference_pixels = int(np.count_nonzero(ref_class))

        if union == 0:
            iou = None
            dice = None
        else:
            iou = intersection / union

            dice_denominator = (
                pred_pixels + reference_pixels
            )

            dice = (
                2 * intersection / dice_denominator
                if dice_denominator > 0
                else None
            )

            valid_ious.append(iou)

        results[class_name] = {
            "iou": iou,
            "dice": dice,
            "intersection_pixels": intersection,
            "union_pixels": union,
            "predicted_pixels": pred_pixels,
            "reference_pixels": reference_pixels,
            "reference_proportion": (
                reference_pixels / np.count_nonzero(valid)
            ),
            "prediction_proportion": (
                pred_pixels / np.count_nonzero(valid)
            ),
        }

    mean_iou = (
        float(np.mean(valid_ious))
        if valid_ious
        else None
    )

    return {
        "image": IMAGE_PATH.name,
        "split": "Train/Rural",
        "device": str(DEVICE),
        "valid_pixels": int(np.count_nonzero(valid)),
        "ignored_pixels": int(np.count_nonzero(~valid)),
        "miou_over_classes_with_nonzero_union": mean_iou,
        "evaluated_classes": len(valid_ious),
        "classes": results,
        "warning": (
            "Esta imagen pertenece a Train/Rural. "
            "Es una evaluación de diagnóstico sobre una "
            "imagen de entrenamiento, no una evaluación "
            "independiente ni el mIoU oficial de validación."
        ),
    }


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main() -> None:
    print("=== EVALUACIÓN DE SEGMENTACIÓN LOVE DA ===")

    for path in (IMAGE_PATH, MASK_PATH):
        if not path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo: {path}"
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.open(IMAGE_PATH).convert("RGB")
    original_mask = np.array(Image.open(MASK_PATH))

    if original_mask.ndim != 2:
        raise ValueError(
            "La máscara de referencia debe ser una "
            "imagen de etiquetas de un solo canal."
        )

    if image.size != (
        original_mask.shape[1],
        original_mask.shape[0],
    ):
        raise ValueError(
            "La imagen y la máscara tienen dimensiones distintas."
        )

    reference = map_reference_mask(original_mask)

    print(f"Imagen: {IMAGE_PATH}")
    print(f"Máscara: {MASK_PATH}")
    print(f"Dimensiones: {image.size}")
    print("Cargando modelo entrenado...")

    model, processor = load_trained_model()

    prediction_tensor = predict(
        image,
        model,
        processor,
    )

    prediction = prediction_tensor.numpy().astype(np.uint8)

    metrics = evaluate_masks(
        prediction,
        reference,
    )

    # Save masks as class-ID PNGs.
    Image.fromarray(prediction).save(PREDICTION_PATH)
    Image.fromarray(reference).save(REFERENCE_PATH)

    create_visualization(
        image,
        prediction_tensor,
        OVERLAY_PATH,
    )

    with open(METRICS_PATH, "w", encoding="utf-8") as file:
        json.dump(
            metrics,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n=== RESULTADOS POR CLASE ===")

    for class_name, values in metrics["classes"].items():
        iou = values["iou"]

        iou_text = (
            f"{iou:.4f} ({iou * 100:.2f}%)"
            if iou is not None
            else "N/A (unión vacía)"
        )

        print(f"\n{class_name}:")
        print(f"  IoU: {iou_text}")
        print(
            "  Proporción referencia: "
            f"{values['reference_proportion'] * 100:.2f}%"
        )
        print(
            "  Proporción predicción: "
            f"{values['prediction_proportion'] * 100:.2f}%"
        )

    mean_iou = metrics["miou_over_classes_with_nonzero_union"]

    print("\n=== mIoU DE ESTA IMAGEN ===")
    if mean_iou is None:
        print("No disponible.")
    else:
        print(f"{mean_iou:.4f} ({mean_iou * 100:.2f}%)")

    print(
        "\nNota: este valor corresponde a una sola imagen "
        "de Train/Rural; no reemplaza el mIoU de validación."
    )

    print("\nArchivos guardados:")
    print(f"Máscara predicha: {PREDICTION_PATH}")
    print(f"Máscara referencia: {REFERENCE_PATH}")
    print(f"Visualización: {OVERLAY_PATH}")
    print(f"Métricas: {METRICS_PATH}")


if __name__ == "__main__":
    main()
