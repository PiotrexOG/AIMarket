from collections import defaultdict
from typing import Dict

from app.dto.portfolio_dto import PortfolioPerformanceBaseDTO

def to_profile_dict(dto: PortfolioPerformanceBaseDTO) -> dict:
    return {
        "id": dto.id,
        "name": dto.name,
        "archetype_key": dto.archetype_key,

        "top_m_share": dto.top_m_share,
        "investment_time_days": dto.investment_time_days,
        "rebalance_time_share": dto.rebalance_time_share,
        "metric_weights": dto.metric_weights,
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

