from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field

# ---- Portfolio Metric Weights (NOWOŚĆ) ----
class PortfolioMetricWeightBase(BaseModel):
    metric_name: str
    weight: float

class PortfolioMetricWeightCreate(PortfolioMetricWeightBase):
    pass

class PortfolioMetricWeightRead(PortfolioMetricWeightBase):
    id: int

    class Config:
        from_attributes = True

# ---- Portfolio Share ----
class PortfolioShareBase(BaseModel):
    ticker: str
    amount: float

class PortfolioShareCreate(PortfolioShareBase):
    pass

class PortfolioShareRead(PortfolioShareBase):
    id: int
    class Config:
        from_attributes = True

# ---- Portfolio History ----
class PortfolioHistoryBase(BaseModel):
    datetime: datetime
    cash: float

class PortfolioHistoryCreate(PortfolioHistoryBase):
    shares: List[PortfolioShareCreate]

class PortfolioHistoryRead(PortfolioHistoryBase):
    id: int
    shares: List[PortfolioShareRead]
    class Config:
        from_attributes = True

# ---- Portfolio ----
class PortfolioBase(BaseModel):
    name: str
    archetype_key: str
    short_term_weight: float
    medium_term_weight: float
    long_term_weight: float
    risk_tolerance: float
    rebalance_threshold: float
    min_score_threshold: float
    softmax_temp: float

class PortfolioCreate(PortfolioBase):
    user_id: int
    # Przy tworzeniu nadal wygodnie jest przyjąć słownik,
    # który serwis rozbije na wiersze w bazie danych
    metric_weights: Dict[str, float] = {}

class PortfolioRead(PortfolioBase):
    id: int
    # Przy odczycie dostajemy listę obiektów z bazy (relacja SQLAlchemy)
    metric_weights: List[PortfolioMetricWeightRead] = []
    history: List[PortfolioHistoryRead] = []

    class Config:
        from_attributes = True

# ---- Pozostałe (bez zmian, ale dla kompletności) ----
class PortfolioTransactionRead(BaseModel):
    datetime: datetime
    decision: str = Field(alias="type")
    ticker: str
    quantity: float
    price: float
    total_value: float

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

class PortfolioTickerTransactionRead(BaseModel):
    datetime: datetime
    quantity: float
    ratio: float
    price: float
    total_value: float

    model_config = {
        "from_attributes": True,
    }