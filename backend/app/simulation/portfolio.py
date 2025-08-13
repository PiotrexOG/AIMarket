from datetime import datetime
from collections import defaultdict
from app.services.portfolio_service import PortfolioService
from app.schemas.portfolio import PortfolioHistoryCreate, PortfolioShareCreate

class Portfolio:
    def __init__(self, portfolio_id: int, starting_cash: float, portfolio_service: PortfolioService):
        self.portfolio_id = portfolio_id
        self.portfolio_service = portfolio_service
        self.cash = starting_cash
        self.shares = defaultdict(int)

    # ---- Operacje na portfelu ----
    def buy(self, ticker: str, amount: int, price: float) -> bool:
        cost = amount * price
        if cost <= self.cash:
            self.cash -= cost
            self.shares[ticker] += amount
            return True
        return False

    def sell(self, ticker: str, amount: int, price: float) -> bool:
        if amount <= self.shares.get(ticker, 0):
            self.cash += amount * price
            self.shares[ticker] -= amount
            return True
        return False

    # ---- Zapis historii do bazy ----
    def evaluate(self, date_time: datetime):
        # Tworzymy wpis historii
        history_data = PortfolioHistoryCreate(
            datetime=date_time,
            cash=self.cash,
            shares=[
                PortfolioShareCreate(ticker=t, amount=a)
                for t, a in self.shares.items()
            ]
        )
        self.portfolio_service.add_portfolio_history(self.portfolio_id, history_data)

    # ---- Pobranie stanu portfela w określonym czasie ----
    # W tej wersji baza trzyma pełną historię, więc metoda może pobierać z repo
    # Możemy też trzymać ostatni snapshot w pamięci, jeśli chcemy przyspieszyć symulację
