import {
  RotateCcw,
  SlidersHorizontal,
} from "lucide-react";


export default function FilterPanel({
  options,
  filters,
  onChange,
  onClear,
  loading = false,
}) {

  const hasFilters =
    Object.values(filters).some(
      (value) =>
        value !== null &&
        value !== undefined &&
        value !== ""
    );


  function handleChange(event) {

    const {
      name,
      value,
    } = event.target;


    onChange({
      ...filters,
      [name]: value || null,
    });

  }


  return (

    <section className="filter-panel">

      <div className="filter-panel-header">

        <div className="filter-title-wrapper">

          <div className="filter-icon">

            <SlidersHorizontal
              size={17}
            />

          </div>


          <div>

            <p className="section-label">
              FILTROS
            </p>

            <h3>
              Criterios de intervención
            </h3>

          </div>

        </div>


        <button
          type="button"
          className="clear-filters-button"
          onClick={onClear}
          disabled={
            !hasFilters || loading
          }
        >

          <RotateCcw
            size={14}
          />

          Limpiar

        </button>

      </div>


      <div className="filter-grid">


        {/* =================================================
            NIVEL DE INTERVENCIÓN
        ================================================== */}

        <div className="filter-field">

          <label htmlFor="intervention_level">
            Nivel de intervención
          </label>


          <select
            id="intervention_level"
            name="intervention_level"
            value={
              filters.intervention_level || ""
            }
            onChange={handleChange}
            disabled={loading}
          >

            <option value="">
              Todos los niveles
            </option>


            {(
              options?.intervention_levels || []
            ).map((option) => (

              <option
                key={option}
                value={option}
              >
                {option}
              </option>

            ))}

          </select>

        </div>


        {/* =================================================
            TIPO DE INTERVENCIÓN
        ================================================== */}

        <div className="filter-field">

          <label htmlFor="intervention_type">
            Tipo de intervención
          </label>


          <select
            id="intervention_type"
            name="intervention_type"
            value={
              filters.intervention_type || ""
            }
            onChange={handleChange}
            disabled={loading}
          >

            <option value="">
              Todos los tipos
            </option>


            {(
              options?.intervention_types || []
            ).map((option) => (

              <option
                key={option}
                value={option}
              >
                {option}
              </option>

            ))}

          </select>

        </div>


        {/* =================================================
            CONDICIÓN DOMINANTE
        ================================================== */}

        <div className="filter-field">

          <label htmlFor="dominant_condition">
            Condición dominante
          </label>


          <select
            id="dominant_condition"
            name="dominant_condition"
            value={
              filters.dominant_condition || ""
            }
            onChange={handleChange}
            disabled={loading}
          >

            <option value="">
              Todas las condiciones
            </option>


            {(
              options?.dominant_conditions || []
            ).map((option) => (

              <option
                key={option}
                value={option}
              >
                {option}
              </option>

            ))}

          </select>

        </div>


        {/* =================================================
            PLAZO DE INTERVENCIÓN
        ================================================== */}

        <div className="filter-field">

          <label htmlFor="priority_timeframe">
            Plazo de intervención
          </label>


          <select
            id="priority_timeframe"
            name="priority_timeframe"
            value={
              filters.priority_timeframe || ""
            }
            onChange={handleChange}
            disabled={loading}
          >

            <option value="">
              Todos los plazos
            </option>


            {(
              options?.priority_timeframes || []
            ).map((option) => (

              <option
                key={option}
                value={option}
              >
                {option}
              </option>

            ))}

          </select>

        </div>

      </div>


      {loading && (

        <div className="filter-loading">
          Actualizando análisis...
        </div>

      )}

    </section>

  );

}