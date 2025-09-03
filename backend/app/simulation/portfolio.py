from datetime import datetime
from collections import defaultdict
from app.services.portfolio_service import PortfolioService
from app.schemas.portfolio import PortfolioHistoryCreate, PortfolioShareCreate

class Portfolio:
    def __init__(self, portfolio_id: int, starting_cash: float):
        self.portfolio_id = portfolio_id
        self.cash = starting_cash
        self.shares = defaultdict(int)

    # ---- Operacje na portfelu ----
    def buy(self, ticker: str, amount: int, price: float) -> bool:
        cost = round(amount * price, 2)
        if cost <= self.cash:
            self.cash -= cost
            self.shares[ticker] += amount
            return True
        return False

    def sell(self, ticker: str, amount: int, price: float) -> bool:
        if amount <= self.shares.get(ticker, 0):
            self.cash += round(amount * price, 2)
            self.shares[ticker] -= amount
            return True
        return False

