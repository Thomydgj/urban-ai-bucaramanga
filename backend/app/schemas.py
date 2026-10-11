from typing import Optional

from pydantic import BaseModel, ConfigDict


class Zone(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_id: str
    operational_rank: int
    hotspot_rank: int

    observations: int
    observation_percentage: float

    area_ha: float
    area_percentage: float

    mean_probability: float
    max_probability: float

    hotspot_score: float
    operational_score: float

    priority_density: float

    mean_ndvi: float
    mean_ndbi: float
    mean_lst: float

    dominant_condition: str
    density_level: str

    intervention_level: str
    priority_class: str
    intervention_type: str

    zone_description: Optional[str] = None

    centroid_x: float
    centroid_y: float

    geometry: Optional[dict] = None