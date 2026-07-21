import math
from datetime import timedelta

import numpy as np

from app.portfolio_generation.top_m import (
    FIXED_METRIC_WEIGHTS,
    INVESTMENT_TIME_MAX_DAYS,
    RELATIVE_SCORE_PERCENTILE_CHANGE_THRESHOLD,
    REBALANCE_TIME_MIN_SHARE,
    TOP_M_MAX_SHARE,
    clamp_investment_time_days,
    clamp_rebalance_time_share,
    fractional_top_m_weights,
)


class DeterministicDecisionMaker:
    def __init__(self, valuation_service, start_time):
        self.valuation_service = valuation_service
        self.start_time = start_time

    def calculate_score(self, ticker, market_scores, profile):
        timeframe_data = market_scores.get("long_term_200d", {}).get(ticker, {})
        relative_scores = timeframe_data.get("relative_scores", {})
        values = [
            relative_scores.get(metric, 0.0) * FIXED_METRIC_WEIGHTS[metric]
            for metric in FIXED_METRIC_WEIGHTS
        ]
        return round(math.fsum(values), 10)

    def _build_target_weights(self, raw_scores: dict[str, float], profile: dict) -> dict[str, float]:
        sorted_tickers = sorted(
            raw_scores,
            key=lambda ticker: (-raw_scores[ticker], ticker),
        )
        return fractional_top_m_weights(
            sorted_tickers,
            profile.get("top_m_share", TOP_M_MAX_SHARE),
        )

    def make_decision(self, market_scores, portfolio, date_time):
        profile = portfolio.user_profile
        all_tickers = sorted({t for tf in market_scores for t in market_scores[tf].keys()})
        if not all_tickers:
            return []

        raw_scores = {
            ticker: self.calculate_score(ticker, market_scores, profile)
            for ticker in all_tickers
        }
        score_percentiles = self._calculate_score_percentiles(raw_scores)
        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash,
            portfolio.shares,
            date_time,
        )
        current_shares = self._current_shares(valuation)

        if profile.get("archetype_key") == "benchmark":
            if current_shares:
                return []
            target_weights = {ticker: 1.0 / len(all_tickers) for ticker in all_tickers}
            return self._build_buy_decisions_from_weights(target_weights, valuation, date_time)

        self._record_score_percentiles(portfolio, score_percentiles, date_time)

        if not current_shares or portfolio.investment_start_date is None:
            return self._start_new_cycle(portfolio, raw_scores, score_percentiles, valuation, date_time)

        investment_time_days = clamp_investment_time_days(
            profile.get("investment_time_days", INVESTMENT_TIME_MAX_DAYS)
        )
        elapsed_days = self._elapsed_days(portfolio.investment_start_date, date_time)
        if elapsed_days >= investment_time_days:
            return self._reset_cycle(portfolio, raw_scores, score_percentiles, valuation, date_time)

        rebalance_time_share = clamp_rebalance_time_share(
            profile.get("rebalance_time_share", REBALANCE_TIME_MIN_SHARE)
        )
        rebalance_after_days = investment_time_days * rebalance_time_share
        if not portfolio.rebalanced_in_cycle and elapsed_days >= rebalance_after_days:
            return self._rebalance_cycle(
                portfolio,
                raw_scores,
                score_percentiles,
                valuation,
                date_time,
            )

        return []

    def _calculate_score_percentiles(self, raw_scores: dict[str, float]) -> dict[str, float]:
        if not raw_scores:
            return {}

        sorted_tickers = sorted(raw_scores, key=lambda ticker: (raw_scores[ticker], ticker))
        universe_size = len(sorted_tickers)
        return {
            ticker: (rank + 1) / universe_size
            for rank, ticker in enumerate(sorted_tickers)
        }

    def _elapsed_days(self, start_date, date_time) -> float:
        return (date_time - start_date).total_seconds() / 86400.0

    def _current_shares(self, valuation) -> dict[str, float]:
        return {
            position.ticker: position.shares
            for position in valuation.positions
            if position.shares > 0
        }

    def _record_score_percentiles(self, portfolio, score_percentiles, date_time):
        history = portfolio.entry_score_percentile_history
        for ticker, percentile in score_percentiles.items():
            ticker_history = history.setdefault(ticker, [])
            if ticker_history and ticker_history[-1][0] == date_time:
                ticker_history[-1] = (date_time, percentile)
            else:
                ticker_history.append((date_time, percentile))

    def _reset_score_percentile_history(self, portfolio, score_percentiles, date_time):
        portfolio.entry_score_percentile_history = {
            ticker: [(date_time, percentile)]
            for ticker, percentile in score_percentiles.items()
        }

    def _set_cycle_state(self, portfolio, target_tickers, score_percentiles, date_time):
        portfolio.investment_start_date = date_time
        portfolio.rebalance_date = (
            date_time
            + self._investment_rebalance_delta(portfolio.user_profile)
        )
        portfolio.rebalanced_in_cycle = False
        portfolio.entry_score_percentiles = {
            ticker: score_percentiles[ticker]
            for ticker in target_tickers
            if ticker in score_percentiles
        }

    def _investment_rebalance_delta(self, profile):
        investment_time_days = clamp_investment_time_days(
            profile.get("investment_time_days", INVESTMENT_TIME_MAX_DAYS)
        )
        rebalance_time_share = clamp_rebalance_time_share(
            profile.get("rebalance_time_share", REBALANCE_TIME_MIN_SHARE)
        )
        return timedelta(days=investment_time_days * rebalance_time_share)

    def _start_new_cycle(self, portfolio, raw_scores, score_percentiles, valuation, date_time):
        target_weights = self._build_target_weights(raw_scores, portfolio.user_profile)
        self._reset_score_percentile_history(portfolio, score_percentiles, date_time)
        self._set_cycle_state(portfolio, target_weights, score_percentiles, date_time)
        return self._build_buy_decisions_from_weights(target_weights, valuation, date_time)

    def _reset_cycle(self, portfolio, raw_scores, score_percentiles, valuation, date_time):
        target_weights = self._build_target_weights(raw_scores, portfolio.user_profile)
        decisions = self._build_full_reset_decisions(target_weights, valuation, date_time)
        self._reset_score_percentile_history(portfolio, score_percentiles, date_time)
        self._set_cycle_state(portfolio, target_weights, score_percentiles, date_time)
        return decisions

    def _rebalance_cycle(
        self,
        portfolio,
        raw_scores,
        score_percentiles,
        valuation,
        date_time,
    ):
        current_shares = self._current_shares(valuation)
        mean_percentiles = {
            ticker: self._mean_score_percentile(portfolio, ticker, date_time)
            for ticker in raw_scores
        }
        sold_tickers = [
            ticker
            for ticker in current_shares
            if self._relative_score_percentile_change(
                portfolio.entry_score_percentiles.get(ticker),
                mean_percentiles.get(ticker),
            )
            < RELATIVE_SCORE_PERCENTILE_CHANGE_THRESHOLD
        ]
        portfolio.rebalanced_in_cycle = True
        portfolio.rebalance_date = date_time

        if not sold_tickers:
            return []

        kept_tickers = set(current_shares) - set(sold_tickers)
        candidate_tickers = [
            ticker
            for ticker in raw_scores
            if ticker not in kept_tickers
        ]
        candidate_tickers = sorted(
            candidate_tickers,
            key=lambda ticker: (
                -(mean_percentiles.get(ticker) if mean_percentiles.get(ticker) is not None else -math.inf),
                ticker,
            ),
        )
        replacement_tickers = candidate_tickers[:len(sold_tickers)]
        decisions = self._build_replacement_decisions(
            sold_tickers,
            replacement_tickers,
            current_shares,
            valuation,
            date_time,
        )
        for ticker in sold_tickers:
            portfolio.entry_score_percentiles.pop(ticker, None)
        for ticker in replacement_tickers:
            if ticker in score_percentiles:
                portfolio.entry_score_percentiles[ticker] = score_percentiles[ticker]
        return decisions

    def _relative_score_percentile_change(self, entry_percentile, mean_percentile):
        if entry_percentile is None or mean_percentile is None or entry_percentile <= 0:
            return 0.0
        return (mean_percentile - entry_percentile) / entry_percentile

    def _mean_score_percentile(self, portfolio, ticker, date_time):
        points = portfolio.entry_score_percentile_history.get(ticker, [])
        points = [
            point
            for point in points
            if point[0] >= portfolio.investment_start_date and point[0] <= date_time
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
            segment_days = self._elapsed_days(timestamp, min(next_timestamp, date_time))
            if segment_days <= 0:
                continue
            weighted_values.append(percentile)
            weights.append(segment_days)

        if not weights:
            return None
        return float(np.average(weighted_values, weights=weights))

    def _build_buy_decisions_from_weights(self, target_weights, valuation, date_time):
        decisions = []
        for ticker, target_weight in target_weights.items():
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue
            target_shares = math.floor(
                (valuation.portfolio_value * target_weight / price) * 100
            ) / 100
            if target_shares <= 0:
                continue
            decisions.append({
                "TICKER": ticker,
                "DECISION": "BUY",
                "NUMBER": target_shares,
                "TARGET_WEIGHT": round(target_weight, 6),
            })
        return sorted(decisions, key=lambda decision: decision["TICKER"])

    def _build_full_reset_decisions(self, target_weights, valuation, date_time):
        current_shares = self._current_shares(valuation)
        decisions = [
            {
                "TICKER": ticker,
                "DECISION": "SELL",
                "NUMBER": shares,
                "TARGET_WEIGHT": 0.0,
            }
            for ticker, shares in sorted(current_shares.items())
        ]
        decisions.extend(
            self._build_buy_decisions_from_weights(target_weights, valuation, date_time)
        )
        return decisions

    def _build_replacement_decisions(
        self,
        sold_tickers,
        replacement_tickers,
        current_shares,
        valuation,
        date_time,
    ):
        sale_proceeds = 0.0
        decisions = []
        for ticker in sorted(sold_tickers):
            shares = current_shares.get(ticker, 0.0)
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if shares <= 0 or not price or price <= 0:
                continue
            sale_proceeds += shares * price
            decisions.append({
                "TICKER": ticker,
                "DECISION": "SELL",
                "NUMBER": shares,
                "TARGET_WEIGHT": 0.0,
            })

        if not decisions or not replacement_tickers or sale_proceeds <= 0:
            return decisions

        cash_per_ticker = sale_proceeds / len(replacement_tickers)
        for ticker in replacement_tickers:
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue
            target_shares = math.floor((cash_per_ticker / price) * 100) / 100
            if target_shares <= 0:
                continue
            decisions.append({
                "TICKER": ticker,
                "DECISION": "BUY",
                "NUMBER": target_shares,
                "TARGET_WEIGHT": None,
            })
        return decisions
