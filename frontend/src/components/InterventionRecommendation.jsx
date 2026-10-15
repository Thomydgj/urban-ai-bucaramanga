
import {
  AlertTriangle,
  Leaf,
  Target,
  Info,
  Trees,
  Sun,
  Layers,
  Droplets,
  Thermometer,
  Network,
  ArrowDownRight,
  Sparkles,
} from "lucide-react";

function formatLabel(value) {
  if (value === null || value === undefined || value === "") {
    return "No disponible";
  }

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (c) => c.toUpperCase());
}

function getLevelClass(level) {
  const normalized = String(level ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase();

  if (normalized.includes("CRIT")) return "critical";
  if (normalized.includes("ALT")) return "high";
  if (normalized.includes("MED")) return "medium";
  return "default";
}

function getActionVisual(action) {
  const text = action.toLowerCase();

  if (text.includes("arbor") || text.includes("veget")) {
    return { Icon: Trees, color: "green", label: "Vegetación" };
  }

  if (text.includes("sombra")) {
    return { Icon: Sun, color: "amber", label: "Confort térmico" };
  }

  if (text.includes("permeab") || text.includes("agua")) {
    return { Icon: Droplets, color: "blue", label: "Agua y suelo" };
  }

  if (
    text.includes("térmic") ||
    text.includes("termic") ||
    text.includes("absorción")
  ) {
    return {
      Icon: Thermometer,
      color: "orange",
      label: "Mitigación térmica",
    };
  }

  if (text.includes("monitoreo") || text.includes("seguimiento")) {
    return {
      Icon: Layers,
      color: "purple",
      label: "Seguimiento",
    };
  }

  if (text.includes("coordinación") || text.includes("multisectorial")) {
    return {
      Icon: Network,
      color: "teal",
      label: "Gestión urbana",
    };
  }

  return { Icon: Leaf, color: "green", label: "Intervención urbana" };
}

function getReasonTags(reason) {
  if (!reason || reason === "—") return [];

  return String(reason)
    .split(/[;|,]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => item.replace(/^[-•]\s*/, ""));
}

export default function InterventionRecommendation({ zone }) {
  if (!zone) {
    return (
      <section className="intervention-recommendation ir-visual">
        <div className="ir-empty">
          <Target size={28} />
          <div>
            <strong>Selecciona una zona</strong>
            <p>Consulta las acciones recomendadas para esa zona.</p>
          </div>
        </div>
      </section>
    );
  }

  const p = zone.properties || {};
  const zoneId = p.zone_id ?? "Zona seleccionada";
  const level = p.intervention_level ?? "Sin clasificar";
  const condition = p.dominant_condition;
  const recommendation = p.recommendation ?? "";
  const objective = p.intervention_objective ?? "";
  const reason = p.priority_reason ?? "";
  const actionPackage = p.action_package ?? "";


  const actions = String(actionPackage)
    .split(/[|;\n]+/)
    .map((item) => item.trim())
    .filter(Boolean);

  const reasons = getReasonTags(reason);

  // Evita mostrar la segunda oración si solo repite la estrategia.
  const mainRecommendation = String(recommendation)
    .split(/\.\s+(?=[A-ZÁÉÍÓÚ])/)[0]
    .trim()
    .replace(/[.!]+$/, "");

  return (
    <section className="intervention-recommendation ir-visual">
      <header className="ir-header">
        <div>
          <div className="ir-eyebrow">
            <Sparkles size={14} />
            PLAN DE INTERVENCIÓN
          </div>
          <h2>{zoneId}</h2>
        
        </div>

        <div className={`ir-priority ${getLevelClass(level)}`}>
          <AlertTriangle size={16} />
          <span>{formatLabel(level)}</span>
        </div>
      </header>

      <section className="ir-recommendation">
        <div className="ir-recommendation-top">
          <div className="ir-recommendation-icon">
            <Leaf size={29} />
          </div>
          <div>
            <span className="ir-overline">ESTRATEGIA RECOMENDADA</span>
            <h3>{mainRecommendation || "Intervención urbana"}</h3>
          </div>
        </div>

        {condition && (
          <div className="ir-condition">
            <span>Condición detectada</span>
            <strong>{formatLabel(condition)}</strong>
          </div>
        )}
      </section>

      <section className="ir-objective">
        <div className="ir-section-icon objective">
          <Target size={21} />
        </div>
        <div>
          <span className="ir-overline">OBJETIVO</span>
          <p>{objective || "No hay un objetivo disponible para esta zona."}</p>
        </div>
      </section>

      {reasons.length > 0 && (
        <section className="ir-reasons">
          <div className="ir-section-heading">
            <div className="ir-section-icon reason">
              <Info size={20} />
            </div>
            <div>
              <h3>¿Por qué intervenir aquí?</h3>
              <p>Factores identificados en esta zona</p>
            </div>
          </div>

          <div className="ir-reason-tags">
            {reasons.map((item, index) => (
              <span className="ir-reason-tag" key={`${item}-${index}`}>
                <ArrowDownRight size={14} />
                {formatLabel(item)}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className="ir-actions">
        <div className="ir-section-heading">
          <div className="ir-section-icon actions">
            <Layers size={20} />
          </div>
          <div>
            <h3>Acciones propuestas</h3>
            <p>Medidas que pueden formar parte de la intervención</p>
          </div>
          <span className="ir-action-count">{actions.length}</span>
        </div>

        <div className="ir-action-grid">
          {actions.map((action, index) => {
            const visual = getActionVisual(action);
            const Icon = visual.Icon;

            return (
              <article
                className={`ir-action-card ${visual.color}`}
                key={`${action}-${index}`}
              >
                <div className="ir-action-card-top">
                  <div className="ir-action-icon">
                    <Icon size={25} strokeWidth={1.8} />
                  </div>
                  <span className="ir-action-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                </div>

                <span className="ir-action-category">
                  {visual.label}
                </span>
                <h4>{formatLabel(action)}</h4>
              </article>
            );
          })}
        </div>
      </section>

   
    </section>
  );
}
