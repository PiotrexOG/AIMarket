from collections import defaultdict
from typing import Dict

from app.dto.portfolio_dto import PortfolioPerformanceBaseDTO

def to_profile_dict(dto: PortfolioPerformanceBaseDTO) -> dict:
    return {
        "id": dto.id,
        "name": dto.name,
        "archetype_key": dto.archetype_key,

        "time_weights": {
            "short_term_14d": dto.short_term_weight,
            "medium_term_50d": dto.medium_term_weight,
            "long_term_200d": dto.long_term_weight,
        },

        "risk_tolerance": dto.risk_tolerance,
        "rebalance_threshold": dto.rebalance_threshold,
        "min_score_threshold": dto.min_score_threshold,
        "softmax_temp": dto.softmax_temp,
        "metric_weights": dto.metric_weights,
    }

class Portfolio:
    def __init__(self, portfolio_id: int, starting_cash: float, user_profile: PortfolioPerformanceBaseDTO, shares: Dict[str, int] = None):
        self.portfolio_id = portfolio_id
        self.cash = starting_cash
        self.shares = defaultdict(float, shares or {})
        self.user_profile = to_profile_dict(user_profile)

    # ---- Operacje na portfelu ----
    def buy(self, ticker: str, amount: float, price: float) -> bool:
        cost = round(amount * price, 2)
        if cost <= self.cash:
            self.cash -= cost
            self.shares[ticker] += amount
            return True
        return False

    def sell(self, ticker: str, amount: float, price: float) -> bool:
        if amount <= self.shares.get(ticker, 0):
            self.cash += round(amount * price, 2)
            self.shares[ticker] -= amount
            return True
        return False

