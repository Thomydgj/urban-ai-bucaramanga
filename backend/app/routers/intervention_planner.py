
import base64
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from openai import APIError, OpenAI

router = APIRouter(
    prefix="/api/intervention-planner",
    tags=["intervention-planner"],
)

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 10 * 1024 * 1024

ALLOWED_TYPES = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
}

DEFAULT_MODEL = "gpt-4.1-mini"


def parse_optional_json(
    raw: str | None,
    field_name: str,
) -> Any:
    """Convierte un campo JSON opcional enviado desde el formulario."""
    if not raw or not raw.strip():
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"El campo '{field_name}' no contiene "
                "JSON válido."
            ),
        ) from exc


@router.get("/health")
def health():
    """Comprueba la configuración local, no la disponibilidad de crédito."""
    return {
        "status": "ok",
        "api_key_configured": bool(
            os.getenv("OPENAI_API_KEY", "").strip()
        ),
        "model": os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
    }


@router.post("/propose")
async def propose_intervention(
    file: UploadFile = File(...),
    segmentation_json: str | None = Form(default=None),
    context_json: str | None = Form(default=None),
    user_goal: str = Form(
        default=(
            "Mejorar la calidad ambiental y la "
            "habitabilidad urbana de la zona."
        )
    ),
):
    """
    Analiza una imagen urbana y propone intervenciones.
    Devuelve un plan estructurado y un prompt para una
    visualización conceptual del escenario posterior.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Falta OPENAI_API_KEY. Configura la clave "
                "en el archivo .env de la raíz del proyecto."
            ),
        )

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip()

    # Validar el tipo de archivo.
    content_type = (file.content_type or "").lower()

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Formato no admitido. Usa JPG, PNG o WEBP.",
        )

    # Leer como máximo 10 MB más un byte para detectar exceso.
    image_bytes = await file.read(MAX_IMAGE_BYTES + 1)

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="El archivo de imagen está vacío.",
        )

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="La imagen supera el límite de 10 MB.",
        )

    # Interpretar los datos opcionales.
    segmentation = parse_optional_json(
        segmentation_json,
        "segmentation_json",
    )

    context = parse_optional_json(
        context_json,
        "context_json",
    )

    # Convertir la imagen a una data URL.
    encoded_image = base64.b64encode(
        image_bytes
    ).decode("ascii")

    data_url = (
        f"data:{content_type};base64,{encoded_image}"
    )

    instructions = """
Eres un asistente de análisis y planificación urbana
para el proyecto académico Urban AI Bucaramanga.

Debes responder exclusivamente con un objeto JSON válido.
JSON significa JavaScript Object Notation. No incluyas
Markdown, bloques de código ni texto fuera del objeto.

OBJETIVO
Analiza la imagen urbana y los datos proporcionados.
Puedes proponer intervenciones nuevas, razonables y
justificadas; no te limites a una lista predefinida.

RIGOR CIENTÍFICO
- Diferencia observaciones, inferencias y propuestas.
- Trata la segmentación como una estimación del modelo,
  no como una verdad perfecta del terreno.
- No inventes NDVI, NDBI, temperaturas, coordenadas,
  superficies, costes, normas ni métricas.
- Si un dato no fue aportado, indícalo como no disponible.
- No afirmes que una intervención es legal, construible
  o físicamente validada sin evidencia.
- No infieras temperatura física a partir de una imagen RGB.
- Justifica cada propuesta con evidencia disponible.
- Describe incertidumbres y formas de verificar la propuesta.
- La imagen del escenario posterior será conceptual,
  no una simulación física ni un plano de construcción.
- No garantices que un generador de imágenes conservará
  exactamente la geometría, los edificios o las vías.

FORMATO JSON REQUERIDO
Devuelve exactamente estas claves principales:

{
  "diagnosis": "string",
  "observations": [
    {
      "finding": "string",
      "basis": "string"
    }
  ],
  "inferences": [
    {
      "inference": "string",
      "uncertainty": "string"
    }
  ],
  "recommendations": [
    {
      "title": "string",
      "description": "string",
      "rationale": "string",
      "evidence_type": "observacion | inferencia | propuesta",
      "priority": "alta | media | baja",
      "expected_benefit": "string",
      "limitations": "string"
    }
  ],
  "intervention_plan": [
    {
      "action": "string",
      "location_hint": "string",
      "purpose": "string",
      "verification": "string"
    }
  ],
  "image_generation_prompt": "string",
  "negative_prompt": "string",
  "data_limitations": ["string"]
}

REGLAS PARA EL CONTENIDO
- Usa español claro y técnico.
- No inventes ubicaciones exactas dentro de la imagen.
- En location_hint, describe solo áreas visualmente
  identificables; si no es posible, dilo expresamente.
- Las prioridades son orientativas y no sustituyen
  una evaluación técnica de campo.
- expected_benefit debe describir beneficios esperados,
  no resultados medidos o garantizados.
- El prompt de imagen debe proponer una transformación
  urbana conceptual realista basada en la imagen original.
- Prioriza las intervenciones recomendadas y evita
  modificaciones innecesarias de edificios y vías.
- Incluye en data_limitations cualquier ausencia
  relevante de datos o evidencia.
"""

    # La palabra JSON aparece explícitamente en el mensaje
    # de entrada y en las instrucciones para cumplir el
    # requisito de json_object de la Responses API.
    user_payload = {
        "output_format": (
            "JSON: devuelve exclusivamente un objeto JSON "
            "válido, sin Markdown ni texto adicional."
        ),
        "user_goal": user_goal,
        "segmentation_results": segmentation,
        "available_geospatial_context": context,
        "instructions": (
            "Analiza la imagen adjunta junto con los datos. "
            "No supongas que existen datos que no se aportaron. "
            "Tu respuesta debe estar en formato JSON válido."
        ),
    }

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                user_payload,
                                ensure_ascii=False,
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": data_url,
                            "detail": "high",
                        },
                    ],
                }
            ],
            text={
                "format": {
                    "type": "json_object",
                }
            },
            max_output_tokens=3000,
        )

        output_text = response.output_text

        if not output_text or not output_text.strip():
            logger.error(
                "OpenAI devolvió una respuesta vacía. "
                "Modelo: %s",
                model,
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "La IA devolvió una respuesta vacía. "
                    "Intenta nuevamente."
                ),
            )

        try:
            result = json.loads(output_text)
        except json.JSONDecodeError as exc:
            logger.exception(
                "La respuesta de OpenAI no es JSON válido."
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "La respuesta de la IA no pudo "
                    "interpretarse como JSON."
                ),
            ) from exc

        if not isinstance(result, dict):
            raise HTTPException(
                status_code=502,
                detail=(
                    "La respuesta de la IA no es "
                    "un objeto JSON."
                ),
            )

        required_keys = {
            "diagnosis",
            "observations",
            "inferences",
            "recommendations",
            "intervention_plan",
            "image_generation_prompt",
            "negative_prompt",
            "data_limitations",
        }

        missing_keys = required_keys - result.keys()

        if missing_keys:
            logger.error(
                "Faltan claves en la respuesta JSON: %s",
                sorted(missing_keys),
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "La IA devolvió una estructura "
                    "incompleta. Revisa los registros."
                ),
            )

        return {
            "status": "success",
            "model": model,
            "conceptual_only": True,
            "analysis": result,
        }

    except HTTPException:
        raise

    except APIError as exc:
        # Registra el detalle del SDK en la terminal.
        # No se devuelve la respuesta interna al navegador.
        logger.exception(
            "Error de OpenAI. Tipo: %s; código HTTP: %s",
            type(exc).__name__,
            getattr(exc, "status_code", None),
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "OpenAI rechazó o no pudo procesar "
                "la solicitud. Consulta la terminal "
                "del backend para ver el error."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Error inesperado en el planificador de intervenciones."
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Ocurrió un error inesperado al generar "
                "la propuesta. Revisa los registros "
                "del backend."
            ),
        ) from exc
