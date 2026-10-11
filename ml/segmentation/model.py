from __future__ import annotations

import torch
from transformers import SegformerForSemanticSegmentation

from ml.segmentation.config import DEVICE, MODEL_NAME


def load_model() -> SegformerForSemanticSegmentation:
    """Load the pretrained SegFormer semantic segmentation model."""

    model = SegformerForSemanticSegmentation.from_pretrained(
        MODEL_NAME
    )

    model.to(DEVICE)
    model.eval()

    return model


def get_model_device(model: torch.nn.Module) -> torch.device:
    """Return the device where the model is loaded."""

    return next(model.parameters()).device