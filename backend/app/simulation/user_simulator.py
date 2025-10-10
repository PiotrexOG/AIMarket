from datetime import datetime, timezone
from time import sleep
from typing import Dict

from app.config import TICKERS
from app.db.schemas.portfolio import PortfolioShareCreate, PortfolioHistoryCreate
from app.simulation.portfolio import Portfolio
from app.core.decision_maker import DecisionMaker
from app.core import market_hours


class UserSimulator:
    def __init__(self, user_id: int, starting_cash: float, portfolio_service, market_data_service, valuation_service, shares: Dict[str, int] = None, use_model: bool = False, with_explanation: bool = False):
        self.user_id = user_id
        self.portfolio = Portfolio(
            portfolio_id=user_id,
            starting_cash=starting_cash,
            shares=shares
        )
        self.decision_maker = DecisionMaker(use_model)
        self.portfolio_service = portfolio_service
        self.market_data_service = market_data_service
        self.valuation_service = valuation_service
        self.with_explanation = with_explanation


    def process_day(self, date_time: datetime) -> None:
        # Sprawdzamy czy giełda jest otwarta dla przykładowego tickera
        if not market_hours.is_market_open_by_exchange("AAPL", date_time):
            return  # Skip if market closed
        # Pobieramy dane rynkowe dla wszystkich tickerów i łączymy w jeden słownik
        day_data = {}
        for ticker in TICKERS:  # zakładamy, że serwis ma listę tickerów
            ticker_data = self.market_data_service.get_recent_data(ticker, date_time, limit=3)  # 1 rekord najnowszy
            if ticker_data:
                day_data[ticker] = ticker_data  # get_recent_data zwraca listę słowników

        pre_cash = self.portfolio.cash
        pre_shares = dict(self.portfolio.shares)

        for ticker, data in day_data.items():
            if not market_hours.is_market_open_by_exchange(ticker, date_time):
                continue

            decision, num, explanation = self.decision_maker.make_decision(
                ticker, data, self.portfolio, self.with_explanation
            )

            self.execute_decision(ticker, decision, num, float(data[0].close))
            self._print_decision(ticker, decision, num, date_time)

        # Jeśli coś się zmieniło -> policz z pamięci i zapisz
        if self._portfolio_changed(pre_cash, pre_shares):

                history_data = PortfolioHistoryCreate(
                    datetime=date_time,
                    cash=self.portfolio.cash,
                    shares=[
                        PortfolioShareCreate(ticker=t, amount=a)
                        for t, a in self.portfolio.shares.items()
                    ]
                )
                self.portfolio_service.evaluate(self.portfolio.portfolio_id, history_data)


    def execute_decision(self, ticker: str, decision: str, num: int, price: float):
        if decision == "KUPUJ":
            self.portfolio.buy(ticker, num, price)
        elif decision == "SPRZEDAJ":
            self.portfolio.sell(ticker, num, price)

    def _portfolio_changed(self, pre_cash: float, pre_shares: dict) -> bool:
        return self.portfolio.cash != pre_cash or self.portfolio.shares != pre_shares

    def _print_decision(self, ticker: str, decision: str, num: int, date_time: datetime):
        print(f"{self.user_id} ➤ {date_time} ➤ {ticker} ➤ {decision} {num}")
