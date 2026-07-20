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
        sell_decisions = self._build_sell_all_decisions(valuation.positions)
        buy_decisions = self._build_buy_decisions(target_weights, valuation.portfolio_value, date_time)
        return sell_decisions + buy_decisions

    def _build_sell_all_decisions(self, positions):
        decisions = []
        for position in positions:
            if position.shares <= 0:
                continue

            decisions.append({
                "TICKER": position.ticker,
                "DECISION": "SELL",
                "NUMBER": position.shares,
                "TARGET_WEIGHT": 0.0,
            })
        return decisions

    def _build_buy_decisions(self, target_weights, total_value, date_time):
        decisions = []
        for ticker, target_weight in target_weights.items():
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            shares = math.floor((total_value * target_weight / price) * 100) / 100
            if shares <= 0:
                continue

            decisions.append({
                "TICKER": ticker,
                "DECISION": "BUY",
                "NUMBER": shares,
                "TARGET_WEIGHT": round(target_weight, 6),
            })
        return decisions
