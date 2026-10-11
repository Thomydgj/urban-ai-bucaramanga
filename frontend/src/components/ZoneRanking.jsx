import {
  AlertTriangle,
  ArrowUpDown,
  MapPin,
} from "lucide-react";


/* =========================================================
   FORMATEAR VALOR
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
   NIVEL
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

export default function ZoneRanking({

  geojson,

  selectedZone,

  onZoneSelect,

}) {

  /* =======================================================
     OBTENER ZONAS
  ======================================================== */

  const features =
    geojson?.features || [];


  /* =======================================================
     ORDENAR POR RANKING OPERACIONAL
  ======================================================== */

  const sortedFeatures = [
    ...features,
  ].sort(
    (
      first,
      second
    ) => {

      const firstRank =
        Number(
          first?.properties
            ?.operational_rank
        );

      const secondRank =
        Number(
          second?.properties
            ?.operational_rank
        );


      /*
       * Si no existe ranking,
       * lo enviamos al final.
       */

      if (
        Number.isNaN(
          firstRank
        )
      ) {

        return 1;

      }


      if (
        Number.isNaN(
          secondRank
        )
      ) {

        return -1;

      }


      return (
        firstRank -
        secondRank
      );

    }
  );


  /* =======================================================
     ESTADO VACÍO
  ======================================================== */

  if (
    sortedFeatures.length === 0
  ) {

    return (

      <section className="zone-ranking">

        <div className="zone-ranking-header">

          <div>

            <p className="section-label">
              PRIORIZACIÓN
            </p>


            <h2>
              Ranking de zonas
            </h2>

          </div>

        </div>


        <div className="zone-ranking-empty">

          <MapPin
            size={24}
          />


          <span>
            No hay zonas que coincidan
            con los filtros seleccionados.
          </span>

        </div>

      </section>

    );

  }


  /* =======================================================
     COMPONENTE
  ======================================================== */

  return (

    <section className="zone-ranking">


      {/* ===================================================
          HEADER
      ==================================================== */}

      <div className="zone-ranking-header">

        <div>

          <p className="section-label">
            PRIORIZACIÓN
          </p>


          <h2>
            Ranking de zonas
          </h2>


          <p className="zone-ranking-description">

            Zonas ordenadas según su
            prioridad operacional.

          </p>

        </div>


        <div className="zone-ranking-count">

          {sortedFeatures.length}

          <span>
            zonas
          </span>

        </div>

      </div>


      {/* ===================================================
          TABLA
      ==================================================== */}

      <div className="zone-ranking-table-wrapper">

        <table className="zone-ranking-table">

          <thead>

            <tr>

              <th>
                <span className="ranking-heading">
                  <ArrowUpDown
                    size={13}
                  />
                  Ranking
                </span>
              </th>


              <th>
                Zona
              </th>


              <th>
                Nivel
              </th>


              <th>
                Operational
              </th>


              <th>
                Hotspot
              </th>


              <th>
                Probabilidad
              </th>


              <th>
                Intervención
              </th>

            </tr>

          </thead>


          <tbody>

            {sortedFeatures.map(
              (
                feature,
                index
              ) => {

                const properties =
                  feature?.properties ||
                  {};


                const zoneId =
                  properties.zone_id ??
                  "—";


                const rank =
                  properties.operational_rank;


                const level =
                  properties.intervention_level ??
                  "—";


                const operationalScore =
                  properties.operational_score;


                const hotspotScore =
                  properties.hotspot_score;


                const probability =
                  properties.mean_probability;


                const interventionType =
                  properties.intervention_type ??
                  "—";


                const isSelected =
                  selectedZone &&
                  String(
                    selectedZone?.properties
                      ?.zone_id
                  ) ===
                  String(
                    zoneId
                  );


                return (

                  <tr

                    key={
                      `${zoneId}-${index}`
                    }

                    className={
                      isSelected
                        ? "zone-ranking-row-selected"
                        : ""
                    }

                    onClick={() => {

                      if (
                        onZoneSelect
                      ) {

                        onZoneSelect(
                          feature
                        );

                      }

                    }}

                  >

                    {/* =============================
                        RANK
                    ============================== */}

                    <td>

                      <div className="zone-rank">

                        {formatValue(
                          rank,
                          0
                        )}

                      </div>

                    </td>


                    {/* =============================
                        ZONA
                    ============================== */}

                    <td>

                      <div className="zone-name">

                        <MapPin
                          size={15}
                        />


                        <strong>
                          {zoneId}
                        </strong>

                      </div>

                    </td>


                    {/* =============================
                        NIVEL
                    ============================== */}

                    <td>

                      <span
                        className={`
                          zone-level
                          ${getLevelClass(
                            level
                          )}
                        `}
                      >

                        {level}

                      </span>

                    </td>


                    {/* =============================
                        OPERATIONAL
                    ============================== */}

                    <td>

                      <strong>
                        {formatValue(
                          operationalScore
                        )}
                      </strong>

                    </td>


                    {/* =============================
                        HOTSPOT
                    ============================== */}

                    <td>

                      {formatValue(
                        hotspotScore
                      )}

                    </td>


                    {/* =============================
                        PROBABILIDAD
                    ============================== */}

                    <td>

                      {formatValue(
                        probability
                      )}

                    </td>


                    {/* =============================
                        INTERVENCIÓN
                    ============================== */}

                    <td>

                      <span className="zone-intervention-type">

                        {interventionType}

                      </span>

                    </td>

                  </tr>

                );

              }
            )}

          </tbody>

        </table>

      </div>

    </section>

  );

}