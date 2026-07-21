import json
import time
from datetime import datetime
from pathlib import Path
import numpy as np
from sqlalchemy.orm import Session

from app.portfolio_generation.archetype_config import get_archetype
from app.config.config import STARTING_CASH
from app.portfolio_generation.random_users import generate_users
from app.portfolio_generation.space_filling_users import generate_space_filling_users
from app.portfolio_generation.top_m import (
    INVESTMENT_TIME_MAX_DAYS,
    REBALANCE_TIME_MIN_SHARE,
    RELATIVE_SCORE_PERCENTILE_CHANGE_THRESHOLD,
    TOP_M_MAX_SHARE,
    calculate_average_score,
)
from app.services.layers.market_data_service import MarketDataService
from app.simulation.batch.helper import get_available_timestamps, fetch_cross_section

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "archetype_results"


def smart_round(values: np.ndarray) -> np.ndarray:
    return np.floor(values * 100) / 100


def money_round(values: np.ndarray) -> np.ndarray:
    return np.vectorize(lambda value: round(float(value), 2), otypes=[np.float64])(values)


class SimulationBatchService:
    def __init__(
        self,
        db: Session,
        tickers: list[str],
        zero_time: datetime,
        start_time: datetime,
        end_time: datetime,
        users_per_archetype: int,
        delta_days,
        archetypes_config,

    ):
        self.shares = None
        self.db = db
        self.tickers = tickers
        self.ticker_to_idx = {ticker: idx for idx, ticker in enumerate(tickers)}
        self.zero_time = zero_time
        self.start_time = start_time
        self.end_time = end_time
        self.delta_days = delta_days
        self.archetypes_config = archetypes_config
        self.market_data_service = MarketDataService(db)

        self.user_profiles: list[dict] = []
        self.user_ids: np.ndarray = np.empty(0, dtype=np.int64)
        self.cash: np.ndarray = np.empty(0, dtype=np.float64)

        self.top_m_share: np.ndarray = np.empty(0, dtype=np.float64)
        self.investment_time_days: np.ndarray = np.empty(0, dtype=np.float64)
        self.rebalance_time_share: np.ndarray = np.empty(0, dtype=np.float64)
        self.investment_start_dates: list[datetime | None] = []
        self.rebalanced_in_cycle: np.ndarray = np.empty(0, dtype=bool)
        self.entry_score_percentiles: np.ndarray = np.empty((0, len(tickers)), dtype=np.float64)
        self.score_percentile_history: list[list[tuple[datetime, np.ndarray]]] = []

        self.initialize_users(users_per_archetype)

    def initialize_users(self, users_per_archetype: int) -> None:
        users_profiles = {}
        archetypes = get_archetype(self.archetypes_config)

        for arc_name in archetypes.keys():
            if arc_name == "random":
                users_profiles.update(
                    generate_space_filling_users(
                        arc_name,
                        users_per_archetype,
                        archetypes,
                    )
                )
            else:
                users_profiles.update(generate_users(arc_name, users_per_archetype, archetypes))

        self.user_profiles = list(users_profiles.values())
        users_count = len(self.user_profiles)

        self.user_ids = np.arange(users_count, dtype=np.int64)
        self.cash = np.full(users_count, STARTING_CASH, dtype=np.float64)
        self.shares = np.zeros((users_count, len(self.tickers)), dtype=np.float64)
        self.top_m_share = np.array(
            [profile.get("top_m_share", TOP_M_MAX_SHARE) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.investment_time_days = np.array(
            [
                profile.get("investment_time_days", INVESTMENT_TIME_MAX_DAYS)
                for profile in self.user_profiles
            ],
            dtype=np.float64,
        )
        self.rebalance_time_share = np.array(
            [
                profile.get("rebalance_time_share", REBALANCE_TIME_MIN_SHARE)
                for profile in self.user_profiles
            ],
            dtype=np.float64,
        )
        self.investment_start_dates = [None] * users_count
        self.rebalanced_in_cycle = np.zeros(users_count, dtype=bool)
        self.score_percentile_history = [[] for _ in range(users_count)]
        self.entry_score_percentiles = np.full(
            (users_count, len(self.tickers)),
            np.nan,
            dtype=np.float64,
        )

        print(f"Users initialized: {users_count}")

    def run_simulation(self) -> None:
        start_time = self.start_time.replace(tzinfo=None)
        end_time = self.end_time.replace(tzinfo=None)
        timestamps = [
            timestamp
            for timestamp in get_available_timestamps()
            if start_time <= timestamp <= end_time
        ]
        new_timestamps = timestamps + [end_time]
        prices = self.market_data_service.get_prices_for_timestamps(new_timestamps)

        cross_section_result = fetch_cross_section(timestamps)

        start = time.perf_counter()

        for current_time in timestamps:
            self._simulate_time_step(current_time, prices[current_time], cross_section_result[current_time])

        print("Symulacja zakonczona.")

        end = time.perf_counter()
        print(f"Czas wykonania: {end - start:.4f} sekundy")

        self.calculate_stats(prices)


    def _price_vector(self, prices: dict[str, float]) -> np.ndarray:
        return np.array([prices.get(ticker, 0.0) or 0.0 for ticker in self.tickers], dtype=np.float64)

    def _simulate_time_step(self, current_time: datetime, prices: dict[str, float], market_scores: dict) -> None:
        print(f"Symulacja dla: {current_time}")

        if not market_scores:
            return

        ticker_indices = self._collect_ticker_indices(market_scores)
        if ticker_indices.size == 0:
            return

        price_vector = self._price_vector(prices)

        score_matrix = self._calculate_score_matrix(market_scores)
        target_weights, active_rows, replacement_trades = self._calculate_cycle_trades(
            score_matrix,
            ticker_indices,
            price_vector,
            current_time,
        )
        self._rebalance_to_target_weights(target_weights, price_vector, active_rows)
        self._apply_trade_differences(replacement_trades, price_vector)

    def _collect_ticker_indices(self, market_scores: dict) -> np.ndarray:
        tickers = sorted(
            {
                ticker
                for timeframe_scores in market_scores.values()
                for ticker in timeframe_scores.keys()
                if ticker in self.ticker_to_idx
            }
        )
        return np.array([self.ticker_to_idx[ticker] for ticker in tickers], dtype=np.int64)

    def _calculate_portfolio_values(self, price_vector: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        current_values = money_round(self.shares * price_vector)
        portfolio_values = money_round(self.cash)

        for ticker_idx in range(len(self.tickers)):
            portfolio_values = money_round(portfolio_values + current_values[:, ticker_idx])

        return portfolio_values, current_values

    def _calculate_score_matrix(self, market_scores: dict) -> np.ndarray:
        scores = np.zeros((len(self.user_profiles), len(self.tickers)), dtype=np.float64)

        timeframe_scores = market_scores.get("long_term_200d")
        if not timeframe_scores:
            return scores

        for ticker, ticker_data in timeframe_scores.items():
            ticker_idx = self.ticker_to_idx.get(ticker)
            if ticker_idx is None:
                continue

            relative_scores = ticker_data.get("relative_scores", {})
            score = calculate_average_score(relative_scores)
            scores[:, ticker_idx] = score

        return np.round(scores, 10)

    def _calculate_initial_target_weights(self, score_matrix: np.ndarray, ticker_indices: np.ndarray) -> np.ndarray:
        target_weights = np.zeros_like(score_matrix)
        if ticker_indices.size == 0:
            return target_weights

        universe_scores = score_matrix[:, ticker_indices]
        universe_weights = np.zeros_like(universe_scores)

        order = np.argsort(-universe_scores, axis=1, kind="stable")
        rank_numbers = np.arange(1, ticker_indices.size + 1, dtype=np.float64)[None, :]
        target_counts = ticker_indices.size * self.top_m_share[:, None]
        full_counts = np.floor(target_counts)
        fractional_counts = target_counts - full_counts

        rank_weights = np.where(
            rank_numbers <= full_counts,
            1.0,
            np.where(rank_numbers == full_counts + 1, fractional_counts, 0.0),
        )
        selected_counts = rank_weights.sum(axis=1)
        valid_rows = selected_counts > 0.0
        rank_weights[valid_rows] = (
            rank_weights[valid_rows] / selected_counts[valid_rows, None]
        )

        rows = np.arange(len(self.user_profiles))[:, None]
        universe_weights[rows, order] = rank_weights
        target_weights[:, ticker_indices] = universe_weights
        return target_weights

    def _calculate_score_percentiles(
            self,
            score_matrix: np.ndarray,
            ticker_indices: np.ndarray,
    ) -> np.ndarray:
        percentiles = np.zeros_like(score_matrix)
        if ticker_indices.size == 0:
            return percentiles

        universe_scores = score_matrix[:, ticker_indices]
        ascending_order = np.argsort(universe_scores, axis=1, kind="stable")
        percentile_values = (
            np.arange(1, ticker_indices.size + 1, dtype=np.float64)
            / float(ticker_indices.size)
        )
        rows = np.arange(len(self.user_profiles))[:, None]
        universe_percentiles = np.zeros_like(universe_scores)
        universe_percentiles[rows, ascending_order] = percentile_values
        percentiles[:, ticker_indices] = universe_percentiles
        return percentiles

    def _slot_weights(self, top_m_share: float, universe_size: int) -> np.ndarray:
        target_count = universe_size * float(top_m_share)
        full_count = int(np.floor(target_count))
        fractional_count = target_count - full_count
        slot_count = full_count + (1 if fractional_count > 0 else 0)
        if slot_count == 0:
            return np.empty(0, dtype=np.float64)

        raw_weights = np.ones(slot_count, dtype=np.float64)
        if fractional_count > 0:
            raw_weights[-1] = fractional_count
        return raw_weights / raw_weights.sum()

    def _elapsed_since_cycle_start(self, row_idx: int, current_time: datetime) -> float | None:
        investment_start_date = self.investment_start_dates[row_idx]
        if investment_start_date is None:
            return None
        return (current_time - investment_start_date).total_seconds() / 86400.0

    def _record_score_percentiles(
            self,
            row_idx: int,
            score_percentiles: np.ndarray,
            current_time: datetime,
    ) -> None:
        row_history = self.score_percentile_history[row_idx]
        current_percentiles = score_percentiles[row_idx].copy()
        if row_history and row_history[-1][0] == current_time:
            row_history[-1] = (current_time, current_percentiles)
        else:
            row_history.append((current_time, current_percentiles))

    def _reset_score_percentile_history(
            self,
            row_idx: int,
            score_percentiles: np.ndarray,
            current_time: datetime,
    ) -> None:
        self.score_percentile_history[row_idx] = [
            (current_time, score_percentiles[row_idx].copy())
        ]

    def _mean_score_percentiles(self, row_idx: int, current_time: datetime) -> np.ndarray:
        means = np.full(len(self.tickers), np.nan, dtype=np.float64)
        investment_start_date = self.investment_start_dates[row_idx]
        if investment_start_date is None:
            return means

        points = [
            point
            for point in self.score_percentile_history[row_idx]
            if investment_start_date <= point[0] <= current_time
        ]
        if not points:
            return means

        total_days = 0.0
        weighted_sum = np.zeros(len(self.tickers), dtype=np.float64)
        for index, (timestamp, percentiles) in enumerate(points):
            next_timestamp = (
                points[index + 1][0]
                if index + 1 < len(points)
                else current_time
            )
            segment_days = (
                min(next_timestamp, current_time) - timestamp
            ).total_seconds() / 86400.0
            if segment_days <= 0:
                continue
            weighted_sum += percentiles * segment_days
            total_days += segment_days

        if total_days > 0:
            means = weighted_sum / total_days
        return means

    def _mark_cycle_start(
            self,
            row_idx: int,
            selected: list[int],
            score_percentiles: np.ndarray,
            current_time: datetime,
    ) -> None:
        self.investment_start_dates[row_idx] = current_time
        self.rebalanced_in_cycle[row_idx] = False
        self.entry_score_percentiles[row_idx, :] = np.nan
        for ticker_idx in selected:
            self.entry_score_percentiles[row_idx, ticker_idx] = score_percentiles[row_idx, ticker_idx]
        self._reset_score_percentile_history(row_idx, score_percentiles, current_time)

    def _calculate_cycle_trades(
            self,
            score_matrix: np.ndarray,
            ticker_indices: np.ndarray,
            price_vector: np.ndarray,
            current_time: datetime,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        target_weights = np.zeros_like(score_matrix)
        active_rows = np.zeros(len(self.user_profiles), dtype=bool)
        replacement_trades = np.zeros_like(score_matrix)
        if ticker_indices.size == 0:
            return target_weights, active_rows, replacement_trades

        score_percentiles = self._calculate_score_percentiles(score_matrix, ticker_indices)
        sorted_indices_by_score = np.argsort(
            -score_matrix[:, ticker_indices],
            axis=1,
            kind="stable",
        )

        for row_idx in range(len(self.user_profiles)):
            if self.user_profiles[row_idx].get("archetype_key") != "benchmark":
                self._record_score_percentiles(row_idx, score_percentiles, current_time)

            held_indices = [
                ticker_idx
                for ticker_idx in np.flatnonzero(self.shares[row_idx] > 0)
                if ticker_idx in set(ticker_indices.tolist())
            ]

            if self.user_profiles[row_idx].get("archetype_key") == "benchmark":
                if held_indices:
                    continue
                active_rows[row_idx] = True
                equal_weight = 1.0 / ticker_indices.size
                target_weights[row_idx, ticker_indices] = equal_weight
                continue

            slot_weights = self._slot_weights(self.top_m_share[row_idx], ticker_indices.size)
            slot_count = len(slot_weights)
            if slot_count == 0:
                self.investment_start_dates[row_idx] = current_time
                self.entry_score_percentiles[row_idx, :] = np.nan
                continue

            elapsed_days = self._elapsed_since_cycle_start(row_idx, current_time)
            if not held_indices or elapsed_days is None:
                selected = self._select_top_m_indices(
                    row_idx,
                    sorted_indices_by_score,
                    ticker_indices,
                    score_matrix,
                    slot_count,
                )
                active_rows[row_idx] = True
                for ticker_idx, weight in zip(selected, slot_weights):
                    target_weights[row_idx, ticker_idx] = weight
                self._mark_cycle_start(row_idx, selected, score_percentiles, current_time)
                continue

            if elapsed_days >= self.investment_time_days[row_idx]:
                selected = self._select_top_m_indices(
                    row_idx,
                    sorted_indices_by_score,
                    ticker_indices,
                    score_matrix,
                    slot_count,
                )
                active_rows[row_idx] = True
                for ticker_idx, weight in zip(selected, slot_weights):
                    target_weights[row_idx, ticker_idx] = weight
                self._mark_cycle_start(row_idx, selected, score_percentiles, current_time)
                continue

            rebalance_after_days = self.investment_time_days[row_idx] * self.rebalance_time_share[row_idx]
            if self.rebalanced_in_cycle[row_idx] or elapsed_days < rebalance_after_days:
                continue

            row_trades = self._calculate_replacement_trades(
                row_idx,
                held_indices,
                ticker_indices,
                score_percentiles,
                price_vector,
                current_time,
            )
            replacement_trades[row_idx] = row_trades
            self.rebalanced_in_cycle[row_idx] = True

        return target_weights, active_rows, replacement_trades

    def _select_top_m_indices(
            self,
            row_idx: int,
            sorted_indices_by_score: np.ndarray,
            ticker_indices: np.ndarray,
            score_matrix: np.ndarray,
            slot_count: int,
    ) -> list[int]:
        selected = [
            int(ticker_indices[local_idx])
            for local_idx in sorted_indices_by_score[row_idx][:slot_count]
        ]
        return self._sort_by_current_score(selected, score_matrix[row_idx])

    def _calculate_replacement_trades(
            self,
            row_idx: int,
            held_indices: list[int],
            ticker_indices: np.ndarray,
            score_percentiles: np.ndarray,
            price_vector: np.ndarray,
            current_time: datetime,
    ) -> np.ndarray:
        trade_differences = np.zeros(len(self.tickers), dtype=np.float64)
        mean_percentiles = self._mean_score_percentiles(row_idx, current_time)
        sold_indices = []

        for ticker_idx in held_indices:
            entry_percentile = self.entry_score_percentiles[row_idx, ticker_idx]
            mean_percentile = mean_percentiles[ticker_idx]
            if (
                not np.isfinite(entry_percentile)
                or entry_percentile <= 0
                or not np.isfinite(mean_percentile)
            ):
                continue

            relative_score_percentile_change = (
                mean_percentile - entry_percentile
            ) / entry_percentile
            if relative_score_percentile_change < RELATIVE_SCORE_PERCENTILE_CHANGE_THRESHOLD:
                sold_indices.append(ticker_idx)

        if not sold_indices:
            return trade_differences

        kept_indices = set(held_indices) - set(sold_indices)
        candidates = [
            int(ticker_idx)
            for ticker_idx in ticker_indices
            if int(ticker_idx) not in kept_indices
        ]
        candidates = sorted(
            candidates,
            key=lambda ticker_idx: (
                -mean_percentiles[ticker_idx]
                if np.isfinite(mean_percentiles[ticker_idx])
                else np.inf,
                self.tickers[ticker_idx],
            ),
        )
        replacement_indices = candidates[:len(sold_indices)]

        sale_proceeds = 0.0
        for ticker_idx in sold_indices:
            shares = self.shares[row_idx, ticker_idx]
            price = price_vector[ticker_idx]
            if shares <= 0 or price <= 0:
                continue
            trade_differences[ticker_idx] = -shares
            sale_proceeds += shares * price
            self.entry_score_percentiles[row_idx, ticker_idx] = np.nan

        if sale_proceeds <= 0 or not replacement_indices:
            return trade_differences

        cash_per_ticker = sale_proceeds / len(replacement_indices)
        for ticker_idx in replacement_indices:
            price = price_vector[ticker_idx]
            if price <= 0:
                continue
            quantity = smart_round(np.array([cash_per_ticker / price]))[0]
            if quantity <= 0:
                continue
            trade_differences[ticker_idx] = quantity
            self.entry_score_percentiles[row_idx, ticker_idx] = score_percentiles[row_idx, ticker_idx]

        return trade_differences

    def _sort_by_current_score(
            self,
            ticker_indices: list[int],
            current_scores: np.ndarray,
    ) -> list[int]:
        return sorted(
            ticker_indices,
            key=lambda ticker_idx: (-current_scores[ticker_idx], self.tickers[ticker_idx]),
        )

    def _rebalance_to_target_weights(
            self,
            target_weights: np.ndarray,
            price_vector: np.ndarray,
            active_rows: np.ndarray,
    ) -> None:
        if not np.any(active_rows):
            return

        valid_price = price_vector > 0
        active_row_indices = np.flatnonzero(active_rows)
        portfolio_values, _ = self._calculate_portfolio_values(price_vector)
        target_quantities = self.shares.copy()
        target_values = portfolio_values[:, None] * target_weights
        target_quantities[np.ix_(active_row_indices, valid_price)] = smart_round(
            target_values[np.ix_(active_row_indices, valid_price)]
            / price_vector[valid_price]
        )

        trade_differences = np.where(
            active_rows[:, None] & valid_price[None, :],
            target_quantities - self.shares,
            0.0,
        )
        self._apply_trade_differences(trade_differences, price_vector)

    def _apply_trade_differences(
            self,
            trade_differences: np.ndarray,
            price_vector: np.ndarray,
    ) -> None:
        rows, cols = np.nonzero(trade_differences)
        if rows.size == 0:
            return

        order = np.argsort(trade_differences[rows, cols], kind="stable")
        for row_idx, ticker_idx in zip(rows[order], cols[order]):
            difference = round(float(trade_differences[row_idx, ticker_idx]), 2)
            if difference == 0.0:
                continue

            price = price_vector[ticker_idx]
            if price <= 0:
                continue

            if difference < 0.0:
                quantity = min(abs(difference), self.shares[row_idx, ticker_idx])
                if quantity <= 0:
                    continue

                self.shares[row_idx, ticker_idx] = round(
                    self.shares[row_idx, ticker_idx] - quantity,
                    2,
                )
                self.cash[row_idx] += round(quantity * price, 2)
            else:
                cost = round(difference * price, 2)
                if cost > self.cash[row_idx]:
                    continue

                self.cash[row_idx] -= cost
                self.shares[row_idx, ticker_idx] = round(
                    self.shares[row_idx, ticker_idx] + difference,
                    2,
                )

    def calculate_stats(self, prices) -> None:
        end_time = self.end_time.replace(tzinfo=None)
        final_prices = prices[end_time]
        price_vector = self._price_vector(final_prices)
        portfolio_values, _ = self._calculate_portfolio_values(price_vector)

        results = []
        for row_idx, profile in enumerate(self.user_profiles):
            end_val = portfolio_values[row_idx]
            change_ratio = ((end_val - STARTING_CASH) / STARTING_CASH) if STARTING_CASH != 0 else 0.0

            results.append(
                {
                    "id": int(self.user_ids[row_idx]),
                    "name": profile.get("name", f"user_{int(self.user_ids[row_idx])}"),
                    "archetype_key": profile["archetype_key"],
                    "top_m_share": profile.get("top_m_share", TOP_M_MAX_SHARE),
                    "investment_time_days": int(self.investment_time_days[row_idx]),
                    "rebalance_time_share": round(float(self.rebalance_time_share[row_idx]), 6),
                    "change_ratio": round(float(change_ratio), 4),
                }
            )

        output_path = DATA_DIR / "results.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
