from collections import defaultdict
from datetime import timedelta
import math
from typing import Dict, Iterable

from app.dto.portfolio_dto import PortfolioPerformanceBaseDTO
from app.portfolio_generation.top_m import (
    INVESTMENT_TIME_MAX_DAYS,
    REBALANCE_TIME_MIN_SHARE,
)

def to_profile_dict(dto: PortfolioPerformanceBaseDTO) -> dict:
    return {
        "id": dto.id,
        "name": dto.name,
        "archetype_key": dto.archetype_key,

        "top_m_share": dto.top_m_share,
        "investment_time_days": dto.investment_time_days,
        "rebalance_time_share": dto.rebalance_time_share,
    }


class Portfolio:
    def __init__(self, portfolio_id: int, starting_cash: float, user_profile: PortfolioPerformanceBaseDTO, shares: Dict[str, float] = None):
        self.portfolio_id = portfolio_id
        self.cash = starting_cash
        self.shares = defaultdict(float, shares or {})
        self.user_profile = to_profile_dict(user_profile)
        self.investment_start_date = None
        self.rebalance_date = None
        self.rebalanced_in_cycle = False
        self.entry_score_percentiles = {}
        self.entry_score_percentile_history = {}

    # ---- Stan cyklu inwestycyjnego ----
    def has_active_cycle(self) -> bool:
        return self.investment_start_date is not None

    def investment_time_days(self) -> int:
        return int(
            round(float(self.user_profile.get("investment_time_days", INVESTMENT_TIME_MAX_DAYS)))
        )

    def rebalance_time_share(self) -> float:
        return float(
            self.user_profile.get("rebalance_time_share", REBALANCE_TIME_MIN_SHARE)
        )

    def investment_rebalance_delta(self) -> timedelta:
        return timedelta(days=self.investment_time_days() * self.rebalance_time_share())

    def elapsed_cycle_days(self, date_time) -> float:
        if self.investment_start_date is None:
            return 0.0
        return (date_time - self.investment_start_date).total_seconds() / 86400.0

    def cycle_has_expired(self, date_time) -> bool:
        return self.elapsed_cycle_days(date_time) >= self.investment_time_days()

    def should_rebalance_cycle(self, date_time) -> bool:
        rebalance_after_days = self.investment_time_days() * self.rebalance_time_share()
        return (
            self.has_active_cycle()
            and not self.rebalanced_in_cycle
            and self.elapsed_cycle_days(date_time) >= rebalance_after_days
        )

    def record_score_percentiles(self, score_percentiles: dict[str, float], date_time) -> None:
        for ticker, percentile in score_percentiles.items():
            ticker_history = self.entry_score_percentile_history.setdefault(ticker, [])
            if ticker_history and ticker_history[-1][0] == date_time:
                ticker_history[-1] = (date_time, percentile)
            else:
                ticker_history.append((date_time, percentile))

    def reset_score_percentile_history(self, score_percentiles: dict[str, float], date_time) -> None:
        self.entry_score_percentile_history = {
            ticker: [(date_time, percentile)]
            for ticker, percentile in score_percentiles.items()
        }

    def start_cycle(
        self,
        target_tickers: Iterable[str],
        score_percentiles: dict[str, float],
        date_time,
    ) -> None:
        self.investment_start_date = date_time
        self.rebalance_date = date_time + self.investment_rebalance_delta()
        self.rebalanced_in_cycle = False
        self.entry_score_percentiles = {
            ticker: score_percentiles[ticker]
            for ticker in target_tickers
            if ticker in score_percentiles
        }

    def restart_cycle(
        self,
        target_tickers: Iterable[str],
        score_percentiles: dict[str, float],
        date_time,
    ) -> None:
        self.reset_score_percentile_history(score_percentiles, date_time)
        self.start_cycle(target_tickers, score_percentiles, date_time)

    def mark_rebalanced(self, date_time) -> None:
        self.rebalanced_in_cycle = True
        self.rebalance_date = date_time

    def mean_entry_score_percentile(self, ticker: str, date_time):
        if self.investment_start_date is None:
            return None

        points = [
            point
            for point in self.entry_score_percentile_history.get(ticker, [])
            if self.investment_start_date <= point[0] <= date_time
        ]
        if not points:
            return None

        weighted_values = []
        weights = []
        for index, (timestamp, percentile) in enumerate(points):
            next_timestamp = (
                points[index + 1][0]
                if index + 1 < len(points)
                else date_time
            )
            segment_days = (
                min(next_timestamp, date_time) - timestamp
            ).total_seconds() / 86400.0
            if segment_days <= 0:
                continue
            weighted_values.append(percentile)
            weights.append(segment_days)

        total_weight = math.fsum(weights)
        if total_weight <= 0:
            return None
        return math.fsum(
            value * weight
            for value, weight in zip(weighted_values, weights)
        ) / total_weight

    def mean_entry_score_percentiles(self, tickers: Iterable[str], date_time) -> dict[str, float | None]:
        return {
            ticker: self.mean_entry_score_percentile(ticker, date_time)
            for ticker in tickers
        }

    def relative_entry_score_percentile_change(self, ticker: str, mean_percentile) -> float:
        entry_percentile = self.entry_score_percentiles.get(ticker)
        if entry_percentile is None or mean_percentile is None or entry_percentile <= 0:
            return 0.0
        return (mean_percentile - entry_percentile) / entry_percentile

    def replace_entry_score_percentiles(
        self,
        sold_tickers: Iterable[str],
        replacement_tickers: Iterable[str],
        score_percentiles: dict[str, float],
    ) -> None:
        for ticker in sold_tickers:
            self.entry_score_percentiles.pop(ticker, None)
        for ticker in replacement_tickers:
            if ticker in score_percentiles:
                self.entry_score_percentiles[ticker] = score_percentiles[ticker]

    def restore_cycle_state(
        self,
        *,
        investment_start_date,
        rebalance_date,
        rebalanced_in_cycle: bool,
        entry_score_percentiles: dict[str, float],
        entry_score_percentile_history: dict[str, list[tuple]],
    ) -> None:
        self.investment_start_date = investment_start_date
        self.rebalance_date = rebalance_date
        self.rebalanced_in_cycle = rebalanced_in_cycle
        self.entry_score_percentiles = dict(entry_score_percentiles or {})
        self.entry_score_percentile_history = {
            ticker: list(points)
            for ticker, points in (entry_score_percentile_history or {}).items()
        }

    def next_rebalance_date(self):
        if not self.has_active_cycle() or self.rebalanced_in_cycle:
            return None
        return self.investment_start_date + self.investment_rebalance_delta()

    def next_cycle_date(self):
        if not self.has_active_cycle():
            return None
        return self.investment_start_date + timedelta(days=self.investment_time_days())

    # ---- Operacje na portfelu ----
    def buy(self, ticker: str, amount: float, price: float) -> bool:
        cost = round(amount * price, 2)
        if cost <= self.cash:
            self.cash -= cost
            self.shares[ticker] = round(self.shares[ticker] + amount, 2)
            return True
        print("nie mam pineidzy na zakup" + ticker + "w ilosci " + str(amount) + "po cenie " + str(price) + "bo brakuje mi" + str(cost - self.cash))
        return False

    def sell(self, ticker: str, amount: float, price: float) -> bool:
        if amount <= self.shares.get(ticker, 0):
            self.cash += round(amount * price, 2)
            self.shares[ticker] = round(self.shares[ticker] - amount, 2)
            return True
        print("nie mam akcji na sprzedaz")
        return False

