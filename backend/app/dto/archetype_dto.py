from pydantic import BaseModel
from typing import Dict, Tuple, List

class WeightRange(BaseModel):
    min: float
    max: float

class ArchetypeWeightsDTO(BaseModel):
    short: Tuple[float, float]
    medium: Tuple[float, float]
    long: Tuple[float, float]

class ArchetypeMetricWeightsDTO(BaseModel):
    tech: Tuple[float, float]
    fund: Tuple[float, float]
    val: Tuple[float, float]
    risk: Tuple[float, float]
    conv: Tuple[float, float]
    asym: Tuple[float, float]

class ArchetypeRead(BaseModel):
    key: str
    name: str
    summary: str
    time_weights: ArchetypeWeightsDTO
    metric_weights: ArchetypeMetricWeightsDTO
    min_exposure: Tuple[float, float]
    aggression_slope: Tuple[float, float]
    exposure_baseline: Tuple[float, float]
    temp: Tuple[float, float]
    rebalance_range: Tuple[float, float]