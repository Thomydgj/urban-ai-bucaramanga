
import {
  useEffect,
  useState,
} from "react";

import {
  AlertTriangle,
  BarChart3,
  Building2,
  Layers3,
  Map,
  Menu,
  Trees,
  X,
  Activity,
  Target,
  Thermometer,
} from "lucide-react";

import {
  getFilterOptions,
  getMap,
  getSummary,
} from "./services/api";

import InterventionMap
  from "./components/InterventionMap";

import FilterPanel
  from "./components/FilterPanel";

import ZoneDetailPanel
  from "./components/ZoneDetailPanel";

import ZoneRanking
  from "./components/ZoneRanking";

import InterventionRecommendation
  from "./components/InterventionRecommendation";

import BeforeAfterPanel
  from "./components/BeforeAfterPanel";

import "./App.css";

/* =========================================================
   FILTROS VACÍOS
========================================================= */

const EMPTY_FILTERS = {
  intervention_level: null,
  intervention_type: null,
  dominant_condition: null,
  priority_timeframe: null,
};

/* =========================================================
   FORMATEAR NÚMEROS
========================================================= */

function formatNumber(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return new Intl.NumberFormat(
    "es-CO"
  ).format(value);
}

/* =========================================================
   FORMATEAR DECIMALES
========================================================= */

function formatDecimal(
  value,
  decimals = 3
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return Number(value).toFixed(
    decimals
  );
}

/* =========================================================
   FORMATEAR TEXTO DEL MOTOR
========================================================= */

function formatLabel(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /^./,
      (character) =>
        character.toUpperCase()
    );
}

/* =========================================================
   CLASE SEGÚN NIVEL
========================================================= */

function getLevelClass(level) {
  switch (
    String(level).toUpperCase()
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
   KPI CARD
========================================================= */

function KpiCard({
  title,
  value,
  description,
  icon: Icon,
}) {
  return (
    <article className="kpi-card">
      <div className="kpi-card-header">
        <div className="kpi-icon">
          <Icon
            size={20}
            strokeWidth={1.8}
          />
        </div>

        <span className="kpi-title">
          {title}
        </span>
      </div>

      <div className="kpi-value">
        {value}
      </div>

      <div className="kpi-description">
        {description}
      </div>
    </article>
  );
}

/* =========================================================
   FILA DEL DIAGNÓSTICO
========================================================= */

function DiagnosticMetric({
  label,
  value,
}) {
  return (
    <div className="diagnostic-metric">
      <span className="diagnostic-metric-label">
        {label}
      </span>

      <strong className="diagnostic-metric-value">
        {value}
      </strong>
    </div>
  );
}

/* =========================================================
   DIAGNÓSTICO DE ZONA
========================================================= */

function ZoneDiagnosis({ zone }) {
  if (!zone) {
    return null;
  }

  const properties =
    zone?.properties || {};

  const zoneId =
    properties.zone_id ?? "—";

  const level =
    properties.intervention_level ?? "—";

  const condition =
    properties.dominant_condition ?? "—";

  const interventionType =
    properties.intervention_type ?? "—";

  const timeframe =
    properties.priority_timeframe ?? "—";

  const priorityReason =
    properties.priority_reason ?? "—";

  const probability =
    properties.mean_probability;

  const hotspotScore =
    properties.hotspot_score;

  const operationalScore =
    properties.operational_score;

  const rank =
    properties.operational_rank;

  return (
    <section className="zone-diagnosis">
      <div className="zone-diagnosis-header">
        <div>
          <p className="section-label">
            DIAGNÓSTICO
          </p>

          <h2>
            Diagnóstico de {zoneId}
          </h2>

          <p className="zone-diagnosis-description">
            Lectura operacional de las
            condiciones y métricas generadas
            por el motor de análisis urbano.
          </p>
        </div>

        <div
          className={`
            diagnostic-level
            ${getLevelClass(level)}
          `}
        >
          <AlertTriangle size={15} />

          <span>
            {formatLabel(level)}
          </span>
        </div>
      </div>

      <div className="diagnostic-condition">
        <div className="diagnostic-condition-icon">
          <Activity size={20} />
        </div>

        <div>
          <span className="diagnostic-condition-label">
            Condición dominante
          </span>

          <strong className="diagnostic-condition-value">
            {formatLabel(condition)}
          </strong>

          <p>
            El motor clasifica esta zona
            principalmente bajo una condición
            de{" "}

            <strong>
              {formatLabel(condition)}
            </strong>

            {" "}y propone una intervención
            de tipo{" "}

            <strong>
              {formatLabel(interventionType)}
            </strong>.
          </p>
        </div>
      </div>

      <div className="diagnostic-reason">
        <div className="diagnostic-reason-header">
          <Target size={17} />

          <span>
            ¿Por qué se prioriza?
          </span>
        </div>

        <p>
          {priorityReason}
        </p>
      </div>

      <div className="diagnostic-metrics">
        <DiagnosticMetric
          label="Ranking"
          value={
            rank !== null &&
            rank !== undefined
              ? formatNumber(rank)
              : "—"
          }
        />

        <DiagnosticMetric
          label="Probabilidad"
          value={formatDecimal(probability)}
        />

        <DiagnosticMetric
          label="Hotspot"
          value={formatDecimal(hotspotScore)}
        />

        <DiagnosticMetric
          label="Operational"
          value={formatDecimal(operationalScore)}
        />
      </div>

      <div className="diagnostic-timeframe">
        <Thermometer size={17} />

        <div>
          <span>
            Horizonte de prioridad
          </span>

          <strong>
            {formatLabel(timeframe)}
          </strong>
        </div>
      </div>
    </section>
  );
}

/* =========================================================
   APP
========================================================= */

function App() {
  const [
    summary,
    setSummary,
  ] = useState(null);

  const [
    filterOptions,
    setFilterOptions,
  ] = useState(null);

  const [
    filters,
    setFilters,
  ] = useState(EMPTY_FILTERS);

  const [
    mapData,
    setMapData,
  ] = useState(null);

  const [
    selectedZone,
    setSelectedZone,
  ] = useState(null);

  const [
    sidebarOpen,
    setSidebarOpen,
  ] = useState(true);

  const [
    loadingInitial,
    setLoadingInitial,
  ] = useState(true);

  const [
    loadingFiltered,
    setLoadingFiltered,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState(null);

  /* =========================================================
     CARGA INICIAL
  ========================================================= */

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      try {
        setLoadingInitial(true);
        setError(null);

        const [
          summaryData,
          mapResponse,
          options,
        ] = await Promise.all([
          getSummary(),
          getMap(),
          getFilterOptions(),
        ]);

        if (cancelled) {
          return;
        }

        setSummary(summaryData);

        let parsedMap;

        if (
          typeof mapResponse?.geojson ===
          "string"
        ) {
          parsedMap = JSON.parse(
            mapResponse.geojson
          );
        } else {
          parsedMap = mapResponse?.geojson;
        }

        setMapData(parsedMap);
        setFilterOptions(options);
      } catch (err) {
        console.error(
          "Error cargando dashboard:",
          err
        );

        if (!cancelled) {
          setError(
            err?.message ||
            "No fue posible cargar el dashboard."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingInitial(false);
        }
      }
    }

    loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  /* =========================================================
     APLICAR FILTROS
  ========================================================= */

  useEffect(() => {
    if (loadingInitial) {
      return;
    }

    let cancelled = false;

    const hasFilters =
      Object.values(filters).some(
        (value) =>
          value !== null &&
          value !== undefined &&
          value !== ""
      );

    async function loadData() {
      try {
        setLoadingFiltered(true);
        setError(null);
        setSelectedZone(null);

        const requestFilters =
          hasFilters
            ? filters
            : undefined;

        const [
          summaryData,
          mapResponse,
        ] = await Promise.all([
          getSummary(requestFilters),
          getMap(requestFilters),
        ]);

        if (cancelled) {
          return;
        }

        setSummary(summaryData);

        let parsedMap;

        if (
          typeof mapResponse?.geojson ===
          "string"
        ) {
          parsedMap = JSON.parse(
            mapResponse.geojson
          );
        } else {
          parsedMap = mapResponse?.geojson;
        }

        setMapData(parsedMap);
      } catch (err) {
        console.error(
          "Error actualizando datos:",
          err
        );

        if (!cancelled) {
          setError(
            err?.message ||
            "No fue posible actualizar los datos."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingFiltered(false);
        }
      }
    }

    loadData();

    return () => {
      cancelled = true;
    };
  }, [filters, loadingInitial]);

  /* =========================================================
     CAMBIO DE FILTROS
  ========================================================= */

  function handleFiltersChange(nextFilters) {
    setSelectedZone(null);
    setFilters(nextFilters);
  }

  function handleClearFilters() {
    setSelectedZone(null);
    setFilters(EMPTY_FILTERS);
  }

  /* =========================================================
     SELECCIÓN DE ZONA
  ========================================================= */

  function handleZoneSelect(zone) {
    setSelectedZone(zone);
  }

  function handleZoneClose() {
    setSelectedZone(null);
  }

  /* =========================================================
     CARGA
  ========================================================= */

  if (loadingInitial) {
    return (
      <div className="app-loading">
        <div className="loading-spinner" />

        <p>
          Cargando Urban AI...
        </p>
      </div>
    );
  }

  /* =========================================================
     DASHBOARD
  ========================================================= */

  return (
    <div className="app-shell">
      <aside
        className={`sidebar ${
          sidebarOpen
            ? "sidebar-expanded"
            : "sidebar-collapsed"
        }`}
      >
        <div className="sidebar-brand">
          <div className="brand-mark">
            <Layers3 size={23} />
          </div>

          {sidebarOpen && (
            <div className="brand-copy">
              <strong>URBAN AI</strong>

              <span>
                Bucaramanga
              </span>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          <button
            type="button"
            className="nav-item active"
          >
            <Map size={19} />

            {sidebarOpen && (
              <span>
                Dashboard
              </span>
            )}
          </button>

          <button
            type="button"
            className="nav-item"
          >
            <Layers3 size={19} />

            {sidebarOpen && (
              <span>
                Zonas prioritarias
              </span>
            )}
          </button>

          <button
            type="button"
            className="nav-item"
          >
            <Trees size={19} />

            {sidebarOpen && (
              <span>
                Intervenciones
              </span>
            )}
          </button>
        </nav>

        {sidebarOpen && (
          <div className="sidebar-footer">
            <span>
              Urban AI
            </span>

            <small>
              Sistema de análisis urbano
            </small>
          </div>
        )}
      </aside>

      <div
        className={`main ${
          sidebarOpen
            ? "main-expanded"
            : "main-full"
        }`}
      >
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="menu-button"
              onClick={() =>
                setSidebarOpen(!sidebarOpen)
              }
              aria-label="Alternar menú"
            >
              {sidebarOpen ? (
                <X size={21} />
              ) : (
                <Menu size={21} />
              )}
            </button>

            <div>
              <div className="page-kicker">
                ANÁLISIS URBANO
              </div>

              <h1>
                Dashboard de intervención
              </h1>
            </div>
          </div>

          <div className="topbar-status">
            <span className="status-dot" />

            <span>
              {loadingFiltered
                ? "Actualizando"
                : "Motor conectado"}
            </span>
          </div>
        </header>

        <main className="content">
          {error && (
            <div className="error-banner" role="alert">
              <AlertTriangle size={18} />

              <span>
                {error}
              </span>
            </div>
          )}

          <section className="intro">
            <div>
              <p className="section-label">
                RESUMEN OPERATIVO
              </p>

              <h2>
                Zonas prioritarias de intervención
              </h2>

              <p className="intro-description">
                Vista general de las zonas
                identificadas por el motor
                de análisis urbano.
              </p>
            </div>
          </section>

          <FilterPanel
            options={filterOptions}
            filters={filters}
            onChange={handleFiltersChange}
            onClear={handleClearFilters}
            loading={loadingFiltered}
          />

          <section
            className={`kpi-grid ${
              loadingFiltered
                ? "content-updating"
                : ""
            }`}
          >
            <KpiCard
              title="Zonas prioritarias"
              value={formatNumber(summary?.zones)}
              description="Zonas de intervención identificadas"
              icon={Map}
            />

            <KpiCard
              title="Observaciones"
              value={formatNumber(summary?.observations)}
              description="Observaciones prioritarias analizadas"
              icon={BarChart3}
            />

            <KpiCard
              title="Área total"
              value={`${formatNumber(summary?.area_ha)} ha`}
              description="Área cubierta por las zonas"
              icon={Building2}
            />

            <KpiCard
              title="Probabilidad media"
              value={formatDecimal(summary?.mean_probability, 3)}
              description="Probabilidad media ponderada"
              icon={AlertTriangle}
            />

            <KpiCard
              title="Hotspot score"
              value={formatDecimal(summary?.mean_hotspot_score, 3)}
              description="Índice medio ponderado"
              icon={Layers3}
            />

            <KpiCard
              title="Operational score"
              value={formatDecimal(summary?.mean_operational_score, 3)}
              description="Prioridad operacional media"
              icon={Trees}
            />
          </section>

          <section className="map-section">
            <div className="map-section-header">
              <div>
                <p className="section-label">
                  ANÁLISIS ESPACIAL
                </p>

                <h2>
                  Mapa de intervención
                </h2>
              </div>

              <div className="map-zone-count">
                {formatNumber(summary?.zones)}
                {" zonas"}
              </div>
            </div>

            <div className="map-workspace">
              <InterventionMap
                geojson={mapData}
                loading={loadingFiltered}
                selectedZone={selectedZone}
                onZoneSelect={handleZoneSelect}
              />

              <ZoneDetailPanel
                zone={selectedZone}
                onClose={handleZoneClose}
              />
            </div>
          </section>

          <ZoneRanking
            geojson={mapData}
            selectedZone={selectedZone}
            onZoneSelect={handleZoneSelect}
          />

          <ZoneDiagnosis
            zone={selectedZone}
          />

          <InterventionRecommendation
            zone={selectedZone}
          />

          {/* Flujo de análisis y comparación conceptual */}
          <BeforeAfterPanel />

          {!selectedZone && (
            <section
              className="
                dashboard-placeholder
                secondary
              "
            >
              <div className="placeholder-grid">
                <div>
                  <Layers3 size={24} />

                  <h3>
                    Filtros
                  </h3>

                  <p>
                    Nivel, tipo, condición
                    y plazo.
                  </p>
                </div>

                <div>
                  <BarChart3 size={24} />

                  <h3>
                    Zonas
                  </h3>

                  <p>
                    Ranking y detalle
                    operacional.
                  </p>
                </div>

                <div>
                  <Trees size={24} />

                  <h3>
                    Intervenciones
                  </h3>

                  <p>
                    Recomendaciones y
                    paquetes de acción.
                  </p>
                </div>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
