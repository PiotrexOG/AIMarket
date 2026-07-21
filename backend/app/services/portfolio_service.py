from datetime import datetime
import math
from typing import List, Optional
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.dto.portfolio_dto import PortfolioStateDTO, PortfolioSummaryDTO, PositionDetail, \
    PortfolioPerformanceSummaryDTO, PortfolioPerformanceBaseDTO
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.portfolio_valuation_service import PortfolioValuationService
from app.db.schemas.portfolio import (
    PortfolioCreate,
    PortfolioCycleEventCreate,
    TickerScoreSnapshotCreate,
)
from app.db.models.portfolio import PortfolioCycleEvent, PortfolioHistory
from app.shared.types import ValuationInterval, INTERVAL_MAP


# ---- Funkcje pomocnicze poza klasą ----
def _create_valuation_dto(valuation, user_id: int = None, detailed: bool = False):
    """Tworzy DTO na podstawie wyceny i flagi detailed."""
    if detailed:
        return PortfolioStateDTO(
            user_id=user_id,
            date=valuation.date.isoformat(),
            cash=valuation.cash,
            portfolio_value=valuation.portfolio_value,
            positions=[
                PositionDetail(
                    ticker=p.ticker,
                    shares=p.shares,
                    price=p.price,
                    value=p.value,
                    value_of_portfolio=p.value/valuation.portfolio_value,
                ) for p in valuation.positions
            ],
        )
    else:
        return PortfolioSummaryDTO(
            date=valuation.date.isoformat(),
            portfolio_value=valuation.portfolio_value,
        )


def _build_portfolio_base(
        portfolio,
) -> Optional[PortfolioPerformanceBaseDTO]:

    return PortfolioPerformanceBaseDTO(
        id=portfolio.id,
        name=portfolio.name,
        archetype_key=portfolio.archetype_key,
        top_m_share=getattr(portfolio, "top_m_share", 1.0),
        investment_time_days=getattr(portfolio, "investment_time_days", 300),
        rebalance_time_share=getattr(portfolio, "rebalance_time_share", 0.2),
    )


class PortfolioService:
    def __init__(self, db: Session, portfolio_valuation_service: PortfolioValuationService):
        self.repo = PortfolioRepository(db)
        self.portfolio_valuation_service = portfolio_valuation_service

    # ---- Podstawowe operacje ----
    def create_portfolio(self, data: PortfolioCreate):
        return self.repo.create(data)

    def get_by_user_id(self, user_id: int):
        return self.repo.get_by_user(user_id)

    def get_latest_history(self, portfolio_id: int) -> Optional[PortfolioHistory]:
        return self.repo.get_latest_history(portfolio_id)

    def evaluate(self, portfolio_id: int, history_data):
        return self.repo.add_history(portfolio_id, history_data)

    def record_score_snapshots(
            self,
            date_time: datetime,
            raw_scores: dict[str, float],
            score_percentiles: dict[str, float],
            timeframe: str = "long_term_200d",
    ) -> None:
        snapshots = [
            TickerScoreSnapshotCreate(
                datetime=date_time,
                ticker=ticker,
                timeframe=timeframe,
                score=float(score),
                score_percentile=float(score_percentiles[ticker]),
            )
            for ticker, score in sorted(raw_scores.items())
            if ticker in score_percentiles
        ]
        self.repo.upsert_score_snapshots(snapshots)

    def record_cycle_event(
            self,
            portfolio,
            event_type: str,
            date_time: datetime,
            *,
            selected_tickers: list[str] | None = None,
            sold_tickers: list[str] | None = None,
            replacement_tickers: list[str] | None = None,
    ) -> Optional[PortfolioCycleEvent]:
        if not portfolio.has_active_cycle():
            return None

        event_data = PortfolioCycleEventCreate(
            datetime=date_time,
            event_type=event_type,
            investment_start_date=portfolio.investment_start_date,
            next_rebalance_date=portfolio.next_rebalance_date(),
            next_cycle_date=portfolio.next_cycle_date(),
            investment_time_days=portfolio.investment_time_days(),
            rebalance_time_share=portfolio.rebalance_time_share(),
            selected_tickers=list(selected_tickers or portfolio.entry_score_percentiles.keys()),
            sold_tickers=list(sold_tickers or []),
            replacement_tickers=list(replacement_tickers or []),
            entry_score_percentiles={
                ticker: float(percentile)
                for ticker, percentile in portfolio.entry_score_percentiles.items()
            },
        )
        return self.repo.add_cycle_event(portfolio.portfolio_id, event_data)

    def hydrate_runtime_portfolio_cycle(
            self,
            portfolio,
            as_of_datetime: datetime,
            timeframe: str = "long_term_200d",
    ) -> bool:
        latest_event = self.repo.get_latest_cycle_event(
            portfolio.portfolio_id,
            as_of_datetime,
        )
        if not latest_event:
            return False

        score_snapshots = self.repo.get_score_snapshots(
            latest_event.investment_start_date,
            as_of_datetime,
            timeframe=timeframe,
        )
        percentile_history: dict[str, list[tuple[datetime, float]]] = {}
        for snapshot in score_snapshots:
            percentile_history.setdefault(snapshot.ticker, []).append(
                (snapshot.datetime, snapshot.score_percentile)
            )

        rebalanced_in_cycle = latest_event.event_type == "REBALANCE"
        rebalance_date = (
            latest_event.datetime
            if rebalanced_in_cycle
            else latest_event.next_rebalance_date
        )
        portfolio.restore_cycle_state(
            investment_start_date=latest_event.investment_start_date,
            rebalance_date=rebalance_date,
            rebalanced_in_cycle=rebalanced_in_cycle,
            entry_score_percentiles=latest_event.entry_score_percentiles,
            entry_score_percentile_history=percentile_history,
        )
        return True

    def calculate_time_weighted_score_percentiles(
            self,
            start: datetime,
            end: datetime,
            timeframe: str = "long_term_200d",
    ) -> dict[str, float]:
        score_snapshots = self.repo.get_score_snapshots(start, end, timeframe=timeframe)
        snapshots_by_ticker: dict[str, list] = {}
        for snapshot in score_snapshots:
            snapshots_by_ticker.setdefault(snapshot.ticker, []).append(snapshot)

        means = {}
        for ticker, snapshots in snapshots_by_ticker.items():
            weighted_sum = 0.0
            weights = []
            values = []
            for index, snapshot in enumerate(snapshots):
                next_datetime = (
                    snapshots[index + 1].datetime
                    if index + 1 < len(snapshots)
                    else end
                )
                segment_days = (
                    min(next_datetime, end) - snapshot.datetime
                ).total_seconds() / 86400.0
                if segment_days <= 0:
                    continue
                values.append(float(snapshot.score_percentile))
                weights.append(segment_days)

            total_weight = math.fsum(weights)
            if total_weight <= 0:
                continue

            weighted_sum = math.fsum(
                value * weight
                for value, weight in zip(values, weights)
            )
            means[ticker] = weighted_sum / total_weight

        return means

    def get_latest_cycle_event(
            self,
            portfolio_id: int,
            date_time: datetime | None = None,
    ) -> Optional[PortfolioCycleEvent]:
        return self.repo.get_latest_cycle_event(portfolio_id, date_time)

    def _create_dto_from_history_entry(self, history_entry, date: datetime, detailed: bool = True):
        """Tworzy DTO na podstawie pojedynczego wpisu historii portfela."""
        shares_dict = {
            share.ticker: share.amount
            for share in history_entry.shares
            if share.amount != 0.0
        }

        valuation = self.portfolio_valuation_service.calculate_portfolio_details(
            cash=history_entry.cash,
            shares=shares_dict,
            date_time=date,
        )
        return _create_valuation_dto(
            valuation=valuation,
            user_id=history_entry.portfolio.user_id,
            detailed=detailed
        )

    def get_portfolio_history(self, portfolio_id: int, detailed: bool = True):
        """Zwraca historię portfela zapisaną w bazie (PortfolioHistory)."""
        history = self.repo.get_history(portfolio_id)
        if not history:
            return []

        return [
            self._create_dto_from_history_entry(h, h.datetime, detailed)
            for h in history
        ]

    def compute_portfolio_state_at_date(
            self,
            portfolio_id: int,
            date: datetime,
            detailed: bool
    ):
        """Pobiera stan portfela z repo i wylicza jego bieżącą wartość rynkową."""
        state = self.repo.get_state_at_date(portfolio_id, date)
        if not state:
            return None

        return self._create_dto_from_history_entry(state, date, detailed)

    # ---- Wycena (valuation) w przedziale czasu ----
    def get_portfolio_valuation_in_range(
            self,
            portfolio_id: int,
            start: datetime,
            end: datetime,
            interval: ValuationInterval,
            detailed: bool = False,
    ) -> dict:
        """Zwraca wycenę portfela w zadanym zakresie, z aktualnym stanem dla każdej chwili."""
        step = INTERVAL_MAP.get(interval)
        if not step:
            raise ValueError(f"Unsupported interval: {interval}")

        valuations = []

        # Zawsze dodaj start
        dates_to_calculate = [start]

        # Dodaj punkty pośrednie
        current = start + step
        while current < end:  # '<' zamiast '<=', żeby uniknąć duplikatu z końcem
            dates_to_calculate.append(current)
            current += step

        # Zawsze dodaj end (chyba że jest taki sam jak start)
        if end != start:
            dates_to_calculate.append(end)

        # Oblicz wartości dla wszystkich dat
        for date in dates_to_calculate:
            dto = self.compute_portfolio_state_at_date(
                portfolio_id=portfolio_id,
                date=date,
                detailed=detailed
            )
            if dto:
                valuations.append(dto)

        if not valuations:
            raise HTTPException(status_code=404, detail="No valuation data in range")

        # Oblicz zmiany procentowe
        start_value = valuations[0].portfolio_value if hasattr(valuations[0], 'portfolio_value') else valuations[0][
            'portfolio_value']
        end_value = valuations[-1].portfolio_value if hasattr(valuations[-1], 'portfolio_value') else valuations[-1][
            'portfolio_value']
        absolute_change = end_value - start_value
        percent_change = (absolute_change / start_value * 100) if start_value != 0 else 0.0

        return {
            "percent_change": round(percent_change, 2),
            "history": valuations
        }

    def _zero_to_NaN(self, value: float):
        """Jeśli wartość = 0 → zwróć pusty dict"""
        return "NaN" if value == 0 else value

    def _build_portfolio_summary(
        self,
        portfolio,
        start: datetime,
        end: datetime
    ) -> Optional[PortfolioPerformanceSummaryDTO]:

        start_state = self.compute_portfolio_state_at_date(portfolio.id, start, detailed=False)
        end_state = self.compute_portfolio_state_at_date(portfolio.id, end, detailed=False)

        if not start_state or not end_state:
            return None

        start_val = start_state.portfolio_value
        end_val = end_state.portfolio_value

        change_ratio = ((end_val - start_val) / start_val) if start_val != 0 else 0.0

        return PortfolioPerformanceSummaryDTO(
            id=portfolio.id,
            name=portfolio.name,
            archetype_key=portfolio.archetype_key,
            top_m_share=getattr(portfolio, "top_m_share", 1.0),
            investment_time_days=getattr(portfolio, "investment_time_days", 300),
            rebalance_time_share=getattr(portfolio, "rebalance_time_share", 0.2),
            change_ratio=round(change_ratio, 4)
        )

    def get_portfolio_performance_summary(
            self,
            portfolio_id: int,
            start: datetime,
            end: datetime
    ) -> PortfolioPerformanceSummaryDTO:

        portfolio = self.repo.get_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        summary = self._build_portfolio_summary(portfolio, start, end)

        if not summary:
            raise HTTPException(status_code=404, detail="Incomplete history for the selected range")

        return summary

    def get_all_portfolios_performance_summary(
            self,
            start: datetime,
            end: datetime
    ) -> List[PortfolioPerformanceSummaryDTO]:

        all_portfolios = self.repo.get_all()

        summaries = [
            summary
            for portfolio in all_portfolios
            if (summary := self._build_portfolio_summary(portfolio, start, end)) is not None
        ]

        return sorted(summaries, key=lambda x: x.change_ratio, reverse=True)


