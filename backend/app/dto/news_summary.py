from pydantic import BaseModel
from typing import List
from datetime import date

class NewsSummaryDTO(BaseModel):
    summary: str
    importance: float
    date: date

class MarketNewsContextDTO(BaseModel):
    short_term_14d: List[NewsSummaryDTO]
    medium_term_50d: List[NewsSummaryDTO]
    long_term_200d: List[NewsSummaryDTO]