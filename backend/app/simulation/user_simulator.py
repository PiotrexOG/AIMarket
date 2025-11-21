from datetime import datetime, timezone
from typing import Dict

from app.config import TICKERS
from app.db.schemas.portfolio import PortfolioShareCreate, PortfolioHistoryCreate
from app.simulation.portfolio import Portfolio
from app.core import market_hours


class UserSimulator:
    def __init__(self, user_id: int, starting_cash: float, decision_maker, portfolio_service, market_data_service, valuation_service, transaction_service, shares: Dict[str, int] = None, use_model: bool = False, with_explanation: bool = False):
        self.user_id = user_id
        self.portfolio = Portfolio(
            portfolio_id=user_id,
            starting_cash=starting_cash,
            shares=shares
        )
        self.decision_maker = decision_maker
        self.portfolio_service = portfolio_service
        self.market_data_service = market_data_service
        self.valuation_service = valuation_service
        self.transaction_service = transaction_service
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

            self.execute_decision(ticker, decision, num, float(data[0].close), date_time)


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

    def process_dayGEM(self, date_time: datetime) -> None:
        # Sprawdzamy czy giełda jest otwarta dla przykładowego tickera
        if not market_hours.is_market_open_by_exchange("AAPL", date_time):
            return  # Skip if market closed

        # Pobieramy dane rynkowe dla wszystkich tickerów
        tickers_data = {}
        for ticker in TICKERS:  # zakładamy, że serwis ma listę tickerów
            # Używamy get_indicators zamiast get_recent_data, aby mieć wskaźniki techniczne
            indicators = self.market_data_service.get_indicators(ticker, date_time, use_daily=True)
            if indicators:
                tickers_data[ticker] = indicators  # get_indicators zwraca listę słowników ze wskaźnikami

        # Jeśli nie ma danych dla żadnego tickera, pomiń dzień
        if not tickers_data:
            return

        pre_cash = self.portfolio.cash
        pre_shares = dict(self.portfolio.shares)

        # Pojedyncze wywołanie LLM dla wszystkich tickerów
        try:
            result = self.decision_maker.make_decision(
                tickers_data, self.portfolio, self.with_explanation
            )


            # Parsowanie wyniku - nowy format zwraca decision, quantity, ticker, explanation
            decision = result["decision"]
            quantity = result["quantity"]
            ticker = result["ticker"]
            explanation = result["explanation"]

            print(f"[LLM] Decision: {decision} {quantity} shares of {ticker}")
            print(f"[LLM] Reason: {explanation}")

            # Wykonanie decyzji tylko jeśli ticker jest dostępny i giełda otwarta
            if ticker and ticker in tickers_data and market_hours.is_market_open_by_exchange(ticker, date_time):
                # Pobierz aktualną cenę z danych
                current_data = tickers_data[ticker][-1]  # najnowsze dane
                current_price = current_data.get('Close', 0)

                self.execute_decision(ticker, decision, quantity, float(current_price), date_time)

                # # Zapisanie historii decyzji LLM
                # self._save_llm_decision_history(date_time, ticker, decision, quantity, explanation, result["prompt"],
                #                                 result["response"])
            else:
                print(f"[LLM] Skipping execution - invalid ticker or market closed: {ticker}")

        except Exception as e:
            print(f"[LLM] Error making decision: {e}")

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

    def execute_decision(self, ticker: str, decision: str, num: int, price: float, date_time: datetime):
        if decision in ["BUY", "SELL"]:
            if decision == "BUY":
                self.portfolio.buy(ticker, num, price)
            elif decision == "SELL":
                self.portfolio.sell(ticker, num, price)

            #print(f"{self.user_id} ➤ {date_time} ➤ {ticker} ➤ {decision} {num}")

            self.transaction_service.record_transaction(
                portfolio_id=self.portfolio.portfolio_id,
                ticker=ticker,
                type_=decision,
                quantity=num,
                price=price,
                datetime_=date_time,
            )

    def _portfolio_changed(self, pre_cash: float, pre_shares: dict) -> bool:
        return self.portfolio.cash != pre_cash or self.portfolio.shares != pre_shares


