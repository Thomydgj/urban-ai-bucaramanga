from __future__ import annotations

import base64
from io import BytesIO
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


# =========================================================
# CONFIGURACIÓN
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_DIR = (
    PROJECT_ROOT
    / "ml"
    / "segmentation"
    / "outputs"
    / "training"
    / "best_model"
)


CLASS_NAMES = {
    VEGETATION: "vegetation",
    BUILT_UP: "built_up",
    ROADS: "roads",
    OTHER: "other",
}


# =========================================================
# PALETA
# =========================================================

PALETTE = np.array(
    [
        [46, 125, 50],    # vegetation
        [180, 80, 60],    # built_up
        [60, 100, 180],   # roads
        [150, 150, 150],  # other
    ],
    dtype=np.float32,
)


# =========================================================
# SERVICIO
# =========================================================

class SegmentationService:
    """Service responsible for Urban AI image segmentation."""

    def __init__(self) -> None:

        if not MODEL_DIR.exists():
            raise FileNotFoundError(
                f"No existe el modelo entrenado: "
                f"{MODEL_DIR}"
            )

        self.device = DEVICE

        self.processor = (
            AutoImageProcessor.from_pretrained(
                MODEL_DIR
            )
        )

        self.model = (
            SegformerForSemanticSegmentation
            .from_pretrained(
                MODEL_DIR
            )
        )

        self.model.to(self.device)
        self.model.eval()

    # =====================================================
    # PREDICCIÓN
    # =====================================================

    def predict(
        self,
        image: Image.Image,
    ) -> torch.Tensor:
        """Generate a full-resolution segmentation mask."""

        inputs = self.processor(
            images=image,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():

            outputs = self.model(
                **inputs
            )

        mask = (
            self.processor
            .post_process_semantic_segmentation(
                outputs,
                target_sizes=[
                    image.size[::-1]
                ],
            )[0]
        )

        return mask.cpu()

    # =====================================================
    # PROPORCIONES
    # =====================================================

    def calculate_proportions(
        self,
        mask: torch.Tensor,
    ) -> dict[str, float]:
        """Calculate pixel proportions by class."""

        mask_array = mask.numpy()

        valid_mask = (
            mask_array != IGNORE_INDEX
        )

        total_pixels = int(
            np.count_nonzero(
                valid_mask
            )
        )

        if total_pixels == 0:

            return {
                class_name: 0.0
                for class_name
                in CLASS_NAMES.values()
            }

        proportions = {}

        for class_id, class_name in CLASS_NAMES.items():

            pixels = int(
                np.count_nonzero(
                    (mask_array == class_id)
                    & valid_mask
                )
            )

            proportions[class_name] = (
                pixels / total_pixels
            )

        return proportions

    # =====================================================
    # VISUALIZACIÓN
    # =====================================================

    def create_overlay(
        self,
        image: Image.Image,
        mask: torch.Tensor,
    ) -> Image.Image:
        """Create segmentation overlay."""

        image_array = np.asarray(
            image.convert("RGB")
        ).astype(np.float32)

        mask_array = mask.numpy()

        mask_colors = np.zeros_like(
            image_array
        )

        for class_id, color in enumerate(
            PALETTE
        ):

            mask_colors[
                mask_array == class_id
            ] = color

        valid = (
            mask_array != IGNORE_INDEX
        )

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

    # =====================================================
    # PROCESAMIENTO COMPLETO
    # =====================================================

    def analyze(
        self,
        image: Image.Image,
    ) -> dict:
        """Run complete segmentation analysis."""

        image = image.convert("RGB")

        original_width, original_height = (
            image.size
        )

        mask = self.predict(
            image
        )

        proportions = (
            self.calculate_proportions(
                mask
            )
        )

        overlay = self.create_overlay(
            image,
            mask,
        )

        buffer = BytesIO()

        overlay.save(
            buffer,
            format="PNG",
        )

        encoded_image = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return {
            "width": original_width,
            "height": original_height,
            "proportions": proportions,
            "segmentation_image": (
                f"data:image/png;base64,"
                f"{encoded_image}"
            ),
            "model": {
                "name": "SegFormer B0",
                "checkpoint": str(
                    MODEL_DIR
                ),
                "device": str(
                    self.device
                ),
                "classes": list(
                    CLASS_NAMES.values()
                ),
                "training_dataset": (
                    "LoveDA Urban"
                ),
                "experimental_scope": (
                    "El modelo fue "
                    "validado en LoveDA "
                    "Urban. Su uso sobre "
                    "imágenes aéreas "
                    "oblicuas de "
                    "Bucaramanga es "
                    "experimental debido "
                    "a diferencia de dominio."
                ),
            },
        }


# =========================================================
# SINGLETON LAZY
# =========================================================

_service: SegmentationService | None = None


def get_segmentation_service() -> SegmentationService:
    """Return the shared segmentation service."""

    global _service

    if _service is None:
        _service = SegmentationService()

    return _service