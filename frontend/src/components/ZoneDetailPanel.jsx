import {
  Activity,
  AlertTriangle,
  BarChart3,
  MapPin,
  Trees,
  X,
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


  return String(
    value
  );

}


/* =========================================================
   FILA DE INFORMACIÓN
========================================================= */

function InfoRow({
  label,
  value,
}) {

  return (

    <div className="zone-detail-row">

      <span className="zone-detail-label">
        {label}
      </span>


      <span className="zone-detail-value">
        {value}
      </span>

    </div>

  );

}


/* =========================================================
   PANEL DE DETALLE DE ZONA
========================================================= */

export default function ZoneDetailPanel({
  zone,
  onClose,
}) {

  /*
   * Si no existe una zona seleccionada,
   * no mostramos el panel.
   */

  if (!zone) {
    return null;
  }


  const properties =
    zone.properties || {};


  /* =======================================================
     IDENTIFICACIÓN
  ======================================================== */

  const zoneId =
    properties.zone_id ?? "—";


  const level =
    properties.intervention_level ?? "—";


  /* =======================================================
     CLASIFICACIÓN DE INTERVENCIÓN
  ======================================================== */

  const interventionType =
    properties.intervention_type ?? "—";


  const condition =
    properties.dominant_condition ?? "—";


  const timeframe =
    properties.priority_timeframe ?? "—";


  /* =======================================================
     INDICADORES
  ======================================================== */

  const probability =
    properties.mean_probability;


  const hotspotScore =
    properties.hotspot_score;


  const operationalScore =
    properties.operational_score;


  /* =======================================================
     INFORMACIÓN TERRITORIAL
  ======================================================== */

  const areaHa =
    properties.area_ha;


  const observations =
    properties.observation_count ??
    properties.observations;


  const rank =
    properties.operational_rank;


  return (

    <aside className="zone-detail-panel">


      {/* ===================================================
          HEADER
      ==================================================== */}

      <div className="zone-detail-header">

        <div>

          <p className="section-label">
            ZONA SELECCIONADA
          </p>


          <h3>
            {zoneId}
          </h3>

        </div>


        <button
          type="button"
          className="zone-detail-close"
          onClick={onClose}
          aria-label="Cerrar detalle"
        >

          <X size={17} />

        </button>

      </div>


      {/* ===================================================
          NIVEL DE INTERVENCIÓN
      ==================================================== */}

      <div className="zone-detail-level">

        <AlertTriangle
          size={17}
        />


        <div>

          <span>
            Nivel de intervención
          </span>


          <strong>
            {level}
          </strong>

        </div>

      </div>


      {/* ===================================================
          INDICADORES
      ==================================================== */}

      <div className="zone-detail-section">

        <div className="zone-detail-section-title">

          <BarChart3
            size={15}
          />

          Indicadores

        </div>


        <div className="zone-detail-metrics">


          {/* PROBABILIDAD */}

          <div className="zone-metric">

            <span>
              Probabilidad
            </span>


            <strong>
              {formatValue(
                probability
              )}
            </strong>

          </div>


          {/* HOTSPOT */}

          <div className="zone-metric">

            <span>
              Hotspot
            </span>


            <strong>
              {formatValue(
                hotspotScore
              )}
            </strong>

          </div>


          {/* OPERATIONAL */}

          <div className="zone-metric">

            <span>
              Operational
            </span>


            <strong>
              {formatValue(
                operationalScore
              )}
            </strong>

          </div>


          {/* RANKING */}

          <div className="zone-metric">

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

        </div>

      </div>


      {/* ===================================================
          INFORMACIÓN TERRITORIAL
      ==================================================== */}

      <div className="zone-detail-section">

        <div className="zone-detail-section-title">

          <MapPin
            size={15}
          />

          Información territorial

        </div>


        <div className="zone-detail-list">


          {/* ÁREA */}

          <InfoRow
            label="Área"
            value={
              areaHa !== undefined &&
              areaHa !== null
                ? `${formatValue(
                    areaHa,
                    2
                  )} ha`
                : "—"
            }
          />


          {/* OBSERVACIONES */}

          <InfoRow
            label="Observaciones"
            value={
              observations !== undefined &&
              observations !== null
                ? formatValue(
                    observations,
                    0
                  )
                : "—"
            }
          />


          {/* CONDICIÓN */}

          <InfoRow
            label="Condición dominante"
            value={
              condition
            }
          />

        </div>

      </div>


      {/* ===================================================
          INTERVENCIÓN
      ==================================================== */}

      <div className="zone-detail-section">

        <div className="zone-detail-section-title">

          <Trees
            size={15}
          />

          Intervención

        </div>


        <div className="zone-detail-list">


          {/* TIPO */}

          <InfoRow
            label="Tipo"
            value={
              interventionType
            }
          />


          {/* PLAZO */}

          <InfoRow
            label="Plazo"
            value={
              timeframe
            }
          />

        </div>

      </div>


      {/* ===================================================
          FOOTER
      ==================================================== */}

      <div className="zone-detail-footer">

        <Activity
          size={14}
        />


        <span>

          Datos provenientes del motor
          de análisis urbano.

        </span>

      </div>


    </aside>

  );

}