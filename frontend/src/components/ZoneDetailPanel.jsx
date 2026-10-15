
import {
  Activity,
  AlertTriangle,
  BarChart3,
  MapPin,
  Trees,
  X,
} from "lucide-react";

function formatValue(value, decimals = 3) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "number") {
    return value.toFixed(decimals);
  }

  return String(value);
}

function firstAvailable(properties, keys) {
  for (const key of keys) {
    const value = properties?.[key];

    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }

  return null;
}

export default function ZoneDetailPanel({ zone, onClose }) {
  if (!zone) {
    return null;
  }

  const properties = zone.properties || {};

  const zoneId = properties.zone_id ?? "—";
  const level = properties.intervention_level ?? "—";

  const lst = firstAvailable(properties, [
    "LST",
    "lst",
    "lst_mean",
    "mean_lst",
    "lst_celsius",
    "lst_mean_c",
    "land_surface_temperature",
    "temperature_lst",
  ]);

  const ndvi = firstAvailable(properties, [
    "NDVI",
    "ndvi",
    "ndvi_mean",
    "mean_ndvi",
  ]);

  const ndbi = firstAvailable(properties, [
    "NDBI",
    "ndbi",
    "ndbi_mean",
    "mean_ndbi",
  ]);

  const rank = properties.operational_rank;

  return (
    <aside className="zone-detail-panel">
      <div className="zone-detail-header">
        <div>
          <p className="section-label">ZONA SELECCIONADA</p>
          <h3>{zoneId}</h3>
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

      <div className="zone-detail-level">
        <AlertTriangle size={17} />

        <div>
          <span>Nivel de intervención</span>
          <strong>{level}</strong>
        </div>
      </div>

      <div className="zone-detail-section">
        <div className="zone-detail-section-title">
          <BarChart3 size={15} />
          Indicadores ambientales
        </div>

        <div className="zone-environmental-intro">
          <span>LECTURA AMBIENTAL</span>
          <p>
            Indicadores satelitales para comprender temperatura,
            vegetación y superficie construida.
          </p>
        </div>

        <div className="zone-detail-metrics zone-environmental-metrics">
          <div className="zone-metric zone-metric-lst">
            <div className="zone-metric-icon">
              <Activity size={17} />
            </div>
            <span className="zone-metric-code">LST</span>
            <strong>
              {lst === null ? "Sin dato" : formatValue(lst, 2)}
            </strong>
            <small>Temperatura superficial</small>
          </div>

          <div className="zone-metric zone-metric-ndvi">
            <div className="zone-metric-icon">
              <Trees size={17} />
            </div>
            <span className="zone-metric-code">NDVI</span>
            <strong>
              {ndvi === null ? "Sin dato" : formatValue(ndvi, 3)}
            </strong>
            <small>Índice de vegetación</small>
          </div>

          <div className="zone-metric zone-metric-ndbi">
            <div className="zone-metric-icon">
              <MapPin size={17} />
            </div>
            <span className="zone-metric-code">NDBI</span>
            <strong>
              {ndbi === null ? "Sin dato" : formatValue(ndbi, 3)}
            </strong>
            <small>Superficie construida</small>
          </div>

          <div className="zone-metric zone-metric-rank">
            <div className="zone-metric-icon">
              <BarChart3 size={17} />
            </div>
            <span className="zone-metric-code">Ranking</span>
            <strong>{formatValue(rank, 0)}</strong>
            <small>Posición de prioridad</small>
          </div>
        </div>
      </div>

      <div className="zone-detail-footer">
        <Activity size={14} />
        <span>Datos provenientes del motor de análisis urbano.</span>
      </div>
    </aside>
  );
}
