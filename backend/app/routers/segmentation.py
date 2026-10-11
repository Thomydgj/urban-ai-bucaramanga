from __future__ import annotations

from io import BytesIO

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)
from PIL import (
    Image,
    UnidentifiedImageError,
)

from ..services.segmentation_service import (
    get_segmentation_service,
)


router = APIRouter(
    prefix="/api",
    tags=["Segmentation"],
)


@router.post("/segmentation/predict")
async def predict_segmentation(
    file: UploadFile = File(...),
):
    """
    Ejecuta la segmentación semántica de una imagen urbana.

    Clases:
        0 → vegetation
        1 → built_up
        2 → roads
        3 → other
    """

    # -----------------------------------------------------
    # Validar tipo de archivo
    # -----------------------------------------------------

    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="El archivo no tiene tipo MIME.",
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen.",
        )

    # -----------------------------------------------------
    # Leer archivo
    # -----------------------------------------------------

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="El archivo está vacío.",
            )

        # -------------------------------------------------
        # Abrir imagen
        # -------------------------------------------------

        try:
            image = Image.open(
                BytesIO(contents)
            )

            image.load()

        except (
            UnidentifiedImageError,
            OSError,
        ) as exc:

            raise HTTPException(
                status_code=400,
                detail="No fue posible leer la imagen.",
            ) from exc

        # -------------------------------------------------
        # Obtener servicio de segmentación
        # -------------------------------------------------

        service = get_segmentation_service()

        # -------------------------------------------------
        # Ejecutar análisis
        # -------------------------------------------------

        result = service.analyze(
            image
        )

        # -------------------------------------------------
        # Respuesta
        # -------------------------------------------------

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            **result,
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error ejecutando segmentación: "
                f"{exc}"
            ),
        ) from exc