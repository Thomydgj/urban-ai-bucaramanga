
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Building2,
  Layers3,
  Map as MapIcon,
  Menu,
  Trees,
  X,
  ArrowRight,
  ScanSearch,
  Leaf,
} from "lucide-react";

import { getFilterOptions, getMap, getSummary } from "./services/api";
import InterventionMap from "./components/InterventionMap";
import FilterPanel from "./components/FilterPanel";
import ZoneDetailPanel from "./components/ZoneDetailPanel";
import ZoneRanking from "./components/ZoneRanking";
import InterventionRecommendation from "./components/InterventionRecommendation";
import BeforeAfterPanel from "./components/BeforeAfterPanel";
import "./App.css";

const EMPTY_FILTERS = {
  intervention_level: null,
  intervention_type: null,
  dominant_condition: null,
  priority_timeframe: null,
};

const CHART_COLORS = {
  critical: "#e85d4f",
  high: "#f28c45",
  medium: "#36a879",
  low: "#36a879",
  blue: "#3984d6",
  teal: "#24a69a",
  purple: "#8b70cf",
};

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "—";

  return new Intl.NumberFormat("es-CO", {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatLabel(value) {
  if (value === null || value === undefined || value === "") return "—";

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (character) => character.toUpperCase());
}

function getFeatureProperties(feature) {
  return feature?.properties ?? {};
}

function getChartData(geojson) {
  const features = Array.isArray(geojson?.features)
    ? geojson.features
    : [];

  const levels = [
    { label: "Crítica", key: "CRITICA", color: CHART_COLORS.critical },
    { label: "Alta", key: "ALTA", color: CHART_COLORS.high },
    { label: "Media", key: "MEDIA", color: CHART_COLORS.medium },
    { label: "Baja", key: "BAJA", color: CHART_COLORS.low },
  ];

  const priorities = levels.map((item) => ({
    ...item,
    value: features.filter((feature) => {
      const level = String(
        getFeatureProperties(feature).intervention_level ?? ""
      )
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toUpperCase();

      return level === item.key;
    }).length,
  }));

  const typeCounts = new Map();
  const conditionCounts = new Map();

  features.forEach((feature) => {
    const properties = getFeatureProperties(feature);
    const type = properties.intervention_type;
    const condition = properties.dominant_condition;

    if (type !== null && type !== undefined && String(type).trim()) {
      const key = String(type).trim();
      typeCounts.set(key, (typeCounts.get(key) ?? 0) + 1);
    }

    if (
      condition !== null &&
      condition !== undefined &&
      String(condition).trim()
    ) {
      const key = String(condition).trim();
      conditionCounts.set(key, (conditionCounts.get(key) ?? 0) + 1);
    }
  });

  const palette = [
    CHART_COLORS.blue,
    CHART_COLORS.teal,
    CHART_COLORS.high,
    CHART_COLORS.low,
    CHART_COLORS.purple,
  ];

  const toRows = (counts) =>
    [...counts.entries()]
      .map(([label, value], index) => ({
        label: formatLabel(label),
        value,
        color: palette[index % palette.length],
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);

  return {
    total: features.length,
    priorities,
    types: toRows(typeCounts),
    conditions: toRows(conditionCounts),
  };
}

function KpiCard({ title, value, description, icon: Icon }) {
  return (
    <article className="kpi-card">
      <div className="kpi-card-header">
        <div className="kpi-icon">
          <Icon size={20} strokeWidth={1.8} />
        </div>
        <span className="kpi-title">{title}</span>
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-description">{description}</div>
    </article>
  );
}

function ChartPanel({ title, subtitle, children }) {
  return (
    <section className="chart-panel">
      <div className="chart-panel-heading">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function ChartLegendDot({ color }) {
  return (
    <span
      className="chart-legend-dot"
      style={{ background: color }}
    />
  );
}

function HorizontalBarChart({
  data,
  emptyMessage = "No hay datos para mostrar en esta selección.",
}) {
  const max = Math.max(1, ...data.map((item) => item.value));

  if (!data.length || !data.some((item) => item.value > 0)) {
    return <p className="chart-empty">{emptyMessage}</p>;
  }

  return (
    <div className="priority-chart">
      {data.map((item) => (
        <div className="priority-row" key={item.key ?? item.label}>
          <div className="priority-row-label">
            <ChartLegendDot color={item.color} />
            <span>{item.label}</span>
            <strong>{formatNumber(item.value)}</strong>
          </div>

          <div
            className="chart-track"
            role="img"
            aria-label={`${item.label}: ${item.value}`}
          >
            <div
              className="chart-bar"
              style={{
                width: `${(item.value / max) * 100}%`,
                background: item.color,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function PriorityPieChart({ data }) {
  const priorityData = data.filter(
    (item) =>
      item.key !== "BAJA" &&
      item.label.toLowerCase() !== "baja" &&
      item.value > 0
  );

  const total = priorityData.reduce((sum, item) => sum + item.value, 0);

  if (total === 0) {
    return (
      <p className="chart-empty">
        No hay zonas clasificadas por nivel de prioridad.
      </p>
    );
  }

  let currentAngle = 0;

  const slices = priorityData.map((item) => {
    const startAngle = currentAngle;
    currentAngle += (item.value / total) * 360;

    return {
      ...item,
      startAngle,
      endAngle: currentAngle,
      percentage: ((item.value / total) * 100).toFixed(1),
    };
  });

  const polarToCartesian = (angle) => {
    const radians = ((angle - 90) * Math.PI) / 180;

    return {
      x: 150 + 110 * Math.cos(radians),
      y: 150 + 110 * Math.sin(radians),
    };
  };

  const describeSlice = (slice) => {
    const start = polarToCartesian(slice.startAngle);
    const end = polarToCartesian(slice.endAngle);
    const largeArc = slice.endAngle - slice.startAngle > 180 ? 1 : 0;

    return [
      "M 150 150",
      `L ${start.x} ${start.y}`,
      `A 110 110 0 ${largeArc} 1 ${end.x} ${end.y}`,
      "Z",
    ].join(" ");
  };

  return (
    <div className="priority-pie-layout">
      <svg
        className="priority-pie"
        viewBox="0 0 300 300"
        role="img"
        aria-label={`Distribución de ${total} zonas por nivel de prioridad`}
      >
        {slices.map((slice) => (
          <path
            key={slice.label}
            d={describeSlice(slice)}
            fill={slice.color}
            stroke="white"
            strokeWidth="2"
          >
            <title>
              {slice.label}: {slice.value} zonas ({slice.percentage}%)
            </title>
          </path>
        ))}

        <circle cx="150" cy="150" r="63" fill="white" />

        <text
          x="150"
          y="143"
          textAnchor="middle"
          fontSize="30"
          fontWeight="700"
          fill="#173b35"
        >
          {total}
        </text>

        <text
          x="150"
          y="166"
          textAnchor="middle"
          fontSize="12"
          fill="#71827d"
        >
          Zonas
        </text>
      </svg>

      <div className="priority-pie-legend">
        {slices.map((slice) => (
          <div className="priority-pie-item" key={slice.label}>
            <ChartLegendDot color={slice.color} />
            <span>{slice.label}</span>
            <strong>{slice.value}</strong>
            <small>{slice.percentage}%</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [activeSection, setActiveSection] = useState("dashboard");
  const [summary, setSummary] = useState(null);
  const [filterOptions, setFilterOptions] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [mapData, setMapData] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingFiltered, setLoadingFiltered] = useState(false);
  const [error, setError] = useState(null);

  // Detecta la sección que ocupa la zona principal de la pantalla.
  useEffect(() => {
    const sectionIds = ["dashboard", "zonas", "intervencion"];

    const updateActiveSection = () => {
      const activationLine = window.innerHeight * 0.35;
      let currentSection = "dashboard";

      sectionIds.forEach((id) => {
        const element = document.getElementById(id);

        if (!element) return;

        const rect = element.getBoundingClientRect();

        if (rect.top <= activationLine) {
          currentSection = id;
        }
      });

      // Si se ha llegado al final de la página, activa la última sección.
      const atPageBottom =
        window.innerHeight + window.scrollY >=
        document.documentElement.scrollHeight - 5;

      if (atPageBottom) {
        currentSection = "intervencion";
      }

      setActiveSection((previous) =>
        previous === currentSection ? previous : currentSection
      );
    };

    window.addEventListener("scroll", updateActiveSection, { passive: true });
    window.addEventListener("resize", updateActiveSection);

    updateActiveSection();

    return () => {
      window.removeEventListener("scroll", updateActiveSection);
      window.removeEventListener("resize", updateActiveSection);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      try {
        setLoadingInitial(true);
        setError(null);

        const [summaryData, mapResponse, options] = await Promise.all([
          getSummary(),
          getMap(),
          getFilterOptions(),
        ]);

        if (cancelled) return;

        setSummary(summaryData);

        const parsedMap =
          typeof mapResponse?.geojson === "string"
            ? JSON.parse(mapResponse.geojson)
            : mapResponse?.geojson;

        setMapData(parsedMap);
        setFilterOptions(options);
      } catch (err) {
        console.error("Error cargando dashboard:", err);

        if (!cancelled) {
          setError(err?.message || "No fue posible cargar el dashboard.");
        }
      } finally {
        if (!cancelled) setLoadingInitial(false);
      }
    }

    loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (loadingInitial) return undefined;

    let cancelled = false;

    const hasFilters = Object.values(filters).some(
      (value) => value !== null && value !== undefined && value !== ""
    );

    async function loadData() {
      try {
        setLoadingFiltered(true);
        setError(null);
        setSelectedZone(null);

        const requestFilters = hasFilters ? filters : undefined;

        const [summaryData, mapResponse] = await Promise.all([
          getSummary(requestFilters),
          getMap(requestFilters),
        ]);

        if (cancelled) return;

        setSummary(summaryData);

        const parsedMap =
          typeof mapResponse?.geojson === "string"
            ? JSON.parse(mapResponse.geojson)
            : mapResponse?.geojson;

        setMapData(parsedMap);
      } catch (err) {
        console.error("Error actualizando datos:", err);

        if (!cancelled) {
          setError(err?.message || "No fue posible actualizar los datos.");
        }
      } finally {
        if (!cancelled) setLoadingFiltered(false);
      }
    }

    loadData();

    return () => {
      cancelled = true;
    };
  }, [filters, loadingInitial]);

  const chartData = useMemo(() => getChartData(mapData), [mapData]);

  function handleFiltersChange(nextFilters) {
    setSelectedZone(null);
    setFilters(nextFilters);
  }

  function handleClearFilters() {
    setSelectedZone(null);
    setFilters(EMPTY_FILTERS);
  }

  function navigateToSection(sectionId) {
  setActiveSection(sectionId);

  document.getElementById(sectionId)?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });

  if (window.matchMedia("(max-width: 768px)").matches) {
    setSidebarOpen(false);
  }
}

  if (loadingInitial) {
    return (
      <div className="app-loading">
        <div className="loading-spinner" />
        <p>Cargando Eco Mapa...</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside
        className={`sidebar ${
          sidebarOpen ? "sidebar-expanded" : "sidebar-collapsed"
        }`}
      >
        <div className="sidebar-brand">
          <div className="brand-mark">
            <Layers3 size={23} />
          </div>

          {sidebarOpen && (
            <div className="brand-copy">
              <strong>ECO MAPA</strong>
              <span>Bucaramanga</span>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          <button
            type="button"
            className={`nav-item ${
              activeSection === "dashboard" ? "active" : ""
            }`}
            onClick={() => navigateToSection("dashboard")}
          >
            <MapIcon size={19} />
            {sidebarOpen && <span>Dashboard</span>}
          </button>

          <button
            type="button"
            className={`nav-item ${
              activeSection === "zonas" ? "active" : ""
            }`}
            onClick={() => navigateToSection("zonas")}
          >
            <Layers3 size={19} />
            {sidebarOpen && <span>Zonas prioritarias</span>}
          </button>

          <button
            type="button"
            className={`nav-item ${
              activeSection === "intervencion" ? "active" : ""
            }`}
            onClick={() => navigateToSection("intervencion")}
          >
            <Trees size={19} />
            {sidebarOpen && <span>Intervención IA</span>}
          </button>
        </nav>

        {sidebarOpen && (
          <div className="sidebar-footer">
            <span>Eco Mapa</span>
            <small>Inteligencia territorial urbana</small>
          </div>
        )}
      </aside>
      
      {sidebarOpen && window.matchMedia("(max-width: 768px)").matches && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className={`main ${sidebarOpen ? "main-expanded" : "main-full"}`}>
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="menu-button"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label="Alternar menú"
            >
              {sidebarOpen ? <X size={21} /> : <Menu size={21} />}
            </button>

            <div>
              <div className="page-kicker">ANÁLISIS TERRITORIAL</div>
              <h1>Eco Mapa Bucaramanga</h1>
            </div>
          </div>

          <div className="topbar-status">
            <span className="status-dot" />
            <span>
              {loadingFiltered ? "Actualizando" : "Motor conectado"}
            </span>
          </div>
        </header>

        <main className="content">
          {error && (
            <div className="error-banner" role="alert">
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}

          <section className="intro hero">
            <div className="hero-content">
              <div className="hero-brand">
                <span className="hero-brand-mark">
                  <Layers3 size={21} />
                </span>
                <span>
                  <strong>ECO MAPA</strong>
                  <small>BUCARAMANGA · TERRITORIO INTELIGENTE</small>
                </span>
              </div>

              <p className="hero-eyebrow">
                DATOS QUE IMPULSAN MEJORES DECISIONES
              </p>

              <h2>
                Una ciudad mejor empieza por saber <em>dónde actuar.</em>
              </h2>

              <p className="intro-description">
                Explora el territorio, identifica zonas prioritarias y convierte
                los datos geoespaciales en decisiones para una ciudad más
                sostenible.
              </p>

              <div className="hero-actions">
                <button
                  type="button"
                  className="hero-primary"
                  onClick={() =>
                    document.querySelector(".map-section")?.scrollIntoView({
                      behavior: "smooth",
                    })
                  }
                >
                  Explorar el mapa <ArrowRight size={17} />
                </button>
              </div>

              <div
                className="hero-capabilities"
                aria-label="Funciones de la plataforma"
              >
                <div>
                  <span className="hero-capability-icon">
                    <ScanSearch size={17} />
                  </span>
                  <span>
                    <strong>Segmentación</strong>
                    <small>Cobertura urbana</small>
                  </span>
                </div>

                <div>
                  <span className="hero-capability-icon">
                    <BarChart3 size={17} />
                  </span>
                  <span>
                    <strong>Indicadores</strong>
                    <small>Datos por zona</small>
                  </span>
                </div>

                <div>
                  <span className="hero-capability-icon">
                    <Leaf size={17} />
                  </span>
                  <span>
                    <strong>Intervenciones</strong>
                    <small>Acciones sugeridas</small>
                  </span>
                </div>
              </div>
            </div>

            <div className="hero-image-credit">BUCARAMANGA · COLOMBIA</div>
          </section>

          <section
            id="dashboard"
            className={`kpi-grid ${
              loadingFiltered ? "content-updating" : ""
            }`}
          >
            <KpiCard
              title="Zonas prioritarias"
              value={formatNumber(summary?.zones)}
              description="Zonas identificadas para intervención"
              icon={MapIcon}
            />

            <KpiCard
              title="Observaciones"
              value={formatNumber(summary?.observations)}
              description="Registros analizados por el sistema"
              icon={BarChart3}
            />

            <KpiCard
              title="Área total"
              value={`${formatNumber(summary?.area_ha)} ha`}
              description="Superficie cubierta por las zonas"
              icon={Building2}
            />
          </section>

          <section
            className={`analytics-grid ${
              loadingFiltered ? "content-updating" : ""
            }`}
          >
            <ChartPanel
              title="Nivel de prioridad"
              subtitle={`${formatNumber(chartData.total)} zonas en la selección actual`}
            >
              <PriorityPieChart data={chartData.priorities} />
              <div className="chart-footnote">
                Distribución de las zonas visibles según su nivel de
                intervención.
              </div>
            </ChartPanel>

            <ChartPanel
              title="Tipos de intervención"
              subtitle="Categorías más frecuentes en las zonas filtradas"
            >
              <HorizontalBarChart data={chartData.types} />
              <div className="chart-footnote">
                Los valores corresponden al número de zonas del GeoJSON actual.
              </div>
            </ChartPanel>
          </section>

          <FilterPanel
            options={filterOptions}
            filters={filters}
            onChange={handleFiltersChange}
            onClear={handleClearFilters}
            loading={loadingFiltered}
          />

          <section className="map-section">
            <div className="map-section-header">
              <div>
                <p className="section-label">ANÁLISIS ESPACIAL</p>
                <h2>Explora el mapa de intervención</h2>
                <p className="map-section-description">
                  Selecciona una zona para consultar sus detalles y las
                  acciones sugeridas.
                </p>
              </div>

              <div className="map-zone-count">
                {formatNumber(summary?.zones)} zonas
              </div>
            </div>

            <div className="map-workspace">
              <InterventionMap
                geojson={mapData}
                loading={loadingFiltered}
                selectedZone={selectedZone}
                onZoneSelect={setSelectedZone}
              />

              <ZoneDetailPanel
                zone={selectedZone}
                onClose={() => setSelectedZone(null)}
              />
            </div>
          </section>

          <InterventionRecommendation zone={selectedZone} />

          <section id="zonas">
            <ZoneRanking
              geojson={mapData}
              selectedZone={selectedZone}
              onZoneSelect={setSelectedZone}
            />
          </section>

          <section id="intervencion">
            <BeforeAfterPanel />
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
