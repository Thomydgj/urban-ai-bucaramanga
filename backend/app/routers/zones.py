from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..data import load_master_layer
from ..services.zone_service import (
    get_filtered_zones,
    zone_to_dict,
)


router = APIRouter(
    prefix="/api",
    tags=["Zones"],
)


# =========================================================
# ALL ZONES
# =========================================================

@router.get("/zones")
def get_zones(
    intervention_level: Optional[str] = Query(
        default=None,
        description="ALTA, CRITICA o MEDIA",
    ),
    intervention_type: Optional[str] = Query(
        default=None,
        description="Tipo de intervención",
    ),
    dominant_condition: Optional[str] = Query(
        default=None,
        description="Condición dominante",
    ),
    priority_timeframe: Optional[str] = Query(
        default=None,
        description="INMEDIATO, CORTO_PLAZO o MEDIANO_PLAZO",
    ),
    limit: int = Query(
        default=224,
        ge=1,
        le=224,
        description="Número máximo de zonas",
    ),
):

    try:

        filtered = get_filtered_zones(
            intervention_level=intervention_level,
            intervention_type=intervention_type,
            dominant_condition=dominant_condition,
            priority_timeframe=priority_timeframe,
        )

        total_matching = len(filtered)

        filtered = filtered.sort_values(
            "operational_rank"
        ).head(limit)

        zones = [
            zone_to_dict(row)
            for _, row in filtered.iterrows()
        ]

        return {
            "count": len(zones),
            "total_matching": total_matching,
            "zones": zones,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =========================================================
# ZONE BY ID
# =========================================================

@router.get("/zones/{zone_id}")
def get_zone(zone_id: str):

    gdf = load_master_layer()

    matches = gdf[
        gdf["zone_id"].astype(str).str.upper()
        == zone_id.upper()
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail=f"No existe la zona {zone_id}",
        )

    return zone_to_dict(
        matches.iloc[0]
    )


# =========================================================
# MAP
# =========================================================

@router.get("/map")
def get_map(
    intervention_level: Optional[str] = None,
    intervention_type: Optional[str] = None,
    dominant_condition: Optional[str] = None,
    priority_timeframe: Optional[str] = None,
):

    try:

        filtered = get_filtered_zones(
            intervention_level=intervention_level,
            intervention_type=intervention_type,
            dominant_condition=dominant_condition,
            priority_timeframe=priority_timeframe,
        )

        filtered = filtered.sort_values(
            "operational_rank"
        )

        if filtered.crs is None:
            raise ValueError(
                "La capa no tiene CRS definido."
            )

        filtered = filtered.to_crs("EPSG:4326")

        return {
            "count": len(filtered),
            "geojson": filtered.to_json(),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =========================================================
# FILTER OPTIONS
# =========================================================

@router.get("/filters")
def get_filters():

    try:

        gdf = load_master_layer()

        return {
            "intervention_levels": sorted(
                gdf["intervention_level"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            "intervention_types": sorted(
                gdf["intervention_type"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            "dominant_conditions": sorted(
                gdf["dominant_condition"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            "priority_timeframes": sorted(
                gdf["priority_timeframe"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )