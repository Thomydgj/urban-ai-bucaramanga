
from __future__ import annotations

from PIL import Image, ImageFilter


def prepare_mask(
    mask: Image.Image,
    target_size: tuple[int, int],
) -> Image.Image:
    """
    Normaliza una máscara para inpainting.

    Blanco (255): zona editable.
    Negro (0): zona que debe conservarse.
    """
    mask = mask.convert("L")

    if mask.size != target_size:
        mask = mask.resize(target_size, Image.Resampling.NEAREST)

    # Evita valores intermedios inesperados en la máscara de entrada.
    mask = mask.point(lambda value: 255 if value >= 128 else 0)

    if mask.getbbox() is None:
        raise ValueError(
            "La máscara está vacía. Pinta de blanco la zona que deseas editar."
        )

    return mask


def composite_result(
    original: Image.Image,
    generated: Image.Image,
    mask: Image.Image,
    feather_radius: float = 0.0,
) -> Image.Image:
    """
    Combina el resultado generado con la imagen original.

    Fuera de la máscara, los píxeles originales se conservan exactamente
    cuando feather_radius=0. Un feather positivo suaviza los bordes,
    pero permite pequeños cambios fuera de la máscara.
    """
    original = original.convert("RGB")
    generated = generated.convert("RGB")

    if generated.size != original.size:
        generated = generated.resize(
            original.size,
            Image.Resampling.LANCZOS,
        )

    mask = prepare_mask(mask, original.size)

    if feather_radius > 0:
        mask = mask.filter(
            ImageFilter.GaussianBlur(radius=feather_radius)
        )

    return Image.composite(generated, original, mask)
