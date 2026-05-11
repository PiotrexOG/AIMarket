from datetime import datetime
from typing import List, Dict

from pydantic import BaseModel

class PositionDetail(BaseModel):
    ticker: str
    shares: float
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


class PortfolioArchetypeDTO(BaseModel):
    date: str
    portfolio_value: float


class PortfolioPerformanceBaseDTO(BaseModel):
    # Dane identyfikacyjne
    id: int
    name: str
    archetype_key: str

    # Konfiguracja (metryki)
    short_term_weight: float| str
    medium_term_weight: float| str
    long_term_weight: float| str
    risk_tolerance: float| str
    rebalance_threshold: float| str
    min_score_threshold: float| str
    softmax_temp: float | str
    metric_weights: Dict[str, float] | Dict[str, str]

    model_config = {"from_attributes": True}


class PortfolioPerformanceSummaryDTO(PortfolioPerformanceBaseDTO):
    # rozszerzenie o wynik
    change_ratio: float