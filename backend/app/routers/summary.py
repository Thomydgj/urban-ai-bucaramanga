from typing import Optional

import geopandas as gpd
from fastapi import APIRouter, HTTPException, Query

from ..config import MASTER_GPKG, MASTER_LAYER


router = APIRouter(
    prefix="/api",
    tags=["summary"],
)


def load_master_layer() -> gpd.GeoDataFrame:
    """
    Carga la capa maestra validada del GeoPackage.
    """

    try:
        master = gpd.read_file(
            MASTER_GPKG,
            layer=MASTER_LAYER,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible cargar la capa "
                f"'{MASTER_LAYER}': {exc}"
            ),
        )

    if master.empty:
        raise HTTPException(
            status_code=500,
            detail="La capa maestra está vacía.",
        )

    return master


def apply_filters(
    master: gpd.GeoDataFrame,
    intervention_level: Optional[str] = None,
    intervention_type: Optional[str] = None,
    dominant_condition: Optional[str] = None,
    priority_timeframe: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """
    Aplica los filtros disponibles en el backend.
    """

    filtered = master.copy()

    if intervention_level:
        filtered = filtered[
            filtered["intervention_level"]
            .astype(str)
            .str.upper()
            == intervention_level.upper()
        ]

    if intervention_type:
        filtered = filtered[
            filtered["intervention_type"]
            .astype(str)
            .str.upper()
            == intervention_type.upper()
        ]

    if dominant_condition:
        filtered = filtered[
            filtered["dominant_condition"]
            .astype(str)
            .str.upper()
            == dominant_condition.upper()
        ]

    if priority_timeframe:
        filtered = filtered[
            filtered["priority_timeframe"]
            .astype(str)
            .str.upper()
            == priority_timeframe.upper()
        ]

    return filtered


def safe_weighted_mean(
    values,
    weights,
) -> float:
    """
    Calcula una media ponderada de forma segura.
    """

    if len(values) == 0:
        return 0.0

    total_weight = float(weights.sum())

    if total_weight <= 0:
        return float(values.mean())

    return float(
        (values * weights).sum()
        / total_weight
    )


@router.get("/summary")
def get_summary(
    intervention_level: Optional[str] = Query(
        default=None,
        description="Nivel de intervención.",
    ),
    intervention_type: Optional[str] = Query(
        default=None,
        description="Tipo de intervención.",
    ),
    dominant_condition: Optional[str] = Query(
        default=None,
        description="Condición dominante.",
    ),
    priority_timeframe: Optional[str] = Query(
        default=None,
        description="Plazo de intervención.",
    ),
):
    """
    Devuelve el resumen de la capa maestra.

    Si se proporcionan filtros, los indicadores se
    recalculan únicamente sobre las zonas filtradas.
    """

    master = load_master_layer()

    filtered = apply_filters(
        master=master,
        intervention_level=intervention_level,
        intervention_type=intervention_type,
        dominant_condition=dominant_condition,
        priority_timeframe=priority_timeframe,
    )

    # ---------------------------------------------------------
    # Sin resultados
    # ---------------------------------------------------------

    if filtered.empty:

        return {
            "zones": 0,
            "observations": 0,
            "area_ha": 0.0,
            "mean_probability": 0.0,
            "mean_hotspot_score": 0.0,
            "mean_operational_score": 0.0,
            "filters_applied": {
                "intervention_level": intervention_level,
                "intervention_type": intervention_type,
                "dominant_condition": dominant_condition,
                "priority_timeframe": priority_timeframe,
            },
        }

    # ---------------------------------------------------------
    # Zonas
    # ---------------------------------------------------------

    zones = len(filtered)

    # ---------------------------------------------------------
    # Observaciones
    # ---------------------------------------------------------

    if "observation_count" in filtered.columns:

        observations = int(
            filtered["observation_count"]
            .fillna(0)
            .sum()
        )

    elif "observations" in filtered.columns:

        observations = int(
            filtered["observations"]
            .fillna(0)
            .sum()
        )

    else:

        observations = 0

    # ---------------------------------------------------------
    # Área
    # ---------------------------------------------------------

    if "area_ha" in filtered.columns:

        area_ha = float(
            filtered["area_ha"]
            .fillna(0)
            .sum()
        )

    else:

        area_ha = 0.0

    # ---------------------------------------------------------
    # Pesos
    # ---------------------------------------------------------

    if "area_ha" in filtered.columns:

        weights = (
            filtered["area_ha"]
            .fillna(0)
            .astype(float)
        )

    else:

        weights = (
            filtered
            .assign(_weight=1.0)
            ["_weight"]
        )

    # ---------------------------------------------------------
    # Probability
    # ---------------------------------------------------------

    if "mean_probability" in filtered.columns:

        probability_values = (
            filtered["mean_probability"]
            .fillna(0)
            .astype(float)
        )

        mean_probability = safe_weighted_mean(
            probability_values,
            weights,
        )

    else:

        mean_probability = 0.0

    # ---------------------------------------------------------
    # Hotspot
    # ---------------------------------------------------------

    if "hotspot_score" in filtered.columns:

        hotspot_values = (
            filtered["hotspot_score"]
            .fillna(0)
            .astype(float)
        )

        mean_hotspot_score = safe_weighted_mean(
            hotspot_values,
            weights,
        )

    else:

        mean_hotspot_score = 0.0

    # ---------------------------------------------------------
    # Operational
    # ---------------------------------------------------------

    if "operational_score" in filtered.columns:

        operational_values = (
            filtered["operational_score"]
            .fillna(0)
            .astype(float)
        )

        mean_operational_score = safe_weighted_mean(
            operational_values,
            weights,
        )

    else:

        mean_operational_score = 0.0

    # ---------------------------------------------------------
    # Respuesta
    # ---------------------------------------------------------

    return {
        "zones": zones,

        "observations": observations,

        "area_ha": round(
            area_ha,
            2,
        ),

        "mean_probability": round(
            mean_probability,
            6,
        ),

        "mean_hotspot_score": round(
            mean_hotspot_score,
            6,
        ),

        "mean_operational_score": round(
            mean_operational_score,
            6,
        ),

        "filters_applied": {
            "intervention_level": intervention_level,
            "intervention_type": intervention_type,
            "dominant_condition": dominant_condition,
            "priority_timeframe": priority_timeframe,
        },
    }