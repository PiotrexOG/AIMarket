from datetime import datetime
from pydantic import BaseModel


class CompanyNewsCreate(BaseModel):
    ticker: str
    as_of_date: datetime

    headline: str | None = None
    summary: str | None = None


class CompanyNewsDTO(BaseModel):
    id: int
    ticker: str
    as_of_date: datetime

    headline: str | None = None
    summary: str | None = None

    class Config:
        from_attributes = True  # SQLAlchemy → Pydantic
