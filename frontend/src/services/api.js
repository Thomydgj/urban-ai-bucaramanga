
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const IMAGE_GENERATION_URL = (
  import.meta.env.VITE_IMAGE_GENERATION_URL ||
  "http://127.0.0.1:8001"
).replace(/\/+$/, "");

/* =========================================================
   UTILIDADES HTTP
========================================================= */

async function request(
  path,
  options = {},
  baseUrl = API_BASE_URL
) {
  const response = await fetch(
    `${baseUrl}${path}`,
    options
  );

  if (!response.ok) {
    let message = "";
    let bodyText = "";

    try {
      bodyText = await response.text();

      if (bodyText) {
        let body;

        try {
          body = JSON.parse(bodyText);
        } catch {
          body = null;
        }

        const detail =
          body?.detail ??
          body?.message ??
          body?.error;

        if (typeof detail === "string") {
          message = detail;
        } else if (
          detail !== null &&
          detail !== undefined
        ) {
          message = JSON.stringify(detail, null, 2);
        } else if (body !== null) {
          message = JSON.stringify(body, null, 2);
        } else {
          message = bodyText;
        }
      }
    } catch (error) {
      message =
        error instanceof Error
          ? error.message
          : String(error);
    }

    if (!message) {
      message = `La solicitud falló con HTTP ${response.status}.`;
    }

    console.error("Error HTTP de la API:", {
      status: response.status,
      url: `${baseUrl}${path}`,
      response: bodyText || message
    });

    throw new Error(
      `Error HTTP ${response.status}: ${message}`
    );
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function buildQuery(filters = {}) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (
      value !== null &&
      value !== undefined &&
      value !== ""
    ) {
      params.set(key, String(value));
    }
  });

  const query = params.toString();

  return query ? `?${query}` : "";
}

/* =========================================================
   DASHBOARD
========================================================= */

export async function getSummary(filters = undefined) {
  return request(
    `/api/summary${buildQuery(filters)}`
  );
}

export async function getMap(filters = undefined) {
  return request(
    `/api/map${buildQuery(filters)}`
  );
}

export async function getFilterOptions() {
  return request("/api/filters");
}

/* =========================================================
   REDUCIR DATOS DE SEGMENTACIÓN
   Elimina imágenes y estructuras excesivamente grandes.
========================================================= */

function compactSegmentation(value, depth = 0) {
  if (value === null || value === undefined) {
    return value ?? null;
  }

  if (depth > 12) {
    return undefined;
  }

  if (typeof value !== "object") {
    if (
      typeof value === "string" &&
      value.length > 2000
    ) {
      return undefined;
    }

    return value;
  }

  const excludedKeys = new Set([
    "mask",
    "overlay",
    "visualization",
    "image",
    "image_url",
    "mask_url",
    "overlay_url",
    "visualization_url",
    "segmentation_image",
    "segmentation_image_url",
    "prediction_image",
    "prediction_url",
    "mask_base64",
    "image_base64",
    "base64",
    "data_url",
    "pixels",
    "tensor",
    "logits",
    "raw_mask",
    "encoded_image"
  ]);

  if (Array.isArray(value)) {
    if (value.length > 1000) {
      return undefined;
    }

    return value
      .map((item) =>
        compactSegmentation(item, depth + 1)
      )
      .filter((item) => item !== undefined);
  }

  const result = {};

  for (const [key, item] of Object.entries(value)) {
    const normalizedKey = key.toLowerCase();

    if (
      excludedKeys.has(normalizedKey) ||
      normalizedKey.endsWith("_base64") ||
      normalizedKey.endsWith("_data_url")
    ) {
      continue;
    }

    const compactValue = compactSegmentation(
      item,
      depth + 1
    );

    if (compactValue !== undefined) {
      result[key] = compactValue;
    }
  }

  return result;
}

/* =========================================================
   SEGMENTACIÓN LOVE DA
========================================================= */

export async function analyzeImageComposition(file) {
  if (!file) {
    throw new Error(
      "Selecciona una imagen para analizar."
    );
  }

  const allowedTypes = [
    "image/jpeg",
    "image/png",
    "image/webp"
  ];

  if (
    file.type &&
    !allowedTypes.includes(file.type.toLowerCase())
  ) {
    throw new Error(
      "Formato no admitido. Usa una imagen JPG, PNG o WEBP."
    );
  }

  const formData = new FormData();

  formData.append("file", file);

  return request(
    "/api/segmentation/predict",
    {
      method: "POST",
      body: formData
    }
  );
}

/* =========================================================
   PLANIFICADOR DE INTERVENCIÓN URBANA
========================================================= */

export async function requestInterventionProposal({
  file,
  segmentation = null,
  context = {},
  userGoal
}) {
  if (!file) {
    throw new Error(
      "Selecciona una imagen para generar el diagnóstico."
    );
  }

  const allowedTypes = [
    "image/jpeg",
    "image/png",
    "image/webp"
  ];

  if (
    file.type &&
    !allowedTypes.includes(file.type.toLowerCase())
  ) {
    throw new Error(
      "Formato no admitido. Usa una imagen JPG, PNG o WEBP."
    );
  }

  const formData = new FormData();

  formData.append("file", file);

  // Agregar solamente los datos resumidos de segmentación.
  if (
    segmentation !== null &&
    segmentation !== undefined
  ) {
    const compact = compactSegmentation(segmentation);

    if (compact !== null && compact !== undefined) {
      const segmentationJSON = JSON.stringify(compact);

      if (segmentationJSON.length <= 500_000) {
        formData.append(
          "segmentation_json",
          segmentationJSON
        );
      } else {
        console.warn(
          "Los datos de segmentación son demasiado grandes. " +
          "Se continuará sin ellos."
        );
      }
    }
  }

  const compactContext = compactSegmentation(
    context ?? {}
  );

  const contextJSON = JSON.stringify(
    compactContext ?? {}
  );

  if (contextJSON.length > 200_000) {
    throw new Error(
      "El contexto enviado al planificador es demasiado grande. " +
      "Reduce los datos geoespaciales antes de continuar."
    );
  }

  formData.append("context_json", contextJSON);

  if (
    typeof userGoal === "string" &&
    userGoal.trim()
  ) {
    formData.append("user_goal", userGoal.trim());
  }

  return request(
    "/api/intervention-planner/propose",
    {
      method: "POST",
      body: formData
    }
  );
}

/* =========================================================
   GENERACIÓN DE IMAGEN CONCEPTUAL
========================================================= */

export async function generateConceptualAfter({
  file,
  prompt,
  negativePrompt = "",
  strength = 0.65,
  steps = 30,
  guidanceScale = 7.5,
  seed = null
}) {
  if (!file) {
    throw new Error(
      "Selecciona una imagen base para generar la propuesta."
    );
  }

  if (!prompt || !prompt.trim()) {
    throw new Error(
      "No se recibió una descripción para generar la imagen."
    );
  }

  // El backend admite máximo 2000 caracteres en prompt.
  const MAX_PROMPT_LENGTH = 2000;

  const cleanPrompt = prompt
    .replace(/\\n/g, "\n")
    .trim()
    .slice(0, MAX_PROMPT_LENGTH);

  const formData = new FormData();

  formData.append("file", file);
  formData.append("prompt", cleanPrompt);
  formData.append(
    "negative_prompt",
    String(negativePrompt || "").slice(0, 2000)
  );
  formData.append("strength", String(strength));
  formData.append("steps", String(steps));
  formData.append(
    "guidance_scale",
    String(guidanceScale)
  );

  if (
    seed !== null &&
    seed !== undefined &&
    seed !== ""
  ) {
    formData.append("seed", String(seed));
  }

  console.log("Generando propuesta conceptual:", {
    promptLength: cleanPrompt.length,
    maxPromptLength: MAX_PROMPT_LENGTH
  });

  return request(
    "/api/image-generation/generate",
    {
      method: "POST",
      body: formData
    },
    IMAGE_GENERATION_URL
  );
}

/* =========================================================
   GENERAR URL ABSOLUTA DE UNA IMAGEN
========================================================= */

export function getGeneratedImageUrl(imageUrl) {
  if (
    !imageUrl ||
    typeof imageUrl !== "string"
  ) {
    return null;
  }

  if (
    imageUrl.startsWith("http://") ||
    imageUrl.startsWith("https://") ||
    imageUrl.startsWith("blob:") ||
    imageUrl.startsWith("data:")
  ) {
    return imageUrl;
  }

  const baseUrl = imageUrl.startsWith(
    "/api/image-generation/"
  )
    ? IMAGE_GENERATION_URL
    : API_BASE_URL;

  return `${baseUrl}${
    imageUrl.startsWith("/") ? "" : "/"
  }${imageUrl}`;
}
