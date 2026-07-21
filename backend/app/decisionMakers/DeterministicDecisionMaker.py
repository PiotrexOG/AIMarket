import math

from app.portfolio_generation.top_m import (
    RELATIVE_SCORE_PERCENTILE_CHANGE_THRESHOLD,
    TOP_M_MAX_SHARE,
    calculate_average_score,
    fractional_top_m_weights,
)


class DeterministicDecisionMaker:
    def __init__(self, valuation_service, start_time, portfolio_service=None):
        self.valuation_service = valuation_service
        self.start_time = start_time
        self.portfolio_service = portfolio_service
        self._recorded_score_snapshot_keys = set()

    def calculate_score(self, ticker, market_scores, profile):
        timeframe_data = market_scores.get("long_term_200d", {}).get(ticker, {})
        relative_scores = timeframe_data.get("relative_scores", {})
        return calculate_average_score(relative_scores)

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
        self._record_score_snapshots(raw_scores, score_percentiles, date_time)
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

        portfolio.record_score_percentiles(score_percentiles, date_time)

        if not current_shares or not portfolio.has_active_cycle():
            return self._start_new_cycle(portfolio, raw_scores, score_percentiles, valuation, date_time)

        if portfolio.cycle_has_expired(date_time):
            return self._reset_cycle(portfolio, raw_scores, score_percentiles, valuation, date_time)

        if portfolio.should_rebalance_cycle(date_time):
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

    def _current_shares(self, valuation) -> dict[str, float]:
        return {
            position.ticker: position.shares
            for position in valuation.positions
            if position.shares > 0
        }

    def _start_new_cycle(self, portfolio, raw_scores, score_percentiles, valuation, date_time):
        target_weights = self._build_target_weights(raw_scores, portfolio.user_profile)
        portfolio.restart_cycle(target_weights, score_percentiles, date_time)
        self._record_cycle_event(
            portfolio,
            "START",
            date_time,
            selected_tickers=list(target_weights.keys()),
        )
        return self._build_buy_decisions_from_weights(target_weights, valuation, date_time)

    def _reset_cycle(self, portfolio, raw_scores, score_percentiles, valuation, date_time):
        target_weights = self._build_target_weights(raw_scores, portfolio.user_profile)
        decisions = self._build_full_reset_decisions(target_weights, valuation, date_time)
        portfolio.restart_cycle(target_weights, score_percentiles, date_time)
        self._record_cycle_event(
            portfolio,
            "RESET",
            date_time,
            selected_tickers=list(target_weights.keys()),
        )
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
        mean_percentiles = portfolio.mean_entry_score_percentiles(raw_scores, date_time)
        sold_tickers = [
            ticker
            for ticker in current_shares
            if portfolio.relative_entry_score_percentile_change(ticker, mean_percentiles.get(ticker))
            < RELATIVE_SCORE_PERCENTILE_CHANGE_THRESHOLD
        ]
        portfolio.mark_rebalanced(date_time)

        if not sold_tickers:
            self._record_cycle_event(
                portfolio,
                "REBALANCE",
                date_time,
                selected_tickers=list(current_shares.keys()),
            )
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
        portfolio.replace_entry_score_percentiles(
            sold_tickers,
            replacement_tickers,
            score_percentiles,
        )
        self._record_cycle_event(
            portfolio,
            "REBALANCE",
            date_time,
            sold_tickers=sold_tickers,
            replacement_tickers=replacement_tickers,
        )
        return decisions

    def _record_score_snapshots(self, raw_scores, score_percentiles, date_time):
        if self.portfolio_service is None:
            return

        key = (date_time, "long_term_200d")
        if key in self._recorded_score_snapshot_keys:
            return

        self.portfolio_service.record_score_snapshots(
            date_time,
            raw_scores,
            score_percentiles,
            timeframe="long_term_200d",
        )
        self._recorded_score_snapshot_keys.add(key)

    def _record_cycle_event(
        self,
        portfolio,
        event_type,
        date_time,
        *,
        selected_tickers=None,
        sold_tickers=None,
        replacement_tickers=None,
    ):
        if self.portfolio_service is None:
            return

        self.portfolio_service.record_cycle_event(
            portfolio,
            event_type,
            date_time,
            selected_tickers=selected_tickers,
            sold_tickers=sold_tickers,
            replacement_tickers=replacement_tickers,
        )

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
