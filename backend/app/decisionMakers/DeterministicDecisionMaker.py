import math

from app.portfolio_generation.top_m import (
    TOP_M_MAX_SHARE,
    FIXED_METRIC_WEIGHTS,
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
        target_weights = self._build_target_weights(raw_scores, profile)

        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash,
            portfolio.shares,
            date_time,
        )
        trade_differences = self._build_trade_differences(
            target_weights,
            valuation,
            date_time,
        )
        return self._build_decisions(trade_differences, target_weights)

    def _build_trade_differences(self, target_weights, valuation, date_time):
        current_shares = {
            position.ticker: position.shares
            for position in valuation.positions
            if position.shares > 0
        }
        tickers = set(current_shares) | set(target_weights)
        trade_differences = {}

        for ticker in tickers:
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            target_weight = target_weights.get(ticker, 0.0)
            target_shares = math.floor(
                (valuation.portfolio_value * target_weight / price) * 100
            ) / 100
            difference = round(target_shares - current_shares.get(ticker, 0.0), 2)
            if difference == 0.0:
                continue

            trade_differences[ticker] = difference

        return dict(
            sorted(
                trade_differences.items(),
                key=lambda item: (item[1], item[0]),
            )
        )

    def _build_decisions(self, trade_differences, target_weights):
        decisions = []
        for ticker, difference in trade_differences.items():
            if difference < 0.0:
                decisions.append({
                    "TICKER": ticker,
                    "DECISION": "SELL",
                    "NUMBER": abs(difference),
                    "TARGET_WEIGHT": round(target_weights.get(ticker, 0.0), 6),
                })
            elif difference > 0.0:
                decisions.append({
                    "TICKER": ticker,
                    "DECISION": "BUY",
                    "NUMBER": difference,
                    "TARGET_WEIGHT": round(target_weights.get(ticker, 0.0), 6),
                })

        return decisions
