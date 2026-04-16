from datetime import datetime
from typing import List, Dict

from pydantic import BaseModel

class PositionDetail(BaseModel):
    ticker: str
    shares: int
    price: float
    value: float

class PortfolioStateDTO(BaseModel):
    user_id: int
    date: str
    cash: float
    portfolio_value: float
    positions: List[PositionDetail]

class PortfolioSummaryDTO(BaseModel):
    date: str
    portfolio_value: float

class PortfolioValuation(BaseModel):
    date: datetime
    cash: float
    portfolio_value: float
    positions: List[PositionDetail]


class PortfolioPerformanceBaseDTO(BaseModel):
    # Dane identyfikacyjne
    id: int
    name: str
    archetype_key: str

    # Konfiguracja (metryki)
    short_term_weight: float
    medium_term_weight: float
    long_term_weight: float
    risk_tolerance: float
    rebalance_threshold: float
    min_score_threshold: float
    softmax_temp: float
    metric_weights: Dict[str, float]

    model_config = {"from_attributes": True}


class PortfolioPerformanceSummaryDTO(PortfolioPerformanceBaseDTO):
    # rozszerzenie o wynik
    change_ratio: float