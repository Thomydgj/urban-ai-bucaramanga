
import { useMemo, useState } from "react";
import {
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Info,
  ArrowUpRight,
  ShieldAlert,
  ShieldCheck,
  Activity,
} from "lucide-react";

function getLevel(level) {
  const normalized = String(level ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase();

  if (normalized === "CRITICA") {
    return {
      label: "Crítica",
      key: "critical",
      description: "Zona situada en el nivel de prioridad crítica.",
    };
  }

  if (normalized === "ALTA") {
    return {
      label: "Alta",
      key: "high",
      description: "Zona situada en el nivel de prioridad alta.",
    };
  }

  if (normalized === "MEDIA") {
    return {
      label: "Media",
      key: "medium",
      description: "Zona situada en el nivel de prioridad media.",
    };
  }

  return {
    label: level || "Sin clasificar",
    key: "default",
    description: "No hay un nivel de prioridad disponible.",
  };
}

function formatValue(value, decimals = 3) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toFixed(decimals)
    : String(value);
}

function humanizeIntervention(value) {
  const labels = {
    INTERVENCION_INTEGRAL: "Intervención integral",
    DIAGNOSTICO_COMPLEMENTARIO: "Diagnóstico complementario",
  };

  const key = String(value ?? "").trim().toUpperCase();

  return (
    labels[key] ||
    (key
      ? key.toLowerCase().replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase())
      : "Por definir")
  );
}

export default function ZoneRanking({
  geojson,
  selectedZone,
  onZoneSelect,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [levelFilter, setLevelFilter] = useState("TODOS");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);

  const features = geojson?.features || [];

  const sortedFeatures = useMemo(
    () =>
      [...features].sort((a, b) => {
        const rankA = Number(a?.properties?.operational_rank);
        const rankB = Number(b?.properties?.operational_rank);

        if (!Number.isFinite(rankA)) return 1;
        if (!Number.isFinite(rankB)) return -1;

        return rankA - rankB;
      }),
    [features]
  );

  const counts = useMemo(() => {
    const result = { CRITICA: 0, ALTA: 0, MEDIA: 0 };

    sortedFeatures.forEach((feature) => {
      const level = String(
        feature?.properties?.intervention_level ?? ""
      )
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toUpperCase();

      if (level in result) {
        result[level] += 1;
      }
    });

    return result;
  }, [sortedFeatures]);

  const filteredFeatures = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return sortedFeatures.filter((feature) => {
      const properties = feature?.properties || {};
      const zoneId = String(properties.zone_id ?? "").toLowerCase();

      const level = String(properties.intervention_level ?? "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toUpperCase();

      return (
        (!query || zoneId.includes(query)) &&
        (levelFilter === "TODOS" || level === levelFilter)
      );
    });
  }, [sortedFeatures, searchTerm, levelFilter]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredFeatures.length / pageSize)
  );

  const safePage = Math.min(page, totalPages);

  const visibleFeatures = filteredFeatures.slice(
    (safePage - 1) * pageSize,
    safePage * pageSize
  );

  const changeSearch = (value) => {
    setSearchTerm(value);
    setPage(1);
  };

  const changeLevel = (value) => {
    setLevelFilter(value);
    setPage(1);
  };

  return (
    <section className="zone-ranking zone-ranking-redesign">
      <header className="zr-hero">
        <div className="zr-hero-copy">
          <p className="section-label">PRIORIZACIÓN URBANA</p>

          <h2>¿Dónde debemos actuar primero?</h2>

          <p>
            Explora las zonas según su nivel de prioridad y consulta la
            intervención sugerida.
          </p>
        </div>

        <div className="zr-total">
          <strong>{filteredFeatures.length}</strong>
          <span>
            zonas
            <br />
            en la lista
          </span>
        </div>
      </header>

      <div className="zr-summary-grid">
        <button
          type="button"
          className={`zr-summary-card zr-summary-all ${
            levelFilter === "TODOS" ? "is-active" : ""
          }`}
          onClick={() => changeLevel("TODOS")}
        >
          <span className="zr-summary-icon">
            <MapPin size={19} />
          </span>
          <span className="zr-summary-text">
            <strong>{sortedFeatures.length}</strong>
            <small>Todas las zonas</small>
          </span>
        </button>

        <button
          type="button"
          className={`zr-summary-card zr-summary-critical ${
            levelFilter === "CRITICA" ? "is-active" : ""
          }`}
          onClick={() => changeLevel("CRITICA")}
        >
          <span className="zr-summary-icon">
            <ShieldAlert size={19} />
          </span>
          <span className="zr-summary-text">
            <strong>{counts.CRITICA}</strong>
            <small>Prioridad crítica</small>
          </span>
        </button>

        <button
          type="button"
          className={`zr-summary-card zr-summary-high ${
            levelFilter === "ALTA" ? "is-active" : ""
          }`}
          onClick={() => changeLevel("ALTA")}
        >
          <span className="zr-summary-icon">
            <ArrowUpRight size={19} />
          </span>
          <span className="zr-summary-text">
            <strong>{counts.ALTA}</strong>
            <small>Prioridad alta</small>
          </span>
        </button>

        <button
          type="button"
          className={`zr-summary-card zr-summary-medium ${
            levelFilter === "MEDIA" ? "is-active" : ""
          }`}
          onClick={() => changeLevel("MEDIA")}
        >
          <span className="zr-summary-icon">
            <ShieldCheck size={19} />
          </span>
          <span className="zr-summary-text">
            <strong>{counts.MEDIA}</strong>
            <small>Prioridad media</small>
          </span>
        </button>
      </div>

      <div className="zr-toolbar">
        <div className="zr-toolbar-title">
          <Activity size={17} />
          <span>Listado de zonas prioritarias</span>
        </div>

        <div className="zone-ranking-tools zr-tools-compact">
          <div
            className={`zone-ranking-search-wrap ${
              searchOpen ? "is-open" : ""
            }`}
          >
            {searchOpen && (
              <label className="zone-ranking-search">
                <Search size={16} aria-hidden="true" />
                <input
                  autoFocus
                  type="search"
                  value={searchTerm}
                  onChange={(event) => changeSearch(event.target.value)}
                  placeholder="Buscar ID de zona"
                  aria-label="Buscar zona por ID"
                />
              </label>
            )}

            <button
              type="button"
              className="zone-ranking-search-toggle"
              onClick={() => {
                if (searchOpen) {
                  setSearchOpen(false);
                  changeSearch("");
                } else {
                  setSearchOpen(true);
                }
              }}
              aria-label={
                searchOpen ? "Cerrar búsqueda por ID" : "Buscar zona por ID"
              }
              title={searchOpen ? "Cerrar búsqueda" : "Buscar por ID"}
              aria-expanded={searchOpen}
            >
              {searchOpen ? <X size={17} /> : <Search size={17} />}
            </button>
          </div>

          <label className="zone-ranking-page-size">
            Mostrar
            <select
              value={pageSize}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(1);
              }}
              aria-label="Cantidad de zonas por página"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
            </select>
          </label>
        </div>
      </div>

      {filteredFeatures.length === 0 ? (
        <div className="zone-ranking-empty">
          <MapPin size={24} />
          <span>
            No hay zonas que coincidan con la búsqueda o los filtros.
          </span>
        </div>
      ) : (
        <>
          <div className="zr-zone-list">
            {visibleFeatures.map((feature, index) => {
              const properties = feature?.properties || {};
              const zoneId = properties.zone_id ?? "Zona sin ID";

              const rank =
                properties.operational_rank ??
                (index + 1 + (safePage - 1) * pageSize);

              const level = getLevel(properties.intervention_level);
              const score = properties.operational_score;

              const isSelected =
                selectedZone &&
                String(selectedZone?.properties?.zone_id) === String(zoneId);

              const scoreNumber = Number(score);

              const scoreWidth = Number.isFinite(scoreNumber)
                ? `${Math.max(0, Math.min(100, scoreNumber * 100))}%`
                : "0%";

              return (
                <button
                  type="button"
                  key={`${zoneId}-${rank}`}
                  className={`zr-zone-card ${level.key} ${
                    isSelected ? "is-selected" : ""
                  }`}
                  onClick={() => onZoneSelect?.(feature)}
                  aria-pressed={Boolean(isSelected)}
                >
                  <span className="zr-rank-badge">{rank}</span>

                  <span className="zr-zone-main">
                    <span className="zr-zone-topline">
                      <strong>{zoneId}</strong>
                      <span className={`zr-level-pill ${level.key}`}>
                        {level.label}
                      </span>
                    </span>

                    <span className="zr-zone-subtitle">
                      {humanizeIntervention(properties.intervention_type)}
                    </span>

                    <span className="zr-score-area">
                      <span className="zr-score-label">
                        Índice de prioridad
                        <span className="zr-tooltip-wrap">
                          <Info
                            size={13}
                            tabIndex={0}
                            aria-label="Información sobre el índice de prioridad"
                          />
                          <span className="zr-tooltip" role="tooltip">
                            Puntuación utilizada para ordenar las zonas.
                            La fórmula y su interpretación detallada se
                            documentarán en la información técnica del proyecto.
                          </span>
                        </span>
                      </span>

                      <span className="zr-score-track">
                        <span style={{ width: scoreWidth }} />
                      </span>
                    </span>
                  </span>

                  <span className="zr-score-value">
                    {formatValue(score)}
                    <small>índice</small>
                  </span>

                  <span className="zr-card-chevron">
                    <ChevronRight size={19} />
                  </span>
                </button>
              );
            })}
          </div>

          <footer className="zone-ranking-pagination zr-pagination">
            <span>
              Mostrando{" "}
              <strong>
                {(safePage - 1) * pageSize + 1}–
                {Math.min(safePage * pageSize, filteredFeatures.length)}
              </strong>{" "}
              de {filteredFeatures.length} zonas
            </span>

            <div className="zone-ranking-pagination-controls">
              <button
                type="button"
                onClick={() =>
                  setPage((current) => Math.max(1, current - 1))
                }
                disabled={safePage <= 1}
                aria-label="Página anterior"
              >
                <ChevronLeft size={17} />
                Anterior
              </button>

              <span>
                Página {safePage} de {totalPages}
              </span>

              <button
                type="button"
                onClick={() =>
                  setPage((current) => Math.min(totalPages, current + 1))
                }
                disabled={safePage >= totalPages}
                aria-label="Página siguiente"
              >
                Siguiente
                <ChevronRight size={17} />
              </button>
            </div>
          </footer>
        </>
      )}
    </section>
  );
}
