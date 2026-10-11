import { useEffect } from "react";

import {
  MapContainer,
  TileLayer,
  GeoJSON,
  useMap,
} from "react-leaflet";

import L from "leaflet";

import "leaflet/dist/leaflet.css";


/* =========================================================
   CONFIGURACIÓN DEL MAPA
========================================================= */

const DEFAULT_CENTER = [
  7.1193,
  -73.1227,
];

const DEFAULT_ZOOM = 12;


/* =========================================================
   ESTILOS POR NIVEL DE INTERVENCIÓN
========================================================= */

const LEVEL_STYLES = {

  CRITICA: {
    color: "#7f1d1d",
    fillColor: "#ef4444",
    fillOpacity: 0.72,
    weight: 1.5,
  },

  ALTA: {
    color: "#92400e",
    fillColor: "#f59e0b",
    fillOpacity: 0.62,
    weight: 1.2,
  },

  MEDIA: {
    color: "#365314",
    fillColor: "#84cc16",
    fillOpacity: 0.55,
    weight: 1.1,
  },

};


/* =========================================================
   ESTILO POR DEFECTO
========================================================= */

const DEFAULT_ZONE_STYLE = {

  color: "#475569",

  fillColor: "#94a3b8",

  fillOpacity: 0.5,

  weight: 1,

};


/* =========================================================
   OBTENER ESTILO
========================================================= */

function getZoneStyle(feature) {

  const level =
    feature?.properties
      ?.intervention_level;


  return (
    LEVEL_STYLES[level] ||
    DEFAULT_ZONE_STYLE
  );

}


/* =========================================================
   CONTROLADOR DE VISTA
========================================================= */

function MapController({
  geojson,
}) {

  const map =
    useMap();


  useEffect(() => {

    if (
      !geojson ||
      !geojson.features ||
      !geojson.features.length
    ) {

      return;

    }


    const layer =
      L.geoJSON(
        geojson
      );


    const bounds =
      layer.getBounds();


    if (
      !bounds.isValid()
    ) {

      return;

    }


    map.fitBounds(
      bounds,
      {
        padding: [25, 25],

        maxZoom: 14,

        animate: false,
      }
    );

  }, [
    geojson,
    map,
  ]);


  return null;

}


/* =========================================================
   POPUP
========================================================= */

function createPopup(
  feature,
  layer
) {

  const properties =
    feature?.properties || {};


  const zoneId =
    properties.zone_id ?? "—";


  const rank =
    properties.operational_rank ?? "—";


  const level =
    properties.intervention_level ?? "—";


  const type =
    properties.intervention_type ?? "—";


  const condition =
    properties.dominant_condition ?? "—";


  const probability =
    properties.mean_probability;


  const operationalScore =
    properties.operational_score;


  layer.bindPopup(`

    <div style="
      min-width:230px;
      font-family:
        Inter,
        system-ui,
        sans-serif;
    ">

      <div style="
        font-size:10px;
        font-weight:700;
        letter-spacing:.08em;
        color:#6b7280;
        margin-bottom:5px;
      ">
        ZONA DE INTERVENCIÓN
      </div>


      <div style="
        font-size:18px;
        font-weight:700;
        color:#18231d;
        margin-bottom:14px;
      ">
        ${zoneId}
      </div>


      <div style="
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:10px;
        font-size:12px;
        color:#374151;
      ">

        <div>

          <div style="
            color:#7a857e;
            font-size:10px;
          ">
            Ranking
          </div>

          <strong>
            ${rank}
          </strong>

        </div>


        <div>

          <div style="
            color:#7a857e;
            font-size:10px;
          ">
            Nivel
          </div>

          <strong>
            ${level}
          </strong>

        </div>


        <div>

          <div style="
            color:#7a857e;
            font-size:10px;
          ">
            Probabilidad
          </div>

          <strong>
            ${
              probability !== undefined &&
              probability !== null
                ? Number(
                    probability
                  ).toFixed(3)
                : "—"
            }
          </strong>

        </div>


        <div>

          <div style="
            color:#7a857e;
            font-size:10px;
          ">
            Operational
          </div>

          <strong>
            ${
              operationalScore !== undefined &&
              operationalScore !== null
                ? Number(
                    operationalScore
                  ).toFixed(3)
                : "—"
            }
          </strong>

        </div>

      </div>


      <hr style="
        margin:14px 0;
        border:0;
        border-top:1px solid #e5e7eb;
      "/>


      <div style="
        font-size:12px;
        line-height:1.5;
        color:#374151;
      ">

        <div style="
          color:#7a857e;
          font-size:10px;
        ">
          Condición dominante
        </div>

        <strong>
          ${condition}
        </strong>


        <div style="
          margin-top:10px;
          color:#7a857e;
          font-size:10px;
        ">
          Tipo de intervención
        </div>

        <strong>
          ${type}
        </strong>

      </div>

    </div>

  `);

}


/* =========================================================
   EVENTOS DE LAS ZONAS
========================================================= */

function styleAndEvents(
  feature,
  layer,
  onZoneSelect
) {

  /* =======================================================
     ESTILO NORMAL
  ======================================================== */

  layer.setStyle(
    getZoneStyle(
      feature
    )
  );


  /* =======================================================
     POPUP
  ======================================================== */

  createPopup(
    feature,
    layer
  );


  /* =======================================================
     EVENTOS
  ======================================================== */

  layer.on({

    /*
     * No aplicamos ningún cambio visual
     * al pasar el mouse.
     *
     * Esto evita el borde grueso que
     * teníamos anteriormente.
     */

    mouseover: () => {
      // Sin resaltado.
    },


    mouseout: () => {
      // Sin restauración de estilo.
    },


    /* =====================================================
       CLICK
    ====================================================== */

    click: () => {

      /*
       * Un solo clic:
       *
       * 1. Leaflet abre el popup.
       * 2. Seleccionamos la zona.
       * 3. App.jsx actualiza:
       *    - ZoneDetailPanel
       *    - InterventionRecommendation
       *    - selectedZone
       */

      if (
        onZoneSelect
      ) {

        onZoneSelect(
          feature
        );

      }

    },

  });

}


/* =========================================================
   COMPONENTE PRINCIPAL
========================================================= */

export default function InterventionMap({

  geojson,

  loading = false,

  onZoneSelect,

}) {

  return (

    <div className="map-container">


      {/* ===================================================
          MAPA
      ==================================================== */}

      <MapContainer

        center={
          DEFAULT_CENTER
        }

        zoom={
          DEFAULT_ZOOM
        }

        scrollWheelZoom={
          true
        }

        className="intervention-map"

      >


        {/* =================================================
            MAPA BASE
        ================================================== */}

        <TileLayer

          attribution="
            &copy; OpenStreetMap contributors
          "

          url="
            https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
          "

        />


        {/* =================================================
            GEOJSON
        ================================================== */}

        {geojson && (

          <>

            <GeoJSON

              key={
                JSON.stringify(
                  geojson
                )
              }

              data={
                geojson
              }

              style={
                getZoneStyle
              }

              onEachFeature={(
                feature,
                layer
              ) => {

                styleAndEvents(

                  feature,

                  layer,

                  onZoneSelect

                );

              }}

            />


            {/* =============================================
                CONTROLADOR DE VISTA
            ============================================== */}

            <MapController

              geojson={
                geojson
              }

            />

          </>

        )}

      </MapContainer>


      {/* ===================================================
          ACTUALIZANDO
      ==================================================== */}

      {loading && (

        <div className="map-loading">

          <div className="loading-spinner" />

          <span>
            Actualizando mapa...
          </span>

        </div>

      )}


      {/* ===================================================
          SIN RESULTADOS
      ==================================================== */}

      {!loading &&
        geojson &&
        geojson.features &&
        geojson.features.length === 0 && (

          <div className="map-empty">

            <span>
              No hay zonas que coincidan
              con los filtros seleccionados.
            </span>

          </div>

        )}


      {/* ===================================================
          LEYENDA
      ==================================================== */}

      <div className="map-legend">

        <div className="map-legend-title">

          Nivel de intervención

        </div>


        <div className="legend-item">

          <span
            className="
              legend-color
              critical
            "
          />

          <span>
            Crítica
          </span>

        </div>


        <div className="legend-item">

          <span
            className="
              legend-color
              high
            "
          />

          <span>
            Alta
          </span>

        </div>


        <div className="legend-item">

          <span
            className="
              legend-color
              medium
            "
          />

          <span>
            Media
          </span>

        </div>

      </div>

    </div>

  );

}