from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.db.models.portfolio import (
    Portfolio,
    PortfolioCycleEvent,
    PortfolioHistory,
    PortfolioShare,
    TickerScoreSnapshot,
)
from app.db.schemas.portfolio import (
    PortfolioCreate,
    PortfolioCycleEventCreate,
    PortfolioHistoryCreate,
    TickerScoreSnapshotCreate,
)


def _model_dump(model) -> dict:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PortfolioCreate) -> Portfolio:
        db_portfolio = Portfolio(**_model_dump(data))
        self.db.add(db_portfolio)
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio

    def get_by_id(self, portfolio_id: int) -> Portfolio:
        return self.db.query(Portfolio).get(portfolio_id)

    def get_all(self) -> List[Portfolio]:
        return self.db.query(Portfolio).all()

    def get_latest_history(self, portfolio_id: int) -> Optional[PortfolioHistory]:
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(PortfolioHistory.portfolio_id == portfolio_id)
            .order_by(PortfolioHistory.datetime.desc(), PortfolioHistory.id.desc())
            .first()
        )

    def get_by_user(self, user_id: int) -> Portfolio:
        return (
            self.db.query(Portfolio)
            .filter(Portfolio.user_id == user_id)
            .first()
        )

    def get_history(self, portfolio_id: int) -> List[PortfolioHistory]:
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(PortfolioHistory.portfolio_id == portfolio_id)
            .order_by(PortfolioHistory.datetime.asc())
            .all()
        )

    def get_state_at_date(
        self, portfolio_id: int, date_time: datetime
    ) -> Optional[PortfolioHistory]:
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(
                PortfolioHistory.portfolio_id == portfolio_id,
                PortfolioHistory.datetime <= date_time,
            )
            .order_by(PortfolioHistory.datetime.desc(), PortfolioHistory.id.desc())
            .first()
        )

    def add_history(
        self, portfolio_id: int, history_data: PortfolioHistoryCreate
    ) -> PortfolioHistory:
        history_obj = PortfolioHistory(
            portfolio_id=portfolio_id,
            datetime=history_data.datetime,
            cash=round(history_data.cash, 2),
        )
        self.db.add(history_obj)
        self.db.flush()

        for share in history_data.shares:
            share_obj = PortfolioShare(
                portfolio_history_id=history_obj.id,
                ticker=share.ticker,
                amount=share.amount,
            )
            self.db.add(share_obj)

        self.db.commit()
        self.db.refresh(history_obj)
        return history_obj

    def upsert_score_snapshots(
        self,
        snapshots: list[TickerScoreSnapshotCreate],
    ) -> None:
        if not snapshots:
            return

        datetimes = list({snapshot.datetime for snapshot in snapshots})
        tickers = list({snapshot.ticker for snapshot in snapshots})
        timeframes = list({snapshot.timeframe for snapshot in snapshots})
        existing_snapshots = (
            self.db.query(TickerScoreSnapshot)
            .filter(
                TickerScoreSnapshot.datetime.in_(datetimes),
                TickerScoreSnapshot.ticker.in_(tickers),
                TickerScoreSnapshot.timeframe.in_(timeframes),
            )
            .all()
        )
        existing_by_key = {
            (snapshot.datetime, snapshot.ticker, snapshot.timeframe): snapshot
            for snapshot in existing_snapshots
        }

        for snapshot in snapshots:
            key = (snapshot.datetime, snapshot.ticker, snapshot.timeframe)
            existing = existing_by_key.get(key)
            if existing:
                existing.score = snapshot.score
                existing.score_percentile = snapshot.score_percentile
                continue

            self.db.add(TickerScoreSnapshot(**_model_dump(snapshot)))

        self.db.commit()

    def get_score_snapshots(
        self,
        start: datetime,
        end: datetime,
        timeframe: str = "long_term_200d",
    ) -> list[TickerScoreSnapshot]:
        return (
            self.db.query(TickerScoreSnapshot)
            .filter(
                TickerScoreSnapshot.datetime >= start,
                TickerScoreSnapshot.datetime <= end,
                TickerScoreSnapshot.timeframe == timeframe,
            )
            .order_by(TickerScoreSnapshot.datetime.asc(), TickerScoreSnapshot.ticker.asc())
            .all()
        )

    def add_cycle_event(
        self,
        portfolio_id: int,
        event_data: PortfolioCycleEventCreate,
    ) -> PortfolioCycleEvent:
        event = PortfolioCycleEvent(
            portfolio_id=portfolio_id,
            **_model_dump(event_data),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_latest_cycle_event(
        self,
        portfolio_id: int,
        date_time: datetime | None = None,
    ) -> Optional[PortfolioCycleEvent]:
        query = self.db.query(PortfolioCycleEvent).filter(
            PortfolioCycleEvent.portfolio_id == portfolio_id,
        )
        if date_time is not None:
            query = query.filter(PortfolioCycleEvent.datetime <= date_time)

        return (
            query
            .order_by(PortfolioCycleEvent.datetime.desc(), PortfolioCycleEvent.id.desc())
            .first()
        )
