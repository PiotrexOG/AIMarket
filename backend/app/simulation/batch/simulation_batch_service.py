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
from app.services.layers.market_data_service import MarketDataService
from app.simulation.batch.helper import get_available_timestamps, fetch_cross_section

TIME_WEIGHT_KEYS = ("long_term_200d", "medium_term_50d", "short_term_14d")
METRIC_WEIGHT_KEYS = (
    "relative_asymmetry_profile",
    "relative_conviction",
    "relative_fundamental_support",
    "relative_structural_risk",
    "relative_technical_strength",
    "relative_valuation_sustainability",
)

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
            [profile.get("min_exposure", 0.5) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.aggression_slope = np.array(
            [profile.get("aggression_slope", 0.2) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.exposure_baseline = np.array(
            [profile.get("exposure_baseline", 5.0) for profile in self.user_profiles],
            dtype=np.float64,
        )
        self.rebalance_threshold = np.array(
            [profile.get("rebalance_threshold", 0.0) for profile in self.user_profiles],
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

        if current_time.date() == self.start_time.date() and np.any(self.is_benchmark):
            self._process_benchmark_buy(ticker_indices, price_vector)

        active_users = ~self.is_benchmark
        if not np.any(active_users):
            return

        score_matrix = self._calculate_score_matrix(market_scores)
        target_weights = self._calculate_target_weights(score_matrix, ticker_indices)
        portfolio_values, current_values = self._calculate_portfolio_values(price_vector)
        trade_quantities = self._calculate_trade_quantities(
            target_weights=target_weights,
            portfolio_values=portfolio_values,
            current_values=current_values,
            ticker_indices=ticker_indices,
            price_vector=price_vector,
        )

        trade_quantities[self.is_benchmark, :] = 0.0
        self._apply_trades(trade_quantities, price_vector, ticker_indices)

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

    def _process_benchmark_buy(self, ticker_indices: np.ndarray, price_vector: np.ndarray) -> None:
        benchmark_rows = np.flatnonzero(self.is_benchmark)
        if benchmark_rows.size == 0:
            return

        n = ticker_indices.size
        if n == 0:
            return

        portfolio_values, _ = self._calculate_portfolio_values(price_vector)
        target_per_ticker = portfolio_values[benchmark_rows] / n

        valid_prices = price_vector[ticker_indices] > 0
        valid_indices = ticker_indices[valid_prices]
        if valid_indices.size == 0:
            return

        prices = price_vector[valid_indices]
        quantities = smart_round(target_per_ticker[:, None] / prices[None, :])

        for local_idx, ticker_idx in enumerate(valid_indices):
            quantity = quantities[:, local_idx]
            costs = money_round(quantity * price_vector[ticker_idx])
            can_buy = (quantity > 0) & (costs <= self.cash[benchmark_rows])
            if not np.any(can_buy):
                continue

            rows = benchmark_rows[can_buy]
            self.cash[rows] -= costs[can_buy]
            self.shares[rows, ticker_idx] = np.round(
                self.shares[rows, ticker_idx] + quantity[can_buy],
                2,
            )

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

    def _calculate_target_weights(self, score_matrix: np.ndarray, ticker_indices: np.ndarray) -> np.ndarray:
        target_weights = np.zeros_like(score_matrix)
        if ticker_indices.size == 0:
            return target_weights

        active_rows = ~self.is_benchmark
        if not np.any(active_rows):
            return target_weights

        universe_scores = score_matrix[:, ticker_indices]
        top_scores = np.sort(universe_scores, axis=1)[:, ::-1][:, :5]
        avg_market_score = np.mean(top_scores, axis=1)
        raw_exposure = self.min_exposure + (
            avg_market_score - self.exposure_baseline
        ) * self.aggression_slope
        total_exposure = 1.0 / (1.0 + np.exp(-raw_exposure))
        total_exposure = np.where(active_rows, total_exposure, 0.0)

        scaled_scores = universe_scores / self.softmax_temp[:, None]
        row_max = np.max(scaled_scores, axis=1)
        exp_scores = np.exp(scaled_scores - row_max[:, None])
        exp_sums = exp_scores.sum(axis=1)

        valid_rows = (exp_sums > 0) & active_rows
        universe_weights = np.zeros_like(universe_scores)
        universe_weights[valid_rows] = (
            exp_scores[valid_rows]
            / exp_sums[valid_rows, None]
            * total_exposure[valid_rows, None]
        )
        target_weights[:, ticker_indices] = universe_weights
        return target_weights

    def _calculate_trade_quantities(
            self,
            target_weights: np.ndarray,
            portfolio_values: np.ndarray,
            current_values: np.ndarray,
            ticker_indices: np.ndarray,
            price_vector: np.ndarray,
    ) -> np.ndarray:
        current_weights = np.divide(
            current_values,
            portfolio_values[:, None],
            out=np.zeros_like(current_values),
            where=portfolio_values[:, None] > 0,
        )
        delta_weights = target_weights - current_weights

        in_universe = np.zeros(len(self.tickers), dtype=bool)
        in_universe[ticker_indices] = True

        held = self.shares > 0
        target_zero = target_weights == 0.0
        close_position = target_zero & held & in_universe[None, :]
        over_threshold = np.abs(delta_weights) >= self.rebalance_threshold[:, None]
        must_sell = close_position | (in_universe[None, :] & over_threshold & (delta_weights < 0))
        must_buy = in_universe[None, :] & over_threshold & (delta_weights > 0) & (target_weights > 0.0)

        expected_sell = np.where(
            must_sell & held,
            np.abs(delta_weights) * portfolio_values[:, None],
            0.0,
        ).sum(axis=1)
        expected_buy = np.where(must_buy, delta_weights * portfolio_values[:, None], 0.0).sum(axis=1)
        cash_gap = expected_buy - (self.cash + expected_sell)

        active = must_sell | must_buy
        lazy_sell_candidates = (
            in_universe[None, :]
            & ~active
            & (target_weights > 0.0)
            & (delta_weights < 0)
        )
        lazy_order = np.argsort(np.where(lazy_sell_candidates, delta_weights, np.inf), axis=1)

        for rank in range(ticker_indices.size):
            rows = np.flatnonzero(cash_gap > 0)
            if rows.size == 0:
                break

            cols = lazy_order[rows, rank]
            can_activate = lazy_sell_candidates[rows, cols]
            if not np.any(can_activate):
                continue

            active_rows = rows[can_activate]
            active_cols = cols[can_activate]
            active[active_rows, active_cols] = True
            cash_gap[active_rows] -= (
                np.abs(delta_weights[active_rows, active_cols])
                * portfolio_values[active_rows]
            )

        trade_quantities = np.zeros_like(self.shares)
        valid_price = price_vector > 0
        diff_values = portfolio_values[:, None] * target_weights - current_values
        trade_quantities[:, valid_price] = smart_round(
            diff_values[:, valid_price] / price_vector[valid_price]
        )

        trade_quantities = np.where(close_position, -self.shares, trade_quantities)
        trade_quantities = np.where(active & valid_price[None, :], trade_quantities, 0.0)

        sell_quantities = np.minimum(np.maximum(-trade_quantities, 0.0), self.shares)
        buy_quantities = np.maximum(trade_quantities, 0.0)
        return np.round(buy_quantities - sell_quantities, 2)

    def _apply_trades(
            self,
            trade_quantities: np.ndarray,
            price_vector: np.ndarray,
            ticker_indices: np.ndarray,
    ) -> None:
        sell_quantities = np.maximum(-trade_quantities, 0.0)
        for ticker_idx in ticker_indices:
            quantity = sell_quantities[:, ticker_idx]
            if not np.any(quantity > 0):
                continue

            self.shares[:, ticker_idx] = np.round(self.shares[:, ticker_idx] - quantity, 2)
            self.cash += money_round(quantity * price_vector[ticker_idx])

        buy_quantities = np.maximum(trade_quantities, 0.0)
        for ticker_idx in ticker_indices:
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

            if profile["archetype_key"] != "benchmark":
                results.append(
                    {
                        "id": int(self.user_ids[row_idx]),
                        "name": f"rand_{int(self.user_ids[row_idx])}",
                        "archetype_key": profile["archetype_key"],
                        "short_term_weight": profile["time_weights"]["short_term_14d"],
                        "medium_term_weight": profile["time_weights"]["medium_term_50d"],
                        "long_term_weight": profile["time_weights"]["long_term_200d"],
                        "min_exposure": profile.get("min_exposure", 0.5),
                        "aggression_slope": profile.get("aggression_slope", 0.2),
                        "exposure_baseline": profile.get("exposure_baseline", 5.0),
                        "rebalance_threshold": profile.get("rebalance_threshold", 0.0),
                        "softmax_temp": profile.get("softmax_temp", 1.0),
                        "metric_weights": dict(profile["metric_weights"]),
                        "change_ratio": round(float(change_ratio), 4),
                    }
                )

        output_path = DATA_DIR / "results.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
