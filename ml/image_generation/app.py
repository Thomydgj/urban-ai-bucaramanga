from __future__ import annotations

import io
import logging
from pathlib import Path

import torch
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError

from engine import OUTPUT_DIR, generate_image, get_device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Urban AI Bucaramanga - Image Generation",
    description=(
        "Generación de visualizaciones conceptuales urbanas mediante "
        "image-to-image. No utiliza inpainting ni máscaras."
    ),
    version="1.1.0",
)

# Permite que el frontend local consuma esta API desde cualquiera de los
# dos orígenes habituales de Vite. No usar "*" junto con credenciales.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


@app.get("/")
def root():
    return {
        "service": "Urban AI Bucaramanga - Image Generation",
        "status": "available",
        "mode": "image-to-image",
        "uses_mask": False,
        "device": get_device(),
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": get_device(),
        "output_directory_exists": OUTPUT_DIR.exists(),
    }


@app.post("/api/image-generation/generate")
async def generate(
    request: Request,
    file: UploadFile = File(..., description="Imagen urbana JPG, PNG o WEBP"),
    prompt: str = Form(..., min_length=5, max_length=2000),
    negative_prompt: str = Form(
        default=(
            "cartoon, illustration, fantasy architecture, distorted buildings, "
            "blurry, low quality, text, watermark"
        ),
        max_length=2000,
    ),
    strength: float = Form(default=0.40, ge=0.1, le=0.9),
    steps: int = Form(default=20, ge=1, le=40),
    guidance_scale: float = Form(default=7.0, ge=1.0, le=12.0),
    seed: int | None = Form(default=None, ge=0, le=4294967295),
):
    """Genera una imagen conceptual y devuelve una URL absoluta accesible."""
    if not prompt.strip():
        raise HTTPException(status_code=422, detail="El prompt no puede estar vacío.")

    try:
        contents = await file.read(MAX_UPLOAD_BYTES + 1)

        if not contents:
            raise HTTPException(status_code=422, detail="El archivo está vacío.")

        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="La imagen supera el límite de 15 MB.",
            )

        try:
            with Image.open(io.BytesIO(contents)) as source:
                image_format = source.format

                if image_format not in ALLOWED_FORMATS:
                    raise HTTPException(
                        status_code=415,
                        detail="Formato no admitido. Usa JPG, PNG o WEBP.",
                    )

                source.verify()

            # Reabrir después de verify() y crear una imagen independiente.
            with Image.open(io.BytesIO(contents)) as source:
                image = source.copy()

        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=415,
                detail="El archivo no parece ser una imagen válida.",
            ) from exc

        result = generate_image(
            image=image,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            steps=steps,
            guidance_scale=guidance_scale,
            seed=seed,
        )

        filename = result.get("filename")
        if not filename:
            raise HTTPException(
                status_code=500,
                detail="El generador no devolvió el nombre del archivo generado.",
            )

        # Construir la URL con la base real de esta petición (puerto 8001).
        image_url = str(
            request.url_for("get_generated_image", filename=filename)
        )

        return {
            **result,
            "status": "success",
            "mode": "image-to-image",
            "uses_mask": False,
            "image_url": image_url,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except torch.cuda.OutOfMemoryError as exc:
        logger.exception("Memoria GPU insuficiente.")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise HTTPException(
            status_code=503,
            detail=(
                "La GPU no tiene memoria suficiente para esta generación. "
                "Intenta nuevamente con una imagen más pequeña."
            ),
        ) from exc

    except Exception as exc:
        logger.exception("Error inesperado en el endpoint de generación.")
        raise HTTPException(
            status_code=500,
            detail=(
                "Falló la generación. Revisa la consola del servicio "
                "para ver el error completo."
            ),
        ) from exc

    finally:
        await file.close()


@app.get("/api/image-generation/results/{filename}", name="get_generated_image")
def get_generated_image(filename: str):
    """Sirve únicamente archivos PNG generados en el directorio de salida."""
    if (
        not filename.endswith(".png")
        or Path(filename).name != filename
        or not filename.startswith("urban_ai_")
    ):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    image_path = OUTPUT_DIR / filename

    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="No se encontró la imagen.")

    # No pasar filename: así se sirve como imagen en línea y no como descarga.
    return FileResponse(
        path=image_path,
        media_type="image/png",
        headers={"Cache-Control": "no-cache"},
    )
