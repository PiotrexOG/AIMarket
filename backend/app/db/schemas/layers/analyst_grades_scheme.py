from datetime import datetime
from pydantic import BaseModel


class AnalystGradesCreate(BaseModel):
    ticker: str
    as_of_date: datetime

    analystRatingsStrongBuy: int | None = None
    analystRatingsBuy: int | None = None
    analystRatingsHold: int | None = None
    analystRatingsSell: int | None = None
    analystRatingsStrongSell: int | None = None


class AnalystGradesDTO(BaseModel):
    id: int
    ticker: str
    as_of_date: datetime

    analystRatingsStrongBuy: int | None = None
    analystRatingsBuy: int | None = None
    analystRatingsHold: int | None = None
    analystRatingsSell: int | None = None
    analystRatingsStrongSell: int | None = None

    class Config:
        from_attributes = True  # SQLAlchemy → Pydantic
