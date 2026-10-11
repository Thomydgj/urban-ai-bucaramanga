from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOVEDA_URBAN_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "loveda"
    / "train"
    / "Train"
    / "Urban"
)

IMAGE_DIR = LOVEDA_URBAN_DIR / "images_png"
MASK_DIR = LOVEDA_URBAN_DIR / "masks_png"


# ---------------------------------------------------------------------------
# Urban AI classes
# ---------------------------------------------------------------------------

VEGETATION = 0
BUILT_UP = 1
ROADS = 2
OTHER = 3

IGNORE_INDEX = 255


# ---------------------------------------------------------------------------
# LoveDA -> Urban AI
# ---------------------------------------------------------------------------

LOVE_DA_TO_URBAN = {
    0: IGNORE_INDEX,  # no-data
    1: OTHER,         # background
    2: BUILT_UP,      # building
    3: ROADS,         # road
    4: OTHER,         # water
    5: OTHER,         # barren
    6: VEGETATION,    # forest
    7: VEGETATION,    # agriculture
}


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class LoveDAUrbanDataset(Dataset):
    """
    LoveDA Urban dataset adapted to the Urban AI four-class taxonomy.

    Urban AI classes:

        0 -> vegetation
        1 -> built_up
        2 -> roads
        3 -> other

    LoveDA no-data pixels are mapped to IGNORE_INDEX (255).
    """

    def __init__(
        self,
        image_dir: Path = IMAGE_DIR,
        mask_dir: Path = MASK_DIR,
    ) -> None:

        self.image_dir = Path(image_dir)
        self.mask_dir = Path(mask_dir)

        self.image_paths = sorted(
            self.image_dir.glob("*.png")
        )

        if not self.image_paths:
            raise RuntimeError(
                f"No se encontraron imágenes en: "
                f"{self.image_dir}"
            )

        self.mask_paths = []

        for image_path in self.image_paths:
            mask_path = self.mask_dir / image_path.name

            if not mask_path.exists():
                raise FileNotFoundError(
                    f"No existe la máscara correspondiente a "
                    f"{image_path.name}: {mask_path}"
                )

            self.mask_paths.append(mask_path)

        if len(self.image_paths) != len(self.mask_paths):
            raise RuntimeError(
                "La cantidad de imágenes y máscaras no coincide."
            )

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(
        self,
        index: int,
    ) -> tuple[Image.Image, torch.Tensor]:

        image_path = self.image_paths[index]
        mask_path = self.mask_paths[index]

        image = Image.open(
            image_path
        ).convert("RGB")

        mask = np.asarray(
            Image.open(mask_path)
        )

        urban_mask = np.full(
            mask.shape,
            fill_value=IGNORE_INDEX,
            dtype=np.uint8,
        )

        for loveda_label, urban_label in LOVE_DA_TO_URBAN.items():
            urban_mask[
                mask == loveda_label
            ] = urban_label

        urban_mask = torch.from_numpy(
            urban_mask.astype(np.int64)
        )

        return image, urban_mask

def save_sample_visualization(
    dataset: LoveDAUrbanDataset,
    index: int = 0,
    output_path: str | Path = "ml/segmentation/outputs/loveda_sample.png",
) -> None:
    """Save an RGB visualization of one transformed LoveDA sample."""

    import numpy as np

    image, mask = dataset[index]

    image_array = np.asarray(image.convert("RGB"))

    mask_array = mask.numpy()

    palette = np.array(
        [
            [46, 125, 50],    # vegetation
            [180, 80, 60],    # built_up
            [60, 100, 180],   # roads
            [150, 150, 150],  # other
        ],
        dtype=np.uint8,
    )

    mask_colors = palette[mask_array]

    overlay = (
        image_array.astype(np.float32) * 0.55
        + mask_colors.astype(np.float32) * 0.45
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

    Image.fromarray(overlay).save(output_path)

    print(
        f"Visualización guardada en: {output_path}"
    )