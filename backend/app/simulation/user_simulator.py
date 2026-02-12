from datetime import datetime
from typing import Dict, Any

from app.config import TICKERS
from app.db.schemas.portfolio import PortfolioShareCreate, PortfolioHistoryCreate
from app.decisionMakers.LLMGEMINIDM import LLMGEMINIDM
from app.simulation.portfolio import Portfolio
from app.core import market_hours
from app.testy.compute import data_valuation


class UserSimulator:
    def __init__(
        self,
        user_id: int,
        starting_cash: float,
        decision_maker,
        portfolio_service,
        market_data_service,
        valuation_service,
        fundamental_service,
        transaction_service,
        analyst_service,
        shares: Dict[str, int] = None,
        with_explanation: bool = False,
    ):
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
        self.fundamental_service = fundamental_service
        self.analyst_service = analyst_service

        self.llm_models = {ticker: LLMGEMINIDM(ticker) for ticker in TICKERS}


    def get_crucial_indicators(self, date_time: datetime):
        if not market_hours.is_market_open_by_exchange("AAPL", date_time):
            return

        results = {}

        for ticker in TICKERS:
            analyst_grades = self.analyst_service.get_latest(ticker, date_time, 2)
            fundamentals  = self.fundamental_service.get_latest(
                ticker,
                date_time
            )
            ohlcv = self.market_data_service.get_indicators(
                ticker,
                date_time,
                use_daily=True
            )

            current_valuation = data_valuation.calculate(fundamentals, ohlcv["Close"])

            results[ticker] = self.llm_models[ticker].create_prompt(analyst_grades, fundamentals, ohlcv, current_valuation)

        return results

    # ---------------------------------------------------------
    # Główny proces jednego dnia
    # ---------------------------------------------------------
    def process_day(self, date_time: datetime) -> None:

        crucial_indicators = self.get_crucial_indicators(date_time)

        if crucial_indicators is not None:
            print(date_time)
            self._print_nested_dict(crucial_indicators, indent=0)

        # pre_cash = self.portfolio.cash
        # pre_shares = dict(self.portfolio.shares)
        #
        # # Decyzja
        # try:
        #     decisions = self.decision_maker.make_decision(
        #         crucial_indicators,
        #         self.portfolio,
        #         self.with_explanation
        #     )
        #
        #     # Wykonanie decyzji
        #     self._execute_decisions(decisions, crucial_indicators, date_time)
        #
        # except Exception as e:
        #     print(f"[LLM] Error in decision: {e}")
        #
        # # Jeżeli portfel się zmienił → historia
        # if self._portfolio_changed(pre_cash, pre_shares):
        #     history_data = PortfolioHistoryCreate(
        #         datetime=date_time,
        #         cash=self.portfolio.cash,
        #         shares=[
        #             PortfolioShareCreate(ticker=t, amount=a)
        #             for t, a in self.portfolio.shares.items()
        #         ]
        #     )
        #     self.portfolio_service.evaluate(self.portfolio.portfolio_id, history_data)


    # ---------------------------------------------------------
    # Wspomagające funkcje
    # ---------------------------------------------------------

    def _execute_decisions(self, decisions, tickers_data, date_time):
        for ticker, d in decisions.items():
            dec = d.get("DECISION")
            qty = d.get("NUMBER")

            if ticker not in tickers_data:
                continue

            if not market_hours.is_market_open_by_exchange(ticker, date_time):
                continue

            price = float(tickers_data[ticker].get("Close", 0))

            self.execute_decision(ticker, dec, qty, price, date_time)

    def execute_decision(self, ticker: str, decision: str, num: int, price: float, date_time: datetime):
        if decision in ["BUY", "SELL"]:
            if decision == "BUY":
                self.portfolio.buy(ticker, num, price)
            elif decision == "SELL":
                self.portfolio.sell(ticker, num, price)

            # print(f"{self.user_id} ➤ {date_time} ➤ {ticker} ➤ {decision} {num}")

            self.transaction_service.record_transaction(
                portfolio_id=self.portfolio.portfolio_id,
                ticker=ticker,
                type_=decision,
                quantity=num,
                price=price,
                datetime_=date_time,
            )

    def _portfolio_changed(self, pre_cash, pre_shares) -> bool:
        return self.portfolio.cash != pre_cash or self.portfolio.shares != pre_shares


    def _print_nested_dict(self, data, indent=0):
        """Rekurencyjnie wypisuje słownik z wcięciami."""
        indent_str = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"{indent_str}{key}:")
                    self._print_nested_dict(value, indent + 1)
                else:
                    print(f"{indent_str}{key}: {value}")
        else:
            print(f"{indent_str}{data}")
