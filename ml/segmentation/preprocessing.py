from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image
from transformers import AutoImageProcessor

from ml.segmentation.config import DEVICE, MODEL_NAME


def load_image(image_path: str | Path) -> Image.Image:
    """Load an RGB image from disk."""

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró la imagen: {path}"
        )

    image = Image.open(path).convert("RGB")

    return image


def load_processor() -> AutoImageProcessor:
    """Load the image processor associated with the model."""

    return AutoImageProcessor.from_pretrained(
        MODEL_NAME
    )


def preprocess_image(
    image: Image.Image,
    processor: AutoImageProcessor,
) -> dict[str, torch.Tensor]:
    """Convert an image into tensors suitable for SegFormer."""

    inputs = processor(
        images=image,
        return_tensors="pt",
    )

    return {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }