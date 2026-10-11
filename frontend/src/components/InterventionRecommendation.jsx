import {
  AlertTriangle,
  Clock3,
  Leaf,
  Target,
  ClipboardCheck,
  Info,
  ListChecks,
} from "lucide-react";


/* =========================================================
   FORMATEAR VALORES
========================================================= */

function formatValue(
  value,
  decimals = 3
) {

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }


  if (
    typeof value === "number"
  ) {

    return value.toFixed(
      decimals
    );

  }


  return String(value);

}


/* =========================================================
   FORMATEAR TEXTO DEL MOTOR
========================================================= */

function formatLabel(
  value
) {

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {

    return "—";

  }


  return String(
    value
  )
    .replaceAll(
      "_",
      " "
    )
    .toLowerCase()
    .replace(
      /^./,
      (character) =>
        character.toUpperCase()
    );

}


/* =========================================================
   FORMATEAR TEXTO LARGO
========================================================= */

function formatText(
  value
) {

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {

    return "—";

  }


  return String(value);

}


/* =========================================================
   CLASE SEGÚN NIVEL
========================================================= */

function getLevelClass(
  level
) {

  switch (
    String(level)
      .toUpperCase()
  ) {

    case "CRITICA":
      return "critical";

    case "ALTA":
      return "high";

    case "MEDIA":
      return "medium";

    default:
      return "default";

  }

}


/* =========================================================
   COMPONENTE
========================================================= */

export default function InterventionRecommendation({
  zone,
}) {


  /* =======================================================
     SIN ZONA
  ======================================================== */

  if (!zone) {

    return (

      <section className="intervention-recommendation">

        <div className="intervention-empty">

          <Target
            size={22}
          />

          <div>

            <strong>
              Selecciona una zona
            </strong>

            <p>
              Selecciona una zona en el
              mapa o en el ranking para
              consultar su intervención.
            </p>

          </div>

        </div>

      </section>

    );

  }


  /* =======================================================
     PROPIEDADES
  ======================================================== */

  const properties =
    zone?.properties || {};


  const zoneId =
    properties.zone_id ??
    "—";


  const level =
    properties.intervention_level ??
    "—";


  const interventionType =
    properties.intervention_type ??
    "—";


  const condition =
    properties.dominant_condition ??
    "—";


  const timeframe =
    properties.priority_timeframe ??
    "—";


  /* =======================================================
     RECOMENDACIONES GENERADAS POR EL MOTOR
  ======================================================== */

  const recommendation =
    properties.recommendation ??
    "—";


  const interventionObjective =
    properties.intervention_objective ??
    "—";


  const priorityReason =
    properties.priority_reason ??
    "—";


  const actionPackage =
    properties.action_package ??
    "—";


  const monitoringIndicator =
    properties.monitoring_indicator ??
    "—";


  /* =======================================================
     INDICADORES
  ======================================================== */

  const operationalScore =
    properties.operational_score;


  const hotspotScore =
    properties.hotspot_score;


  const probability =
    properties.mean_probability;


  const rank =
    properties.operational_rank;


  /* =======================================================
     ACCIONES DEL PAQUETE
     
     El motor entrega action_package como una cadena
     separada por "|".
  ======================================================== */

  const actionItems =
    String(actionPackage)
      .split("|")
      .map(
        (action) =>
          action.trim()
      )
      .filter(
        (action) =>
          action.length > 0
      );


  /* =======================================================
     RENDER
  ======================================================== */

  return (

    <section className="intervention-recommendation">


      {/* ===================================================
          HEADER
      ==================================================== */}

      <div className="intervention-recommendation-header">

        <div>

          <p className="section-label">
            INTERVENCIÓN
          </p>


          <h2>
            Recomendación para {zoneId}
          </h2>


          <p className="intervention-description">

            Propuesta de intervención generada
            por el motor de análisis urbano a
            partir de las condiciones e
            indicadores de la zona.

          </p>

        </div>


        <div
          className={`
            intervention-level
            ${getLevelClass(level)}
          `}
        >

          <AlertTriangle
            size={16}
          />

          <span>
            {formatLabel(level)}
          </span>

        </div>

      </div>


      {/* ===================================================
          RECOMENDACIÓN PRINCIPAL
      ==================================================== */}

      <div className="intervention-main-card">

        <div className="intervention-main-icon">

          <Leaf
            size={24}
          />

        </div>


        <div>

          <span className="intervention-main-label">

            Recomendación de intervención

          </span>


          <strong className="intervention-main-title">

            {formatText(
              recommendation
            )}

          </strong>


          <p>

            La recomendación corresponde
            a una zona con condición dominante
            de{" "}

            <strong>
              {formatLabel(
                condition
              )}
            </strong>

            {" "}y tipo de intervención{" "}

            <strong>
              {formatLabel(
                interventionType
              )}
            </strong>.

          </p>

        </div>

      </div>


      {/* ===================================================
          OBJETIVO
      ==================================================== */}

      <div className="intervention-detail-card">

        <div className="intervention-detail-icon">

          <Target
            size={18}
          />

        </div>


        <div>

          <span className="intervention-detail-label">

            Objetivo de intervención

          </span>


          <p className="intervention-detail-text">

            {formatText(
              interventionObjective
            )}

          </p>

        </div>

      </div>


      {/* ===================================================
          JUSTIFICACIÓN DE PRIORIDAD
      ==================================================== */}

      <div className="intervention-detail-card">

        <div className="intervention-detail-icon">

          <Info
            size={18}
          />

        </div>


        <div>

          <span className="intervention-detail-label">

            Razón de prioridad

          </span>


          <p className="intervention-detail-text">

            {formatText(
              priorityReason
            )}

          </p>

        </div>

      </div>


      {/* ===================================================
          PAQUETE DE ACCIÓN
      ==================================================== */}

      <div className="intervention-action-card">

        <div className="intervention-action-header">

          <ListChecks
            size={18}
          />

          <span>
            Paquete de acción
          </span>

        </div>


        <div className="intervention-action-list">

          {actionItems.length > 0 ? (

            actionItems.map(
              (
                action,
                index
              ) => (

                <div
                  className="intervention-action-item"
                  key={`${action}-${index}`}
                >

                  <span className="intervention-action-number">

                    {index + 1}

                  </span>


                  <span className="intervention-action-item-text">

                    {action}

                  </span>

                </div>

              )
            )

          ) : (

            <p className="intervention-action-text">

              No hay acciones disponibles
              para esta zona.

            </p>

          )}

        </div>

      </div>


      {/* ===================================================
          INDICADOR DE SEGUIMIENTO
      ==================================================== */}

      <div className="intervention-detail-card">

        <div className="intervention-detail-icon">

          <ClipboardCheck
            size={18}
          />

        </div>


        <div>

          <span className="intervention-detail-label">

            Indicador de seguimiento

          </span>


          <p className="intervention-detail-text">

            {formatText(
              monitoringIndicator
            )}

          </p>

        </div>

      </div>


      {/* ===================================================
          INDICADORES DEL MOTOR
      ==================================================== */}

      <div className="intervention-metrics">


        <div className="intervention-metric">

          <span>
            Ranking
          </span>


          <strong>
            {formatValue(
              rank,
              0
            )}
          </strong>

        </div>


        <div className="intervention-metric">

          <span>
            Operational
          </span>


          <strong>
            {formatValue(
              operationalScore
            )}
          </strong>

        </div>


        <div className="intervention-metric">

          <span>
            Hotspot
          </span>


          <strong>
            {formatValue(
              hotspotScore
            )}
          </strong>

        </div>


        <div className="intervention-metric">

          <span>
            Probabilidad
          </span>


          <strong>
            {formatValue(
              probability
            )}
          </strong>

        </div>

      </div>


      {/* ===================================================
          PLAZO
      ==================================================== */}

      <div className="intervention-timeframe">

        <Clock3
          size={18}
        />


        <div>

          <span>
            Horizonte de prioridad
          </span>


          <strong>
            {formatLabel(
              timeframe
            )}
          </strong>

        </div>

      </div>


      {/* ===================================================
          FUENTE
      ==================================================== */}

      <div className="intervention-footer">

        <span>

          Esta recomendación utiliza los
          atributos producidos por el motor
          de análisis urbano para la zona
          seleccionada.

        </span>

      </div>

    </section>

  );

}