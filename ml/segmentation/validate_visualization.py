from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import random_split
from transformers import (
    AutoImageProcessor,
    SegformerForSemanticSegmentation,
)

from ml.segmentation.config import DEVICE
from ml.segmentation.dataset import (
    LoveDAUrbanDataset,
    IGNORE_INDEX,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42

VAL_RATIO = 0.20

VALIDATION_INDEX = 0

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    PROJECT_ROOT
    / "ml"
    / "segmentation"
    / "outputs"
    / "training"
    / "best_model"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "segmentation"
    / "outputs"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "loveda_validation_sample.png"
)


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

CLASS_NAMES = {
    0: "vegetation",
    1: "built_up",
    2: "roads",
    3: "other",
}

PALETTE = np.array(
    [
        [46, 125, 50],    # vegetation
        [180, 80, 60],    # built_up
        [60, 100, 180],   # roads
        [150, 150, 150],  # other
    ],
    dtype=np.uint8,
)


# ---------------------------------------------------------------------------
# Dataset split
# ---------------------------------------------------------------------------


def get_validation_dataset() -> tuple[LoveDAUrbanDataset, list[int]]:
    """
    Recreate exactly the validation split used during training.
    """

    dataset = LoveDAUrbanDataset()

    validation_size = int(
        len(dataset) * VAL_RATIO
    )

    training_size = (
        len(dataset) - validation_size
    )

    _, validation_dataset = random_split(
        dataset,
        [
            training_size,
            validation_size,
        ],
        generator=torch.Generator().manual_seed(
            SEED
        ),
    )

    return dataset, validation_dataset.indices


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


def load_model():
    """Load the best fine-tuned Urban AI model."""

    model = SegformerForSemanticSegmentation.from_pretrained(
        MODEL_DIR
    )

    processor = AutoImageProcessor.from_pretrained(
        MODEL_DIR
    )

    model.to(DEVICE)
    model.eval()

    return model, processor


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


def predict(
    image: Image.Image,
    model,
    processor,
) -> torch.Tensor:
    """Generate a full-resolution semantic segmentation mask."""

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

    prediction = processor.post_process_semantic_segmentation(
        outputs,
        target_sizes=[image.size[::-1]],
    )[0]

    return prediction.cpu()


# ---------------------------------------------------------------------------
# Color masks
# ---------------------------------------------------------------------------


def colorize_mask(
    mask: np.ndarray,
) -> Image.Image:
    """Convert a class mask into an RGB visualization."""

    height, width = mask.shape

    colored = np.zeros(
        (height, width, 3),
        dtype=np.uint8,
    )

    for class_id, color in enumerate(PALETTE):
        colored[
            mask == class_id
        ] = color

    colored[
        mask == IGNORE_INDEX
    ] = [0, 0, 0]

    return Image.fromarray(
        colored,
        mode="RGB",
    )


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------


def create_overlay(
    image: Image.Image,
    mask: np.ndarray,
) -> Image.Image:
    """Overlay a segmentation mask over the original image."""

    image_array = np.asarray(
        image.convert("RGB")
    ).astype(np.float32)

    mask_colors = np.zeros_like(
        image_array
    )

    for class_id, color in enumerate(PALETTE):
        mask_colors[
            mask == class_id
        ] = color

    valid = mask != IGNORE_INDEX

    overlay = image_array.copy()

    overlay[valid] = (
        image_array[valid] * 0.55
        + mask_colors[valid] * 0.45
    )

    return Image.fromarray(
        np.clip(
            overlay,
            0,
            255,
        ).astype(np.uint8),
        mode="RGB",
    )


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def calculate_statistics(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
) -> None:
    """Print class proportions for prediction and ground truth."""

    valid = ground_truth != IGNORE_INDEX

    print()
    print("=== PROPORCIONES DE LA MUESTRA ===")

    for class_id, class_name in CLASS_NAMES.items():

        gt_pixels = np.count_nonzero(
            (ground_truth == class_id)
            & valid
        )

        predicted_pixels = np.count_nonzero(
            (prediction == class_id)
            & valid
        )

        total_pixels = np.count_nonzero(
            valid
        )

        gt_percentage = (
            gt_pixels / total_pixels * 100
            if total_pixels
            else 0.0
        )

        predicted_percentage = (
            predicted_pixels / total_pixels * 100
            if total_pixels
            else 0.0
        )

        print(
            f"{class_name:<12} "
            f"GT: {gt_percentage:6.2f}% "
            f"| Pred: {predicted_percentage:6.2f}%"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:

    print("=== LOVeDA VALIDATION VISUALIZATION ===")
    print(f"Device: {DEVICE}")
    print(f"Modelo: {MODEL_DIR}")

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"No existe el modelo: {MODEL_DIR}"
        )

    dataset, validation_indices = (
        get_validation_dataset()
    )

    if VALIDATION_INDEX >= len(validation_indices):
        raise IndexError(
            "VALIDATION_INDEX está fuera del rango "
            "del conjunto de validación."
        )

    original_index = validation_indices[
        VALIDATION_INDEX
    ]

    image_path = dataset.image_paths[
        original_index
    ]

    mask_path = dataset.mask_paths[
        original_index
    ]

    print()
    print("=== MUESTRA ===")
    print(
        f"Índice global: {original_index}"
    )
    print(
        f"Índice validación: "
        f"{VALIDATION_INDEX}"
    )
    print(
        f"Imagen: {image_path.name}"
    )
    print(
        f"Máscara: {mask_path.name}"
    )

    image, ground_truth_tensor = dataset[
        original_index
    ]

    ground_truth = (
        ground_truth_tensor.numpy()
    )

    model, processor = load_model()

    prediction_tensor = predict(
        image,
        model,
        processor,
    )

    prediction = prediction_tensor.numpy()

    print()
    print(
        f"Tamaño imagen: {image.size}"
    )
    print(
        f"Tamaño máscara GT: "
        f"{ground_truth.shape}"
    )
    print(
        f"Tamaño predicción: "
        f"{prediction.shape}"
    )

    calculate_statistics(
        prediction,
        ground_truth,
    )

    # ---------------------------------------------------------------
    # Generate visualizations
    # ---------------------------------------------------------------

    ground_truth_image = colorize_mask(
        ground_truth
    )

    prediction_image = colorize_mask(
        prediction
    )

    overlay_image = create_overlay(
        image,
        prediction,
    )

    width, height = image.size

    canvas = Image.new(
        "RGB",
        (
            width * 2,
            height * 2,
        ),
        "white",
    )

    canvas.paste(
        image,
        (0, 0),
    )

    canvas.paste(
        ground_truth_image,
        (width, 0),
    )

    canvas.paste(
        prediction_image,
        (0, height),
    )

    canvas.paste(
        overlay_image,
        (width, height),
    )

    draw = ImageDraw.Draw(canvas)

    draw.rectangle(
        (0, 0, width, 35),
        fill="black",
    )

    draw.rectangle(
        (width, 0, width * 2, 35),
        fill="black",
    )

    draw.rectangle(
        (0, height, width, height + 35),
        fill="black",
    )

    draw.rectangle(
        (
            width,
            height,
            width * 2,
            height + 35,
        ),
        fill="black",
    )

    draw.text(
        (10, 10),
        "Original",
        fill="white",
    )

    draw.text(
        (width + 10, 10),
        "Ground Truth",
        fill="white",
    )

    draw.text(
        (10, height + 10),
        "Predicción",
        fill="white",
    )

    draw.text(
        (
            width + 10,
            height + 10,
        ),
        "Predicción + imagen",
        fill="white",
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    canvas.save(
        OUTPUT_PATH
    )

    print()
    print(
        "Visualización guardada en:"
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()