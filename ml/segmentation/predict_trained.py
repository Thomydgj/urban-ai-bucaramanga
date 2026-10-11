from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import (
    AutoImageProcessor,
    SegformerForSemanticSegmentation,
)

from ml.segmentation.config import DEVICE
from ml.segmentation.dataset import (
    BUILT_UP,
    IGNORE_INDEX,
    OTHER,
    ROADS,
    VEGETATION,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    PROJECT_ROOT
    / "ml"
    / "segmentation"
    / "outputs"
    / "training"
    / "best_model"
)

INPUT_IMAGE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "segmentation"
    / "test_urban.png"
)

OUTPUT_IMAGE = (
    PROJECT_ROOT
    / "ml"
    / "segmentation"
    / "outputs"
    / "test_urban_trained_segmentation.png"
)


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

CLASS_NAMES = {
    VEGETATION: "vegetation",
    BUILT_UP: "built_up",
    ROADS: "roads",
    OTHER: "other",
}


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


def load_trained_model():
    """Load the fine-tuned Urban AI segmentation model."""

    model = SegformerForSemanticSegmentation.from_pretrained(
        MODEL_DIR
    )

    model.to(DEVICE)
    model.eval()

    processor = AutoImageProcessor.from_pretrained(
        MODEL_DIR
    )

    return model, processor


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


def predict(
    image: Image.Image,
    model,
    processor,
) -> torch.Tensor:
    """Predict the four Urban AI classes."""

    inputs = processor(
        images=image,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = model(**inputs)

    mask = processor.post_process_semantic_segmentation(
        outputs,
        target_sizes=[image.size[::-1]],
    )[0]

    return mask.cpu()


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def calculate_proportions(
    mask: torch.Tensor,
) -> dict[str, float]:
    """Calculate pixel proportions for the four classes."""

    mask_array = mask.numpy()

    valid_mask = mask_array != IGNORE_INDEX

    total_pixels = np.count_nonzero(
        valid_mask
    )

    if total_pixels == 0:
        return {
            name: 0.0
            for name in CLASS_NAMES.values()
        }

    proportions = {}

    for class_id, class_name in CLASS_NAMES.items():

        pixels = np.count_nonzero(
            (mask_array == class_id)
            & valid_mask
        )

        proportions[class_name] = (
            pixels / total_pixels
        )

    return proportions


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------


def create_visualization(
    image: Image.Image,
    mask: torch.Tensor,
    output_path: Path,
) -> None:
    """Create a segmentation overlay."""

    image_array = np.asarray(
        image.convert("RGB")
    ).astype(np.float32)

    mask_array = mask.numpy()

    palette = np.array(
        [
            [46, 125, 50],    # vegetation
            [180, 80, 60],    # built_up
            [60, 100, 180],   # roads
            [150, 150, 150],  # other
        ],
        dtype=np.float32,
    )

    mask_colors = palette[
        np.clip(mask_array, 0, 3)
    ]

    overlay = (
        image_array * 0.55
        + mask_colors * 0.45
    )

    overlay = np.clip(
        overlay,
        0,
        255,
    ).astype(np.uint8)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    Image.fromarray(
        overlay
    ).save(output_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:

    print("=== URBAN AI TRAINED MODEL ===")

    print(f"Modelo: {MODEL_DIR}")
    print(f"Dispositivo: {DEVICE}")
    print(f"Imagen: {INPUT_IMAGE}")

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"No existe el modelo entrenado: {MODEL_DIR}"
        )

    if not INPUT_IMAGE.exists():
        raise FileNotFoundError(
            f"No existe la imagen: {INPUT_IMAGE}"
        )

    model, processor = load_trained_model()

    image = Image.open(
        INPUT_IMAGE
    ).convert("RGB")

    print(
        f"Tamaño imagen: {image.size}"
    )

    mask = predict(
        image,
        model,
        processor,
    )

    print(
        f"Tamaño máscara: {tuple(mask.shape)}"
    )

    proportions = calculate_proportions(
        mask
    )

    print()
    print("=== PROPORCIONES URBAN AI ===")

    for class_name, proportion in proportions.items():
        print(
            f"{class_name:<12}: "
            f"{proportion * 100:.2f}%"
        )

    create_visualization(
        image,
        mask,
        OUTPUT_IMAGE,
    )

    print()
    print("Visualización guardada en:")
    print(OUTPUT_IMAGE)


if __name__ == "__main__":
    main()