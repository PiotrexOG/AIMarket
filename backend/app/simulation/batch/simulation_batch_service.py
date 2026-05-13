import json
import time
from datetime import datetime
from pathlib import Path
import numpy as np
from sqlalchemy.orm import Session

from app.config.archetype_config import get_archetype
from app.config.config import END_TIME, STARTING_CASH
from app.services.layers.market_data_service import MarketDataService
from app.simulation.batch.helper import deserialize, get_available_timestamps, fetch_cross_section
from app.testy.random_users import generate_users


TIME_WEIGHT_KEYS = ("long_term_200d", "medium_term_50d", "short_term_14d")
METRIC_WEIGHT_KEYS = (
    "relative_asymmetry_profile",
    "relative_conviction",
    "relative_fundamental_support",
    "relative_structural_risk",
    "relative_technical_strength",
    "relative_valuation_sustainability",
)

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"

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
        self.shares: np.ndarray = np.empty((0, len(tickers)), dtype=np.int64)
        self.time_weights: np.ndarray = np.empty((0, len(TIME_WEIGHT_KEYS)), dtype=np.float64)
        self.metric_weights: np.ndarray = np.empty((0, len(METRIC_WEIGHT_KEYS)), dtype=np.float64)
        self.min_exposure: np.ndarray = np.empty(0, dtype=np.float64)
        self.aggression_slope: np.ndarray = np.empty(0, dtype=np.float64)
        self.exposure_baseline: np.ndarray = np.empty(0, dtype=np.float64)
        self.rebalance_threshold: np.ndarray = np.empty(0, dtype=np.float64)
        self.softmax_temp: np.ndarray = np.empty(0, dtype=np.float64)
        self.is_benchmark: np.ndarray = np.empty(0, dtype=bool)

        self.initialize_users(users_per_archetype)

    def initialize_users(self, users_per_archetype: int) -> None:
        users_profiles = {}
        archetypes = get_archetype(self.archetypes_config)

        for arc_name in archetypes.keys():
            users_profiles.update(generate_users(arc_name, users_per_archetype, archetypes))

        self.user_profiles = list(users_profiles.values())
        users_count = len(self.user_profiles)

        self.user_ids = np.arange(users_count, dtype=np.int64)
        self.cash = np.full(users_count, STARTING_CASH, dtype=np.float64)
        self.shares = np.zeros((users_count, len(self.tickers)), dtype=np.int64)
        self.time_weights = np.array(
            [
                [profile["time_weights"].get(key, 0.0) for key in TIME_WEIGHT_KEYS]
                for profile in self.user_profiles
            ],
            dtype=np.float64,
        )
        self.metric_weights = np.array(
            [
                [profile["metric_weights"].get(key, 0.0) for key in METRIC_WEIGHT_KEYS]
                for profile in self.user_profiles
            ],
            dtype=np.float64,
        )
        self.min_exposure = np.array(
            [profile.get("min_exposure", 0.0) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.aggression_slope = np.array(
            [profile.get("aggression_slope", 4.5) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.exposure_baseline = np.array(
            [profile.get("exposure_baseline", 4.5) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.rebalance_threshold = np.array(
            [profile.get("rebalance_threshold", 0.02) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.softmax_temp = np.maximum(
            np.array(
                [profile.get("softmax_temp", 1.0) for profile in self.user_profiles],
                dtype=np.float64,
            ),
            1e-6,
        )
        self.is_benchmark = np.array(
            [profile.get("name") == "benchmark" for profile in self.user_profiles],
            dtype=bool,
        )

        print(f"Users initialized: {users_count}")

    def run_simulation(self) -> None:
        timestamps = get_available_timestamps()
        new_timestamps = timestamps + [self.end_time.replace(tzinfo=None)]
        prices = self.market_data_service.get_prices_for_timestamps(new_timestamps)

        cross_section_result = fetch_cross_section(timestamps)

        start = time.perf_counter()

        for current_time in timestamps:
            self._simulate_time_step(current_time, prices[current_time], cross_section_result[current_time])

        print("Symulacja zakonczona.")

        end = time.perf_counter()
        print(f"Czas wykonania: {end - start:.4f} sekundy")

        self.calculate_stats(prices)

    def _simulate_time_step(self, current_time: datetime, prices, cross_section_result) -> None:
        print(f"Symulacja dla: {current_time}")

        if not cross_section_result:
            return

        price_vector = self._price_vector(prices)

        if current_time.date() == self.start_time.date() and np.any(self.is_benchmark):
            self._process_benchmark_buy(cross_section_result, price_vector)

        score_matrix = self._calculate_score_matrix(cross_section_result)
        if score_matrix.size == 0:
            return

        target_weights = self._calculate_target_weights(score_matrix)
        if not np.any(target_weights):
            return

        portfolio_values = self.cash + self.shares @ price_vector
        current_values = self.shares * price_vector
        target_values = portfolio_values[:, None] * target_weights
        diff_values = target_values - current_values
        threshold_amounts = portfolio_values * self.rebalance_threshold

        with np.errstate(divide="ignore", invalid="ignore"):
            trade_quantities = np.rint(diff_values / price_vector).astype(np.int64)

        can_trade = (
            (price_vector > 0)
            & ~self.is_benchmark[:, None]
            & (np.abs(diff_values) > (threshold_amounts[:, None] + 1e-12))
            & (np.abs(trade_quantities) >= 2)
        )
        trade_quantities = np.where(can_trade, trade_quantities, 0)

        self._apply_trades(trade_quantities, price_vector)

    def _price_vector(self, prices: dict[str, float]) -> np.ndarray:
        return np.array([prices.get(ticker, 0.0) or 0.0 for ticker in self.tickers], dtype=np.float64)

    def _process_benchmark_buy(self, market_scores: dict, price_vector: np.ndarray) -> None:
        tradable_tickers = sorted(
            {
                ticker
                for timeframe_scores in market_scores.values()
                for ticker in timeframe_scores.keys()
                if ticker in self.ticker_to_idx
            }
        )
        if not tradable_tickers:
            return

        ticker_indices = np.array([self.ticker_to_idx[ticker] for ticker in tradable_tickers], dtype=np.int64)
        prices = price_vector[ticker_indices]
        valid_prices = prices > 0
        if not np.any(valid_prices):
            return

        benchmark_rows = np.flatnonzero(self.is_benchmark)
        target_per_stock_value = self.cash[benchmark_rows] / len(tradable_tickers)
        quantities = np.zeros((len(benchmark_rows), len(ticker_indices)), dtype=np.int64)
        quantities[:, valid_prices] = np.floor(target_per_stock_value[:, None] / prices[valid_prices]).astype(np.int64)

        costs = np.round(quantities * prices, 2)
        total_costs = costs.sum(axis=1)
        affordable = total_costs <= self.cash[benchmark_rows]

        rows = benchmark_rows[affordable]
        if rows.size == 0:
            return

        self.shares[np.ix_(rows, ticker_indices)] += quantities[affordable]
        self.cash[rows] -= total_costs[affordable]

    def _calculate_score_matrix(self, market_scores: dict) -> np.ndarray:
        scores = np.zeros((len(self.user_profiles), len(self.tickers)), dtype=np.float64)

        for time_idx, timeframe in enumerate(TIME_WEIGHT_KEYS):
            timeframe_scores = market_scores.get(timeframe)
            if not timeframe_scores:
                continue

            user_time_weights = self.time_weights[:, time_idx]
            for ticker, ticker_data in timeframe_scores.items():
                ticker_idx = self.ticker_to_idx.get(ticker)
                if ticker_idx is None:
                    continue

                relative_scores = ticker_data.get("relative_scores", {})
                metric_scores = np.array(
                    [relative_scores.get(metric, 0.0) for metric in METRIC_WEIGHT_KEYS],
                    dtype=np.float64,
                )
                scores[:, ticker_idx] += user_time_weights * (self.metric_weights @ metric_scores)

        return np.round(scores, 10)

    def _calculate_target_weights(self, score_matrix: np.ndarray) -> np.ndarray:
        eligible = (score_matrix >= self.min_score_threshold[:, None]) & ~self.is_benchmark[:, None]
        if not np.any(eligible):
            return np.zeros_like(score_matrix)

        scaled_scores = np.divide(score_matrix, self.softmax_temp[:, None])
        scaled_scores = np.where(eligible, scaled_scores, -np.inf)

        row_max = np.max(scaled_scores, axis=1)
        has_scores = np.isfinite(row_max)
        safe_row_max = np.where(has_scores, row_max, 0.0)

        exp_scores = np.where(eligible, np.exp(scaled_scores - safe_row_max[:, None]), 0.0)
        exp_sums = exp_scores.sum(axis=1)

        target_weights = np.zeros_like(score_matrix)
        valid_rows = exp_sums > 0
        target_weights[valid_rows] = (
            exp_scores[valid_rows]
            / exp_sums[valid_rows, None]
            * self.risk_tolerance[valid_rows, None]
        )
        return target_weights

    def _apply_trades(self, trade_quantities: np.ndarray, price_vector: np.ndarray) -> None:
        sell_quantities = np.minimum(np.maximum(-trade_quantities, 0), self.shares)
        if np.any(sell_quantities):
            self.shares -= sell_quantities
            self.cash += np.round(sell_quantities * price_vector, 2).sum(axis=1)

        buy_quantities = np.maximum(trade_quantities, 0)
        if not np.any(buy_quantities):
            return

        buy_costs = np.round(buy_quantities * price_vector, 2)
        total_buy_costs = buy_costs.sum(axis=1)
        overspent_rows = total_buy_costs > self.cash

        if np.any(overspent_rows):
            scale = np.divide(
                self.cash[overspent_rows],
                total_buy_costs[overspent_rows],
                out=np.zeros_like(self.cash[overspent_rows]),
                where=total_buy_costs[overspent_rows] > 0,
            )
            buy_quantities[overspent_rows] = np.floor(buy_quantities[overspent_rows] * scale[:, None]).astype(np.int64)
            buy_costs = np.round(buy_quantities * price_vector, 2)
            total_buy_costs = buy_costs.sum(axis=1)

        affordable_rows = total_buy_costs <= self.cash
        if not np.any(affordable_rows):
            return

        self.shares[affordable_rows] += buy_quantities[affordable_rows]
        self.cash[affordable_rows] -= total_buy_costs[affordable_rows]

    def calculate_stats(self, prices) -> None:
        end_time = END_TIME.replace(tzinfo=None)
        final_prices = prices[end_time]
        price_vector = self._price_vector(final_prices)
        portfolio_values = self.cash + self.shares @ price_vector

        results = []
        for row_idx, profile in enumerate(self.user_profiles):
            end_val = portfolio_values[row_idx]
            change_ratio = ((end_val - STARTING_CASH) / STARTING_CASH) if STARTING_CASH != 0 else 0.0

            results.append(
                {
                    "id": int(self.user_ids[row_idx]),
                    "name": f"rand_{int(self.user_ids[row_idx])}",
                    "archetype_key": profile["archetype_key"],
                    "short_term_weight": profile["time_weights"]["short_term_14d"],
                    "medium_term_weight": profile["time_weights"]["medium_term_50d"],
                    "long_term_weight": profile["time_weights"]["long_term_200d"],
                    "risk_tolerance": profile["risk_tolerance"],
                    "rebalance_threshold": profile["rebalance_threshold"],
                    "min_score_threshold": profile["min_score_threshold"],
                    "softmax_temp": profile["softmax_temp"],
                    "metric_weights": dict(profile["metric_weights"]),
                    "change_ratio": round(float(change_ratio), 4),
                }
            )

        output_path = DATA_DIR / "results.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
