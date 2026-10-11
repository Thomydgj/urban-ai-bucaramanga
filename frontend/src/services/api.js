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

    try {
      const body = await response.json();

      message = body?.detail
        ? String(body.detail)
        : body?.message
          ? String(body.message)
          : JSON.stringify(body);
    } catch {
      message = `La solicitud falló con HTTP ${response.status}.`;
    }

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

export async function getZones(filters = undefined) {
  return request(
    `/api/zones${buildQuery(filters)}`
  );
}

export async function getFilterOptions() {
  return request("/api/filters");
}

export async function getZone(zoneId) {
  if (
    zoneId === null ||
    zoneId === undefined ||
    zoneId === ""
  ) {
    throw new Error(
      "Debes indicar el identificador de la zona."
    );
  }

  return request(
    `/api/zones/${encodeURIComponent(zoneId)}`
  );
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
      .map((item) => compactSegmentation(item, depth + 1))
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

  const compactContext = compactSegmentation(context ?? {});
  const contextJSON = JSON.stringify(compactContext ?? {});

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

  const formData = new FormData();

  formData.append("file", file);
  formData.append("prompt", prompt);
  formData.append("negative_prompt", negativePrompt);
  formData.append("strength", String(strength));
  formData.append("steps", String(steps));
  formData.append("guidance_scale", String(guidanceScale));

  if (
    seed !== null &&
    seed !== undefined &&
    seed !== ""
  ) {
    formData.append("seed", String(seed));
  }

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

/* =========================================================
   GENERACIÓN CONCEPTUAL LEGACY
   Compatibilidad con llamadas anteriores.
========================================================= */

export async function generateConceptualAfterLegacy(
  file,
  prompt,
  options = {}
) {
  return generateConceptualAfter({
    file,
    prompt,
    negativePrompt:
      options.negativePrompt ??
      options.negative_prompt ??
      "",
    strength: options.strength ?? 0.65,
    steps: options.steps ?? 30,
    guidanceScale:
      options.guidanceScale ??
      options.guidance_scale ??
      7.5,
    seed: options.seed ?? null
  });
}
