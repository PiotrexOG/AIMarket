from datetime import date
from pydantic import BaseModel


class CompanyDailySummaryCreate(BaseModel):
    ticker: str
    date: date
    summary: str | None = None
    importance: float = 0.0

class CompanyDailySummaryDTO(BaseModel):
    id: int
    ticker: str
    date: date
    summary: str | None = None
    importance: float

    class Config:
        from_attributes = True