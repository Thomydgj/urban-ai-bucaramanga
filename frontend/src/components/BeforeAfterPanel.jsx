
import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowDown,
  ArrowRight,
  CheckCircle2,
  ImagePlus,
  LoaderCircle,
  RefreshCw,
  Sparkles,
  Upload,
  Trees,
} from "lucide-react";

import {
  analyzeImageComposition,
  requestInterventionProposal,
  generateConceptualAfter,
  getGeneratedImageUrl,
} from "../services/api";

/* -------------------- Utilidades -------------------- */

function getAnalysis(payload) {
  return (
    payload?.analysis ??
    payload?.result?.analysis ??
    payload?.data?.analysis ??
    payload?.result ??
    payload?.data ??
    payload ??
    {}
  );
}

function getErrorMessage(error) {
  return error?.message || "Ocurrió un error al procesar la imagen.";
}

function formatPercent(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return "—";

  return `${(number >= 0 && number <= 1 ? number * 100 : number).toFixed(1)}%`;
}

function getSegmentationClasses(result) {
  const candidates = [
    result?.class_percentages,
    result?.class_proportions,
    result?.proportions,
    result?.percentages,
    result?.class_distribution,
    result?.statistics?.class_percentages,
    result?.statistics?.class_proportions,
    result?.statistics?.class_distribution,
    result?.stats?.class_percentages,
    result?.data?.class_percentages,
  ];

  const data = candidates.find(
    (item) => item && typeof item === "object" && !Array.isArray(item)
  );

  if (data) {
    return Object.entries(data).map(([name, value]) => ({
      name: name.replaceAll("_", " "),
      value:
        typeof value === "object" && value !== null
          ? value.percentage ??
            value.percent ??
            value.proportion ??
            value.area_fraction ??
            value.value ??
            0
          : value,
    }));
  }

  // También admite respuestas donde las clases vienen como una lista.
  const list =
    result?.classes ??
    result?.class_statistics ??
    result?.statistics?.classes;

  if (Array.isArray(list)) {
    return list.map((item, index) => ({
      name: String(item?.name ?? item?.class_name ?? item?.label ?? `Clase ${index + 1}`),
      value:
        item?.percentage ??
        item?.percent ??
        item?.proportion ??
        item?.area_fraction ??
        item?.value ??
        0,
    }));
  }

  return [];
}

function resolveImage(candidate) {
  if (typeof candidate !== "string" || !candidate.trim()) return null;

  const value = candidate.trim();

  if (
    value.startsWith("data:image/") ||
    value.startsWith("blob:") ||
    /^https?:\/\//i.test(value)
  ) {
    return value;
  }

  if (value.startsWith("/")) {
    return getGeneratedImageUrl(value);
  }

  return null;
}

function getMaskFromResponse(payload) {
  const sources = [
    payload,
    payload?.result,
    payload?.data,
    payload?.prediction,
    payload?.segmentation,
    payload?.visualization,
    payload?.result?.data,
    payload?.data?.result,
    payload?.statistics,
  ].filter(Boolean);

  const keys = [
    "mask_url",
    "overlay_url",
    "visualization_url",
    "segmentation_url",
    "segmentation_image_url",
    "mask_image_url",
    "prediction_url",
    "mask",
    "overlay",
    "visualization",
    "segmentation_image",
    "prediction_image",
    "image_url",
    "image",
  ];

  for (const source of sources) {
    for (const key of keys) {
      const image = resolveImage(source?.[key]);
      if (image) return image;
    }
  }

  return null;
}

function getGeneratedImage(payload) {
  const sources = [
    payload,
    payload?.result,
    payload?.data,
    payload?.result?.data,
  ].filter(Boolean);

  for (const source of sources) {
    for (const key of ["image_url", "url", "image"]) {
      const image = resolveImage(source?.[key]);
      if (image) return image;
    }
  }

  return null;
}

function asList(value) {
  return Array.isArray(value) ? value : [];
}

/* -------------------- Componente -------------------- */

export default function BeforeAfterPanel() {
  const [file, setFile] = useState(null);
  const [segmentation, setSegmentation] = useState(null);
  const [maskImage, setMaskImage] = useState(null);
  const [maskError, setMaskError] = useState(false);
  const [proposal, setProposal] = useState(null);
  const [generatedImage, setGeneratedImage] = useState(null);

  const [loadingSegmentation, setLoadingSegmentation] = useState(false);
  const [loadingProposal, setLoadingProposal] = useState(false);
  const [loadingGeneration, setLoadingGeneration] = useState(false);

  const [error, setError] = useState("");
  const [stage, setStage] = useState("idle");

  const previewUrl = useMemo(
    () => (file ? URL.createObjectURL(file) : null),
    [file]
  );

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const analysis = useMemo(() => getAnalysis(proposal), [proposal]);
  const classes = useMemo(
    () => getSegmentationClasses(segmentation),
    [segmentation]
  );

  const observations = asList(analysis?.observations);
  const inferences = asList(analysis?.inferences);
  const recommendations = asList(analysis?.recommendations);
  const interventionPlan = asList(analysis?.intervention_plan);
  const limitations = asList(analysis?.data_limitations);

  const busy =
    loadingSegmentation || loadingProposal || loadingGeneration;

  function handleFileChange(event) {
    const selected = event.target.files?.[0];

    if (!selected) return;

    if (!selected.type.startsWith("image/")) {
      setError("Selecciona un archivo de imagen válido.");
      return;
    }

    setFile(selected);
    setSegmentation(null);
    setMaskImage(null);
    setMaskError(false);
    setProposal(null);
    setGeneratedImage(null);
    setError("");
    setStage("idle");
  }

  function resetWorkflow() {
    setFile(null);
    setSegmentation(null);
    setMaskImage(null);
    setMaskError(false);
    setProposal(null);
    setGeneratedImage(null);
    setError("");
    setStage("idle");
  }

  async function handleAnalyze() {
    if (!file) {
      setError("Primero selecciona una imagen urbana.");
      return;
    }

    setError("");
    setSegmentation(null);
    setMaskImage(null);
    setMaskError(false);
    setProposal(null);
    setGeneratedImage(null);

    try {
      setLoadingSegmentation(true);
      setStage("segmenting");

      const segmentationResult = await analyzeImageComposition(file);

      // Conserva la respuesta completa de LoveDA.
      setSegmentation(segmentationResult);

      const detectedMask = getMaskFromResponse(segmentationResult);
      setMaskImage(detectedMask);

      // Permite revisar el formato real de la respuesta en DevTools.
      console.log("Respuesta completa de LoveDA:", segmentationResult);
      console.log("Imagen de segmentación detectada:", detectedMask);

      setLoadingSegmentation(false);
      setLoadingProposal(true);
      setStage("diagnosing");

      const proposalResult = await requestInterventionProposal({
        file,
        segmentation: segmentationResult,
        context: {
          project: "Urban AI Bucaramanga",
          purpose:
            "Analizar una imagen urbana y proponer intervenciones conceptuales.",
          constraints: [
            "No presentar la propuesta como una obra ejecutada.",
            "Distinguir los resultados del modelo de las inferencias.",
            "No afirmar cambios físicos de temperatura sin datos térmicos.",
            "Respetar la estructura urbana visible en la imagen original.",
          ],
        },
      });

      setProposal(proposalResult);
      setStage("ready");
    } catch (err) {
      console.error("Error en el análisis urbano:", err);
      setError(getErrorMessage(err));
      setStage("error");
    } finally {
      setLoadingSegmentation(false);
      setLoadingProposal(false);
    }
  }

  async function handleGenerateAfter() {
    if (!file || !analysis) {
      setError("Primero analiza la imagen y genera el diagnóstico.");
      return;
    }

    // Construye un prompt breve a partir de las recomendaciones y acciones.
    // El backend valida un máximo de 2000 caracteres para el campo "prompt".
    const basePrompt = String(
      analysis?.image_generation_prompt ??
      analysis?.image_prompt ??
      analysis?.visual_prompt ??
      "Representación conceptual de una intervención urbana localizada basada en el diagnóstico."
    ).trim();

    // Extrae solo la acción recomendada; omite justificaciones y fundamentos.
    const extractAction = (item) => {
      const raw =
        typeof item === "string"
          ? item
          : item?.action ??
            item?.title ??
            item?.recommendation ??
            item?.description ??
            "";

      return String(raw)
        .split(/justificación\\s*:/i)[0]
        .split(/justification\\s*:/i)[0]
        .trim()
        .replace(/^\\d+[.)]\\s*/, "");
    };

    const actionTexts = [
      ...recommendations.map(extractAction),
      ...interventionPlan.map(extractAction),
    ].filter(Boolean);

    // Evita duplicados sin alterar el orden de prioridad.
    const uniqueActions = [...new Set(actionTexts)].slice(0, 6);
    const actionInstructions = uniqueActions.length
      ? uniqueActions.map((action, index) => `${index + 1}. ${action}`).join("\\n")
      : "Aplicar únicamente las acciones de intervención explícitas en el diagnóstico.";

    const fixedInstructions = [
      "Representa las acciones recomendadas como intervenciones urbanas plausibles y localizadas.",
      "Conserva perspectiva, calles, edificios y distribución espacial originales.",
      "No agregues elementos decorativos ni intervenciones no respaldadas por las recomendaciones.",
      "Propuesta conceptual; no representa una obra ejecutada.",
    ].join("\\n");

    // Reservar espacio para las acciones y las reglas; recortar la descripción base
    // antes que eliminar las recomendaciones.
    const actionBlock = `ACCIONES RECOMENDADAS (sin justificaciones):\\n${actionInstructions}`;
    const suffix = `\\n\\n${actionBlock}\\n\\n${fixedInstructions}`;
    const availableBaseLength = Math.max(
      0,
      2000 - suffix.length
    );
    const compactBase = basePrompt.slice(0, availableBaseLength).trim();
    const prompt = `${compactBase}${suffix}`.trim().slice(0, 2000);

    const backendNegativePrompt = analysis?.negative_prompt ?? "";
    const negativePrompt = [
      backendNegativePrompt,
      "generic tree planting, excessive trees, forest, decorative greenery, unrelated landscaping, invented interventions, redesigning the whole street, changing camera angle, changing building locations, unrealistic urban layout",
    ]
      .filter(Boolean)
      .join(", ");

    if (!String(prompt).trim()) {
      setError(
        "El diagnóstico no contiene un prompt visual para generar la propuesta."
      );
      return;
    }

    setError("");
    setLoadingGeneration(true);
    setStage("generating");

    try {
      const result = await generateConceptualAfter({
        file,
        prompt,
        negativePrompt,
      });

      const imageUrl = getGeneratedImage(result);

      if (!imageUrl) {
        console.error("Respuesta del generador:", result);
        throw new Error(
          "El generador no devolvió una URL de imagen reconocida."
        );
      }

      setGeneratedImage(imageUrl);
      setStage("complete");
    } catch (err) {
      console.error("Error generando la propuesta:", err);
      setError(getErrorMessage(err));
      setStage("ready");
    } finally {
      setLoadingGeneration(false);
    }
  }

  return (
    <section className="before-after-panel" id="before-after">
      <header className="before-after-header">
        <div className="before-after-heading">
          <div className="before-after-icon">
            <Sparkles size={22} />
          </div>
          <div>
            <p className="section-label">INTELIGENCIA ARTIFICIAL</p>
            <h2>Intervención urbana conceptual</h2>
            <p>
              Analiza una imagen urbana, consulta la segmentación y genera una
              propuesta visual de intervención.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="before-after-reset"
          onClick={resetWorkflow}
          disabled={busy}
        >
          <RefreshCw size={16} /> Reiniciar
        </button>
      </header>

      <div className="before-after-workflow">
        <div className={`workflow-step ${segmentation ? "workflow-step-done" : ""}`}>
          <span className="workflow-step-number">1</span>
          <div><strong>Segmentación</strong><small>Modelo LoveDA</small></div>
        </div>
        <ArrowRight className="workflow-arrow" size={18} />
        <div className={`workflow-step ${proposal ? "workflow-step-done" : ""}`}>
          <span className="workflow-step-number">2</span>
          <div><strong>Diagnóstico</strong><small>Planificador IA</small></div>
        </div>
        <ArrowRight className="workflow-arrow" size={18} />
        <div className={`workflow-step ${generatedImage ? "workflow-step-done" : ""}`}>
          <span className="workflow-step-number">3</span>
          <div><strong>Propuesta visual</strong><small>Imagen conceptual</small></div>
        </div>
      </div>

      <div className="before-after-upload">
        <div className="before-after-upload-copy">
          <div className="before-after-upload-icon"><ImagePlus size={24} /></div>
          <div>
            <h3>Imagen de referencia</h3>
            <p>Selecciona una imagen de una calle, barrio o espacio urbano.</p>
            <small>Selecciona una imagen compatible con el modelo LoveDA.</small>
          </div>
        </div>

        <label className="before-after-file-button">
          <Upload size={17} />
          {file ? "Cambiar imagen" : "Seleccionar imagen"}
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            disabled={busy}
          />
        </label>
      </div>

      {file && (
        <div className="before-after-selected-file">
          <CheckCircle2 size={16} />
          <span>{file.name}</span>
          <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
        </div>
      )}

      {previewUrl && (
        <div className="before-after-image-grid">
          <article className="before-after-image-card">
            <div className="before-after-card-heading">
              <span className="before-after-tag">ORIGINAL</span>
              <span>Imagen de entrada</span>
            </div>
            <img src={previewUrl} alt="Imagen urbana original" />
            <div className="before-after-image-caption">
              Imagen proporcionada para el análisis.
            </div>
          </article>

          <article className="before-after-image-card">
            <div className="before-after-card-heading">
              <span className="before-after-tag">PROPUESTA</span>
              <span>Resultado conceptual</span>
            </div>

            {generatedImage ? (
              <>
                <img
                  src={generatedImage}
                  alt="Propuesta conceptual de intervención urbana"
                />
                <div className="before-after-image-caption">
                  Imagen generada por IA. No representa una obra ejecutada.
                </div>
              </>
            ) : (
              <div className="before-after-image-placeholder">
                {loadingGeneration ? (
                  <>
                    <LoaderCircle className="before-after-spinner" size={30} />
                    <strong>Generando propuesta visual...</strong>
                    <p>El proceso puede tardar unos momentos.</p>
                  </>
                ) : (
                  <>
                    <Trees size={32} />
                    <strong>La propuesta aparecerá aquí</strong>
                    <p>Analiza primero la imagen para habilitar la generación.</p>
                  </>
                )}
              </div>
            )}
          </article>
        </div>
      )}

      {error && (
        <div className="before-after-error" role="alert">
          <AlertCircle size={19} />
          <div>
            <strong>No se pudo completar el proceso</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      <div className="before-after-actions">
        <button
          type="button"
          className="before-after-primary"
          onClick={handleAnalyze}
          disabled={!file || busy}
        >
          {loadingSegmentation || loadingProposal ? (
            <LoaderCircle size={18} className="before-after-spinner" />
          ) : (
            <Sparkles size={18} />
          )}
          {loadingSegmentation
            ? "Segmentando imagen..."
            : loadingProposal
              ? "Generando diagnóstico..."
              : "Analizar imagen urbana"}
        </button>

        <button
          type="button"
          className="before-after-secondary"
          onClick={handleGenerateAfter}
          disabled={!file || !proposal || busy}
        >
          {loadingGeneration ? (
            <LoaderCircle size={18} className="before-after-spinner" />
          ) : (
            <ImagePlus size={18} />
          )}
          {loadingGeneration
            ? "Generando imagen..."
            : generatedImage
              ? "Regenerar propuesta visual"
              : "Generar imagen conceptual"}
        </button>
      </div>

      {busy && (
        <div className="before-after-progress">
          <div className="before-after-progress-track">
            <div className="before-after-progress-bar" />
          </div>
          <p>
            {stage === "segmenting"
              ? "LoveDA está analizando la imagen."
              : stage === "diagnosing"
                ? "El planificador está elaborando el diagnóstico."
                : stage === "generating"
                  ? "Generando la propuesta visual."
                  : "Procesando solicitud..."}
          </p>
        </div>
      )}

      {segmentation && (
        <section className="before-after-results">
          <div className="before-after-section-title">
            <div>
              <p className="section-label">RESULTADO DEL MODELO</p>
              <h3>Composición urbana estimada</h3>
            </div>
            <span className="before-after-result-status">
              <CheckCircle2 size={15} /> Segmentación recibida
            </span>
          </div>

          {maskImage && !maskError ? (
            <div className="before-after-mask">
              <h4>Máscara o visualización de segmentación LoveDA</h4>
              <img
                src={maskImage}
                alt="Máscara de segmentación urbana LoveDA"
                onError={() => {
                  console.error("No se pudo cargar la imagen de segmentación:", maskImage);
                  setMaskError(true);
                }}
              />
            </div>
          ) : (
            <div className="before-after-mask-missing">
              <AlertCircle size={19} />
              <div>
                <strong>La imagen de segmentación no está disponible</strong>
                <p>
                  {maskError
                    ? "El servidor devolvió una ruta de imagen, pero el navegador no pudo cargarla."
                    : "La respuesta recibida no contiene una URL de máscara reconocida. Los porcentajes pueden mostrarse aunque el endpoint no devuelva la imagen."}
                </p>
                <small>
                  Abre la consola del navegador (F12) para revisar la respuesta
                  completa de LoveDA.
                </small>
              </div>
            </div>
          )}

          {classes.length > 0 ? (
            <div className="before-after-classes">
              {classes.map((item) => (
                <article className="before-after-class-card" key={item.name}>
                  <span>{item.name}</span>
                  <strong>{formatPercent(item.value)}</strong>
                </article>
              ))}
            </div>
          ) : (
            <p className="before-after-muted">
              La respuesta llegó, pero no se identificó un objeto de porcentajes
              compatible en los campos consultados.
            </p>
          )}

          <p className="before-after-disclaimer">
            Las proporciones corresponden a la salida del modelo de segmentación.
            No son mediciones catastrales ni verificaciones de campo.
          </p>
        </section>
      )}

      {proposal && (
        <section className="before-after-results">
          <div className="before-after-section-title">
            <div>
              <p className="section-label">DIAGNÓSTICO ASISTIDO POR IA</p>
              <h3>Análisis y plan de intervención</h3>
            </div>
            <span className="before-after-result-status">
              <CheckCircle2 size={15} /> Diagnóstico recibido
            </span>
          </div>

          {analysis?.diagnosis && (
            <article className="before-after-diagnosis">
              <h4>Diagnóstico general</h4>
              <p>{analysis.diagnosis}</p>
            </article>
          )}

          {observations.length > 0 && (
            <div className="before-after-list-section">
              <h4>Observaciones</h4>
              <ul>
                {observations.map((item, index) => (
                  <li key={index}>
                    <strong>
                      {typeof item === "string"
                        ? item
                        : item.finding ?? item.title ?? "Observación"}
                    </strong>
                    {typeof item === "object" && item?.basis && (
                      <p>Fundamento: {item.basis}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {inferences.length > 0 && (
            <div className="before-after-list-section">
              <h4>Inferencias</h4>
              <ul>
                {inferences.map((item, index) => (
                  <li key={index}>
                    {typeof item === "string"
                      ? item
                      : item.description ??
                        item.inference ??
                        item.finding ??
                        JSON.stringify(item)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {recommendations.length > 0 && (
            <div className="before-after-list-section">
              <h4>Recomendaciones</h4>
              <div className="before-after-recommendations">
                {recommendations.map((item, index) => (
                  <article className="before-after-recommendation" key={index}>
                    <div className="before-after-recommendation-heading">
                      <strong>{item.title ?? `Recomendación ${index + 1}`}</strong>
                      {item.priority && (
                        <span className="before-after-priority">{item.priority}</span>
                      )}
                    </div>
                    {item.description && <p>{item.description}</p>}
                    {item.rationale && (
                      <p><strong>Justificación:</strong> {item.rationale}</p>
                    )}
                    {item.evidence_type && (
                      <small>Tipo de evidencia: {item.evidence_type}</small>
                    )}
                  </article>
                ))}
              </div>
            </div>
          )}

          {interventionPlan.length > 0 && (
            <div className="before-after-list-section">
              <h4>Plan de intervención</h4>
              <ol>
                {interventionPlan.map((item, index) => (
                  <li key={index}>
                    {typeof item === "string"
                      ? item
                      : item.title ??
                        item.action ??
                        item.description ??
                        JSON.stringify(item)}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {limitations.length > 0 && (
            <div className="before-after-limitations">
              <h4>Limitaciones de los datos</h4>
              <ul>
                {limitations.map((item, index) => (
                  <li key={index}>
                    {typeof item === "string"
                      ? item
                      : item.description ??
                        item.limitation ??
                        JSON.stringify(item)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="before-after-disclaimer">
            <AlertCircle size={17} />
            <p>
              <strong>Propuesta conceptual, no validación técnica.</strong>{" "}
              Las recomendaciones requieren revisión profesional y verificación
              en campo. La imagen generada no demuestra viabilidad ni permite
              calcular cambios reales de temperatura.
            </p>
          </div>
        </section>
      )}

      {generatedImage && (
        <div className="before-after-completion">
          <CheckCircle2 size={19} />
          <div>
            <strong>Propuesta visual generada</strong>
            <p>
              Considera la imagen como una representación conceptual de una
              posible intervención.
            </p>
          </div>
        </div>
      )}

      {stage === "complete" && (
        <div className="before-after-next-step">
          <ArrowDown size={17} />
          Flujo completado: segmentación, diagnóstico y generación conceptual.
        </div>
      )}
    </section>
  );
}
