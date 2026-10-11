
from __future__ import annotations

import base64
import logging
import os
import uuid
from io import BytesIO
from pathlib import Path

from openai import APIError, OpenAI
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Raíz del proyecto: urban-ai-bucaramanga/
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "generated"

# Se puede cambiar desde el archivo .env.
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
MAX_IMAGE_PIXELS = 20_000_000

_client: OpenAI | None = None


def get_device() -> str:
    """Mantiene compatibilidad con el endpoint existente."""
    return "openai_api"


def _get_client() -> OpenAI:
    """Crea el cliente de OpenAI cuando se necesita."""
    global _client

    if _client is not None:
        return _client

    try:
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env", override=False)
    except ImportError:
        pass

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Falta OPENAI_API_KEY. Configúrala en el archivo .env "
            "de la raíz del proyecto."
        )

    _client = OpenAI()
    return _client


def prepare_image(image: Image.Image) -> Image.Image:
    """Corrige orientación y convierte la imagen a RGB."""
    image = ImageOps.exif_transpose(image).convert("RGB")

    if image.width < 64 or image.height < 64:
        raise ValueError(
            "La imagen debe medir al menos 64 × 64 píxeles."
        )

    if image.width * image.height > MAX_IMAGE_PIXELS:
        raise ValueError(
            "La imagen tiene demasiados píxeles. "
            "Reduce su resolución antes de subirla."
        )

    return image


def _image_to_png_bytes(image: Image.Image) -> BytesIO:
    """Convierte la imagen a un archivo PNG en memoria."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = "urban_ai_input.png"
    return buffer


def generate_image(
    image: Image.Image,
    prompt: str,
    negative_prompt: str = "",
    strength: float = 0.40,
    steps: int = 20,
    guidance_scale: float = 7.0,
    seed: int | None = None,
) -> dict:
    """
    Edita una imagen con OpenAI para producir una propuesta urbana conceptual.

    strength, steps, guidance_scale y seed se conservan para mantener
    compatibilidad con el endpoint anterior. No todos estos parámetros
    tienen un equivalente directo en la API de imágenes de OpenAI.
    """
    if not prompt or not prompt.strip():
        raise ValueError("El prompt no puede estar vacío.")

    # Validar los parámetros heredados del generador anterior.
    if not 0.1 <= strength <= 0.9:
        raise ValueError("strength debe estar entre 0.1 y 0.9.")

    if not 1 <= steps <= 40:
        raise ValueError("steps debe estar entre 1 y 40.")

    if not 1.0 <= guidance_scale <= 12.0:
        raise ValueError(
            "guidance_scale debe estar entre 1 y 12."
        )

    if seed is not None and not 0 <= seed <= 2**32 - 1:
        raise ValueError(
            "seed debe ser un entero entre 0 y 4294967295."
        )

    input_image = prepare_image(image)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"urban_ai_{uuid.uuid4().hex}.png"

    full_prompt = prompt.strip()

    if negative_prompt and negative_prompt.strip():
        full_prompt += (
            "\n\nEvita los siguientes elementos o resultados: "
            + negative_prompt.strip()
            + "."
        )

    try:
        client = _get_client()

        response = client.images.edit(
            model=IMAGE_MODEL,
            image=_image_to_png_bytes(input_image),
            prompt=full_prompt,
            input_fidelity="high",
            quality="medium",
            size="auto",
        )

        if not response.data or not response.data[0].b64_json:
            raise RuntimeError(
                "OpenAI no devolvió datos de imagen."
            )

        image_bytes = base64.b64decode(
            response.data[0].b64_json
        )

        with Image.open(BytesIO(image_bytes)) as generated_image:
            generated = generated_image.convert("RGB")
            generated.save(output_path, format="PNG")

        logger.info(
            "Imagen conceptual guardada en %s",
            output_path,
        )

        return {
            "filename": output_path.name,
            "output_path": str(output_path),
            "width": generated.width,
            "height": generated.height,
            "model": IMAGE_MODEL,
            "device": "openai_api",
            "provider": "OpenAI",
            "input_fidelity": "high",
            "quality": "medium",
            "seed": None,
            "disclaimer": (
                "Visualización conceptual generada mediante IA. "
                "No representa una simulación física validada ni "
                "garantiza conservar exactamente las edificaciones, "
                "la geometría, las dimensiones o la viabilidad "
                "urbanística de la escena original."
            ),
        }

    except APIError:
        logger.exception(
            "La API de OpenAI rechazó o no pudo procesar la solicitud."
        )
        output_path.unlink(missing_ok=True)
        raise

    except Exception:
        logger.exception(
            "Falló la generación de imagen conceptual."
        )
        output_path.unlink(missing_ok=True)
        raise
