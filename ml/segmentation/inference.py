from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image

from ml.segmentation.config import CLASS_NAMES, OUTPUT_DIR
from ml.segmentation.model import load_model
from ml.segmentation.preprocessing import (
    load_image,
    load_processor,
    preprocess_image,
)


# ---------------------------------------------------------------------------
# ADE20K -> Urban AI
# ---------------------------------------------------------------------------

# Estas clases corresponden a categorías que ya vimos en la inferencia
# del checkpoint ADE20K.
#
# El mapeo es un baseline inicial. No representa todavía un modelo
# entrenado específicamente para Urban AI Bucaramanga.

ADE20K_TO_URBAN = {
    "building": "built_up",
    "tree": "vegetation",
    "grass": "vegetation",
    "plant": "vegetation",
    "road": "roads",
}


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


def run_inference(image_path: str | Path):
    """Run semantic segmentation inference on an image."""

    model = load_model()
    processor = load_processor()

    image = load_image(image_path)
    inputs = preprocess_image(image, processor)

    with torch.no_grad():
        outputs = model(**inputs)

    # Convert model output to a mask at the original image resolution.
    predicted_mask = processor.post_process_semantic_segmentation(
        outputs,
        target_sizes=[image.size[::-1]],
    )[0]

    predicted_mask = predicted_mask.to("cpu")

    return image, outputs, predicted_mask, model


def inspect_prediction(
    predicted_mask: torch.Tensor,
    model,
) -> None:
    """Print the ADE20K classes found in the predicted mask."""

    class_ids, counts = torch.unique(
        predicted_mask,
        return_counts=True,
    )

    id2label = model.config.id2label

    print("\n=== CLASES DETECTADAS ===")

    for class_id, count in zip(class_ids, counts):
        class_id_int = class_id.item()

        label = id2label.get(
            class_id_int,
            f"class_{class_id_int}",
        )

        print(
            f"Clase {class_id_int:3d} "
            f"→ {label:<25} "
            f"→ {count.item():>8} píxeles"
        )


# ---------------------------------------------------------------------------
# Urban AI mapping
# ---------------------------------------------------------------------------


def map_to_urban_classes(
    predicted_mask: torch.Tensor,
    model,
) -> np.ndarray:
    """
    Map ADE20K predictions to the four Urban AI classes.

    Classes:
        0 -> vegetation
        1 -> built_up
        2 -> roads
        3 -> other
    """

    mask = predicted_mask.numpy()

    urban_mask = np.full(
        mask.shape,
        fill_value=3,
        dtype=np.uint8,
    )

    id2label = model.config.id2label

    for class_id, label in id2label.items():
        normalized_label = label.lower().strip()

        urban_class = ADE20K_TO_URBAN.get(
            normalized_label
        )

        if urban_class is None:
            continue

        urban_id = next(
            key
            for key, name in CLASS_NAMES.items()
            if name == urban_class
        )

        urban_mask[mask == int(class_id)] = urban_id

    return urban_mask


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def calculate_class_proportions(
    urban_mask: np.ndarray,
) -> dict[str, float]:
    """Calculate pixel proportions for Urban AI classes."""

    total_pixels = urban_mask.size

    if total_pixels == 0:
        return {
            name: 0.0
            for name in CLASS_NAMES.values()
        }

    proportions = {}

    for class_id, class_name in CLASS_NAMES.items():
        count = np.count_nonzero(
            urban_mask == class_id
        )

        proportions[class_name] = (
            count / total_pixels
        )

    return proportions


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------


def create_visualization(
    image: Image.Image,
    urban_mask: np.ndarray,
    output_path: str | Path,
) -> None:
    """Create and save a segmentation overlay."""

    image_array = np.asarray(
        image.convert("RGB")
    ).astype(np.float32)

    # Fixed diagnostic palette for the four project classes.
    palette = np.array(
        [
            [46, 125, 50],    # vegetation
            [180, 80, 60],    # built_up
            [60, 100, 180],   # roads
            [150, 150, 150],  # other
        ],
        dtype=np.float32,
    )

    mask_colors = palette[urban_mask]

    overlay = (
        image_array * 0.55
        + mask_colors * 0.45
    )

    overlay = np.clip(
        overlay,
        0,
        255,
    ).astype(np.uint8)

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    Image.fromarray(overlay).save(
        output_path
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    image_path = Path(
        "data/raw/segmentation/test_urban.png"
    )

    output_path = (
        OUTPUT_DIR / "test_urban_segmentation.png"
    )

    print("Cargando imagen...")
    
    image, outputs, predicted_mask, model = run_inference(
        image_path
    )

    print(f"Imagen: {image.size}")
    print(
        f"Máscara: "
        f"{tuple(predicted_mask.shape)}"
    )

    inspect_prediction(
        predicted_mask,
        model,
    )

    urban_mask = map_to_urban_classes(
        predicted_mask,
        model,
    )

    proportions = calculate_class_proportions(
        urban_mask
    )

    print("\n=== PROPORCIONES URBAN AI ===")

    for class_name, proportion in proportions.items():
        print(
            f"{class_name:<12}: "
            f"{proportion * 100:.2f}%"
        )

    create_visualization(
        image,
        urban_mask,
        output_path,
    )

    print(
        "\nVisualización guardada en:"
    )
    print(output_path)


if __name__ == "__main__":
    main()