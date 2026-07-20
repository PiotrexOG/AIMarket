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
    FIXED_METRIC_WEIGHTS,
    TOP_M_MAX_SHARE,
    TOP_M_MIN_SHARE,
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
        self.top_m_share = np.clip(self.top_m_share, TOP_M_MIN_SHARE, TOP_M_MAX_SHARE)

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
        target_weights = self._calculate_target_weights(score_matrix, ticker_indices)
        self._rebalance_to_target_weights(target_weights, price_vector, ticker_indices)

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
            score = sum(
                relative_scores.get(metric, 0.0) * FIXED_METRIC_WEIGHTS[metric]
                for metric in FIXED_METRIC_WEIGHTS
            )
            scores[:, ticker_idx] = score

        return np.round(scores, 10)

    def _calculate_target_weights(self, score_matrix: np.ndarray, ticker_indices: np.ndarray) -> np.ndarray:
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

    def _rebalance_to_target_weights(
            self,
            target_weights: np.ndarray,
            price_vector: np.ndarray,
            ticker_indices: np.ndarray,
    ) -> None:
        valid_price = price_vector > 0

        sell_quantities = np.where(valid_price[None, :], self.shares, 0.0)
        for ticker_idx in np.flatnonzero(valid_price):
            quantity = sell_quantities[:, ticker_idx]
            if not np.any(quantity > 0):
                continue

            self.shares[:, ticker_idx] = np.round(self.shares[:, ticker_idx] - quantity, 2)
            self.cash += money_round(quantity * price_vector[ticker_idx])

        buy_values = self.cash[:, None] * target_weights
        buy_quantities = np.zeros_like(self.shares)
        valid_target_prices = valid_price[ticker_indices]
        valid_indices = ticker_indices[valid_target_prices]
        buy_quantities[:, valid_indices] = smart_round(
            buy_values[:, valid_indices] / price_vector[valid_indices]
        )

        for ticker_idx in valid_indices:
            quantity = buy_quantities[:, ticker_idx]
            if not np.any(quantity > 0):
                continue

            costs = money_round(quantity * price_vector[ticker_idx])
            can_buy = (quantity > 0) & (costs <= self.cash)
            if not np.any(can_buy):
                continue

            self.cash[can_buy] -= costs[can_buy]
            self.shares[can_buy, ticker_idx] = np.round(
                self.shares[can_buy, ticker_idx] + quantity[can_buy],
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
                    "short_term_weight": profile["time_weights"]["short_term_14d"],
                    "medium_term_weight": profile["time_weights"]["medium_term_50d"],
                    "long_term_weight": profile["time_weights"]["long_term_200d"],
                    "metric_weights": dict(profile["metric_weights"]),
                    "change_ratio": round(float(change_ratio), 4),
                }
            )

        output_path = DATA_DIR / "results.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
