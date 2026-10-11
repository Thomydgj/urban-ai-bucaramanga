import {
  useEffect,
  useState,
} from "react";

import {
  Upload,
  Image as ImageIcon,
  Leaf,
  Building2,
  Route,
  Layers3,
  Loader2,
  AlertTriangle,
} from "lucide-react";


const API_BASE_URL = "http://127.0.0.1:8000";


const CLASS_CONFIG = {
  vegetation: {
    label: "Vegetación",
    icon: Leaf,
  },

  built_up: {
    label: "Construido",
    icon: Building2,
  },

  roads: {
    label: "Vías",
    icon: Route,
  },

  other: {
    label: "Otros",
    icon: Layers3,
  },
};


function formatPercentage(value) {

  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }


  return `${(
    Number(value) * 100
  ).toFixed(2)}%`;

}


export default function SegmentationPanel() {

  const [
    selectedFile,
    setSelectedFile,
  ] = useState(null);


  const [
    previewUrl,
    setPreviewUrl,
  ] = useState(null);


  const [
    result,
    setResult,
  ] = useState(null);


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState(null);


  /* =========================================================
     LIMPIAR URL DE PREVISUALIZACIÓN
  ========================================================= */

  useEffect(() => {

    return () => {

      if (previewUrl) {

        URL.revokeObjectURL(
          previewUrl
        );

      }

    };

  }, [previewUrl]);


  /* =========================================================
     SELECCIONAR IMAGEN
  ========================================================= */

  function handleFileChange(
    event
  ) {

    const file =
      event.target.files?.[0];


    if (!file) {
      return;
    }


    setSelectedFile(file);

    setResult(null);

    setError(null);


    const newPreviewUrl =
      URL.createObjectURL(file);


    setPreviewUrl(
      newPreviewUrl
    );

  }


  /* =========================================================
     EJECUTAR SEGMENTACIÓN
  ========================================================= */

  async function handleAnalyze() {

    if (!selectedFile) {

      setError(
        "Selecciona una imagen antes de analizar."
      );

      return;

    }


    setLoading(true);

    setError(null);

    setResult(null);


    try {

      const formData =
        new FormData();


      formData.append(
        "file",
        selectedFile
      );


      const response =
        await fetch(
          `${API_BASE_URL}/api/segmentation/predict`,
          {
            method: "POST",
            body: formData,
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data?.detail ||
          "No fue posible ejecutar la segmentación."
        );

      }


      setResult(data);

    } catch (err) {

      console.error(
        "Error ejecutando segmentación:",
        err
      );


      setError(
        err?.message ||
        "Ocurrió un error ejecutando la segmentación."
      );

    } finally {

      setLoading(false);

    }

  }


  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <section className="segmentation-section">

      <div className="segmentation-header">

        <div>

          <p className="section-label">
            VISIÓN ARTIFICIAL
          </p>


          <h2>
            Segmentación urbana
          </h2>


          <p className="segmentation-description">

            Analiza una imagen urbana mediante
            segmentación semántica para estimar
            la proporción de vegetación,
            superficie construida, vías y otros
            elementos.

          </p>

        </div>

      </div>


      {/* =====================================================
          CARGA DE IMAGEN
      ====================================================== */}

      <div className="segmentation-upload-card">

        <div className="segmentation-upload">

          <input
            id="segmentation-file"
            type="file"
            accept="image/*"
            onChange={
              handleFileChange
            }
            hidden
          />


          <label
            htmlFor="segmentation-file"
            className="segmentation-file-button"
          >

            <Upload
              size={18}
            />

            Seleccionar imagen

          </label>


          {selectedFile && (

            <div className="segmentation-file-name">

              <ImageIcon
                size={17}
              />

              <span>
                {selectedFile.name}
              </span>

            </div>

          )}


          <button
            type="button"
            className="segmentation-analyze-button"
            onClick={
              handleAnalyze
            }
            disabled={
              !selectedFile ||
              loading
            }
          >

            {loading ? (

              <>

                <Loader2
                  size={18}
                  className="segmentation-spinner"
                />

                Analizando...

              </>

            ) : (

              "Ejecutar segmentación"

            )}

          </button>

        </div>


        {error && (

          <div className="segmentation-error">

            <AlertTriangle
              size={18}
            />

            <span>
              {error}
            </span>

          </div>

        )}

      </div>


      {/* =====================================================
          PREVISUALIZACIÓN
      ====================================================== */}

      {previewUrl && (

        <div className="segmentation-preview-card">

          <div className="segmentation-card-title">

            <ImageIcon
              size={19}
            />

            Imagen seleccionada

          </div>


          <img
            src={previewUrl}
            alt="Imagen seleccionada para segmentación"
            className="segmentation-preview-image"
          />

        </div>

      )}


      {/* =====================================================
          RESULTADOS
      ====================================================== */}

      {result && (

        <div className="segmentation-results">

          <div className="segmentation-results-header">

            <div>

              <p className="section-label">
                RESULTADO DEL MODELO
              </p>


              <h3>
                Distribución de clases
              </h3>

            </div>

          </div>


          <div className="segmentation-content-grid">

            {/* ===============================================
                PROPORCIONES
            ================================================ */}

            <div className="segmentation-proportions-card">

              <h4>
                Proporciones estimadas
              </h4>


              <div className="segmentation-metrics">

                {Object.entries(
                  CLASS_CONFIG
                ).map(
                  ([
                    className,
                    config,
                  ]) => {

                    const Icon =
                      config.icon;


                    const value =
                      result?.proportions?.[
                        className
                      ] ?? 0;


                    return (

                      <div
                        className="segmentation-metric"
                        key={className}
                      >

                        <div className="segmentation-metric-icon">

                          <Icon
                            size={19}
                          />

                        </div>


                        <div className="segmentation-metric-info">

                          <span>
                            {config.label}
                          </span>


                          <strong>
                            {formatPercentage(
                              value
                            )}
                          </strong>

                        </div>

                      </div>

                    );

                  }
                )}

              </div>

            </div>


            {/* ===============================================
                SEGMENTACIÓN
            ================================================ */}

            <div className="segmentation-image-card">

              <h4>
                Mapa de segmentación
              </h4>


              {result.segmentation_image ? (

                <img
                  src={
                    result.segmentation_image
                  }
                  alt="Resultado de segmentación semántica"
                  className="segmentation-result-image"
                />

              ) : (

                <div className="segmentation-no-image">

                  No se recibió una imagen
                  segmentada.

                </div>

              )}

            </div>

          </div>


          {/* =================================================
              INFORMACIÓN DEL MODELO
          ================================================== */}

          <div className="segmentation-model-card">

            <div>

              <span className="segmentation-model-label">
                Modelo
              </span>


              <strong>
                {result?.model?.architecture ||
                  "SegFormer B0"}
              </strong>

            </div>


            <div>

              <span className="segmentation-model-label">
                Dataset
              </span>


              <strong>
                {result?.model?.training_dataset ||
                  "LoveDA Urban"}
              </strong>

            </div>


            <div>

              <span className="segmentation-model-label">
                Validación mIoU
              </span>


              <strong>
                {result?.model?.validation_miou
                  ? Number(
                      result.model.validation_miou
                    ).toFixed(4)
                  : "—"}
              </strong>

            </div>


            <div>

              <span className="segmentation-model-label">
                Dispositivo
              </span>


              <strong>
                {result?.model?.device ||
                  "—"}
              </strong>

            </div>

          </div>


          {/* =================================================
              ADVERTENCIA CIENTÍFICA
          ================================================== */}

          <div className="segmentation-notice">

            <AlertTriangle
              size={19}
            />


            <div>

              <strong>
                Alcance experimental
              </strong>


              <p>

                Este modelo fue entrenado y
                validado con imágenes urbanas
                del dataset LoveDA. Su aplicación
                sobre imágenes aéreas de
                Bucaramanga debe interpretarse
                como análisis experimental debido
                a la diferencia de dominio entre
                los datos de entrenamiento y la
                imagen analizada.

              </p>

            </div>

          </div>

        </div>

      )}

    </section>

  );

}