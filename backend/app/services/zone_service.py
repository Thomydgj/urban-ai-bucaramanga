from typing import Optional

import geopandas as gpd

from ..data import load_master_layer


def apply_zone_filters(
    gdf: gpd.GeoDataFrame,
    intervention_level: Optional[str] = None,
    intervention_type: Optional[str] = None,
    dominant_condition: Optional[str] = None,
    priority_timeframe: Optional[str] = None,
) -> gpd.GeoDataFrame:

    filtered = gdf

    if intervention_level:
        filtered = filtered[
            filtered["intervention_level"].astype(str).str.upper()
            == intervention_level.upper()
        ]

    if intervention_type:
        filtered = filtered[
            filtered["intervention_type"].astype(str).str.upper()
            == intervention_type.upper()
        ]

    if dominant_condition:
        filtered = filtered[
            filtered["dominant_condition"].astype(str).str.upper()
            == dominant_condition.upper()
        ]

    if priority_timeframe:
        filtered = filtered[
            filtered["priority_timeframe"].astype(str).str.upper()
            == priority_timeframe.upper()
        ]

    return filtered


def get_filtered_zones(
    intervention_level: Optional[str] = None,
    intervention_type: Optional[str] = None,
    dominant_condition: Optional[str] = None,
    priority_timeframe: Optional[str] = None,
) -> gpd.GeoDataFrame:

    gdf = load_master_layer()

    return apply_zone_filters(
        gdf,
        intervention_level=intervention_level,
        intervention_type=intervention_type,
        dominant_condition=dominant_condition,
        priority_timeframe=priority_timeframe,
    )


def clean_value(value):

    if hasattr(value, "item"):
        return value.item()

    return value


def zone_to_dict(row):

    result = {}

    for column in row.index:

        if column == "geometry":
            continue

        result[column] = clean_value(row[column])

    return result