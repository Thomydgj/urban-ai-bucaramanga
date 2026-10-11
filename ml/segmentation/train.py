from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, random_split
from transformers import (
    AutoImageProcessor,
    SegformerForSemanticSegmentation,
)

from ml.segmentation.config import (
    DEVICE,
    MODEL_NAME,
    NUM_CLASSES,
)
from ml.segmentation.dataset import (
    IGNORE_INDEX,
    LoveDAUrbanDataset,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42

BATCH_SIZE = 4
NUM_EPOCHS = 5

LEARNING_RATE = 6e-5
WEIGHT_DECAY = 0.01

VAL_RATIO = 0.20

NUM_WORKERS = 0

OUTPUT_DIR = (
    Path(__file__).resolve().parent
    / "outputs"
    / "training"
)

BEST_MODEL_DIR = OUTPUT_DIR / "best_model"

METRICS_PATH = OUTPUT_DIR / "metrics.json"


# ---------------------------------------------------------------------------
# Urban AI labels
# ---------------------------------------------------------------------------

ID2LABEL = {
    0: "vegetation",
    1: "built_up",
    2: "roads",
    3: "other",
}

LABEL2ID = {
    name: index
    for index, name in ID2LABEL.items()
}


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


def set_seed(seed: int = SEED) -> None:
    """Set random seeds for reproducible experiments."""

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------------------------
# Collate function
# ---------------------------------------------------------------------------


def create_collate_fn(processor):
    """
    Create a batch collator that processes RGB images and masks.

    Images are processed with the Hugging Face processor.
    Masks are resized using nearest-neighbor interpolation so that
    categorical labels are not numerically interpolated.
    """

    def collate_fn(batch):
        images, masks = zip(*batch)

        pixel_inputs = processor(
            images=list(images),
            return_tensors="pt",
        )

        target_height = pixel_inputs[
            "pixel_values"
        ].shape[-2]

        target_width = pixel_inputs[
            "pixel_values"
        ].shape[-1]

        resized_masks = []

        for mask in masks:
            mask_image = Image.fromarray(
                mask.numpy().astype(np.uint8),
                mode="L",
            )

            mask_image = mask_image.resize(
                (target_width, target_height),
                Image.Resampling.NEAREST,
            )

            resized_masks.append(
                np.asarray(mask_image, dtype=np.int64)
            )

        labels = torch.tensor(
            np.stack(resized_masks),
            dtype=torch.long,
        )

        pixel_inputs["labels"] = labels

        return pixel_inputs

    return collate_fn


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def update_confusion_matrix(
    confusion_matrix: np.ndarray,
    predictions: torch.Tensor,
    labels: torch.Tensor,
) -> None:
    """Update the confusion matrix while ignoring no-data pixels."""

    predictions = predictions.detach().cpu().numpy()
    labels = labels.detach().cpu().numpy()

    valid = labels != IGNORE_INDEX

    predictions = predictions[valid]
    labels = labels[valid]

    if labels.size == 0:
        return

    indices = (
        labels * NUM_CLASSES
        + predictions
    )

    bincount = np.bincount(
        indices,
        minlength=NUM_CLASSES * NUM_CLASSES,
    )

    confusion_matrix += bincount.reshape(
        NUM_CLASSES,
        NUM_CLASSES,
    )


def calculate_metrics(
    confusion_matrix: np.ndarray,
) -> dict[str, object]:
    """Calculate IoU, Dice and mean metrics."""

    iou = {}
    dice = {}

    for class_id, class_name in ID2LABEL.items():

        true_positive = confusion_matrix[
            class_id,
            class_id,
        ]

        false_positive = (
            confusion_matrix[:, class_id].sum()
            - true_positive
        )

        false_negative = (
            confusion_matrix[class_id, :].sum()
            - true_positive
        )

        union = (
            true_positive
            + false_positive
            + false_negative
        )

        denominator_dice = (
            2 * true_positive
            + false_positive
            + false_negative
        )

        if union > 0:
            iou_value = (
                true_positive / union
            )
        else:
            iou_value = float("nan")

        if denominator_dice > 0:
            dice_value = (
                2 * true_positive
                / denominator_dice
            )
        else:
            dice_value = float("nan")

        iou[class_name] = float(iou_value)
        dice[class_name] = float(dice_value)

    valid_iou = [
        value
        for value in iou.values()
        if not np.isnan(value)
    ]

    valid_dice = [
        value
        for value in dice.values()
        if not np.isnan(value)
    ]

    mean_iou = (
        float(np.mean(valid_iou))
        if valid_iou
        else 0.0
    )

    mean_dice = (
        float(np.mean(valid_dice))
        if valid_dice
        else 0.0
    )

    return {
        "iou": iou,
        "dice": dice,
        "mean_iou": mean_iou,
        "mean_dice": mean_dice,
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(
    model,
    dataloader,
    device,
) -> tuple[float, dict[str, object]]:

    model.eval()

    total_loss = 0.0
    batches = 0

    confusion_matrix = np.zeros(
        (
            NUM_CLASSES,
            NUM_CLASSES,
        ),
        dtype=np.int64,
    )

    with torch.no_grad():

        for batch in dataloader:

            batch = {
                key: value.to(device)
                for key, value in batch.items()
            }

            outputs = model(**batch)

            loss = outputs.loss

            total_loss += loss.item()
            batches += 1

            logits = outputs.logits

            logits = torch.nn.functional.interpolate(
                logits,
                size=batch["labels"].shape[-2:],
                mode="bilinear",
                align_corners=False,
            )

            predictions = logits.argmax(dim=1)

            update_confusion_matrix(
                confusion_matrix,
                predictions,
                batch["labels"],
            )

    average_loss = (
        total_loss / batches
        if batches > 0
        else 0.0
    )

    metrics = calculate_metrics(
        confusion_matrix
    )

    return average_loss, metrics


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def train() -> None:
    """Train SegFormer for Urban AI semantic segmentation."""

    set_seed()

    print("=== URBAN AI SEGMENTATION TRAINING ===")
    print(f"Device: {DEVICE}")
    print(f"Model: {MODEL_NAME}")
    print(f"Classes: {NUM_CLASSES}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Epochs: {NUM_EPOCHS}")
    print(f"Learning rate: {LEARNING_RATE}")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Dataset
    # ---------------------------------------------------------------

    dataset = LoveDAUrbanDataset()

    validation_size = int(
        len(dataset) * VAL_RATIO
    )

    training_size = (
        len(dataset) - validation_size
    )

    train_dataset, validation_dataset = random_split(
        dataset,
        [
            training_size,
            validation_size,
        ],
        generator=torch.Generator().manual_seed(
            SEED
        ),
    )

    print()
    print("=== DATASET ===")
    print(f"Total: {len(dataset)}")
    print(f"Train: {len(train_dataset)}")
    print(f"Validation: {len(validation_dataset)}")

    # ---------------------------------------------------------------
    # Processor
    # ---------------------------------------------------------------

    processor = AutoImageProcessor.from_pretrained(
        MODEL_NAME
    )

    collate_fn = create_collate_fn(
        processor
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
        collate_fn=collate_fn,
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
        collate_fn=collate_fn,
    )

    # ---------------------------------------------------------------
    # Model
    # ---------------------------------------------------------------

    model = (
        SegformerForSemanticSegmentation
        .from_pretrained(
            MODEL_NAME,
            num_labels=NUM_CLASSES,
            id2label=ID2LABEL,
            label2id=LABEL2ID,
            ignore_mismatched_sizes=True,
        )
    )

    model.to(DEVICE)

    # ---------------------------------------------------------------
    # Optimizer
    # ---------------------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    scaler = torch.amp.GradScaler(
        "cuda",
        enabled=(
            DEVICE.type == "cuda"
        ),
    )

    # ---------------------------------------------------------------
    # Training loop
    # ---------------------------------------------------------------

    best_mean_iou = -1.0

    history = []

    for epoch in range(
        1,
        NUM_EPOCHS + 1,
    ):

        model.train()

        training_loss = 0.0
        training_batches = 0

        for batch_index, batch in enumerate(
            train_loader,
            start=1,
        ):

            batch = {
                key: value.to(DEVICE)
                for key, value in batch.items()
            }

            optimizer.zero_grad(
                set_to_none=True
            )

            with torch.amp.autocast(
                device_type=DEVICE.type,
                enabled=(
                    DEVICE.type == "cuda"
                ),
            ):

                outputs = model(
                    **batch
                )

                loss = outputs.loss

            scaler.scale(loss).backward()

            scaler.step(optimizer)

            scaler.update()

            training_loss += loss.item()
            training_batches += 1

            if batch_index % 20 == 0:
                print(
                    f"Epoch {epoch}/{NUM_EPOCHS} "
                    f"| Batch {batch_index}/{len(train_loader)} "
                    f"| Loss {loss.item():.4f}"
                )

        average_training_loss = (
            training_loss / training_batches
        )

        validation_loss, metrics = validate(
            model,
            validation_loader,
            DEVICE,
        )

        mean_iou = metrics["mean_iou"]
        mean_dice = metrics["mean_dice"]

        print()
        print(
            f"Epoch {epoch}/{NUM_EPOCHS} completada"
        )
        print(
            f"Train loss: {average_training_loss:.4f}"
        )
        print(
            f"Validation loss: {validation_loss:.4f}"
        )
        print(
            f"mIoU: {mean_iou:.4f}"
        )
        print(
            f"mDice: {mean_dice:.4f}"
        )

        for class_name in ID2LABEL.values():

            print(
                f"  {class_name:<12} "
                f"IoU: "
                f"{metrics['iou'][class_name]:.4f} "
                f"| Dice: "
                f"{metrics['dice'][class_name]:.4f}"
            )

        epoch_result = {
            "epoch": epoch,
            "train_loss": average_training_loss,
            "validation_loss": validation_loss,
            "metrics": metrics,
        }

        history.append(
            epoch_result
        )

        # -----------------------------------------------------------
        # Save best model
        # -----------------------------------------------------------

        if mean_iou > best_mean_iou:

            best_mean_iou = mean_iou

            BEST_MODEL_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            model.save_pretrained(
                BEST_MODEL_DIR
            )

            processor.save_pretrained(
                BEST_MODEL_DIR
            )

            print()
            print(
                "Nuevo mejor modelo guardado."
            )
            print(
                f"mIoU: {best_mean_iou:.4f}"
            )
            print(
                f"Ruta: {BEST_MODEL_DIR}"
            )

    # ---------------------------------------------------------------
    # Save training history
    # ---------------------------------------------------------------

    with METRICS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            {
                "model": MODEL_NAME,
                "num_classes": NUM_CLASSES,
                "seed": SEED,
                "batch_size": BATCH_SIZE,
                "epochs": NUM_EPOCHS,
                "learning_rate": LEARNING_RATE,
                "weight_decay": WEIGHT_DECAY,
                "train_samples": training_size,
                "validation_samples": validation_size,
                "best_mean_iou": best_mean_iou,
                "history": history,
            },
            file,
            indent=2,
        )

    print()
    print("=== ENTRENAMIENTO FINALIZADO ===")
    print(
        f"Mejor mIoU: {best_mean_iou:.4f}"
    )
    print(
        f"Métricas: {METRICS_PATH}"
    )
    print(
        f"Mejor modelo: {BEST_MODEL_DIR}"
    )


if __name__ == "__main__":
    train()