import time

from app.core.portfolio import Portfolio
from app.core.decision_maker import DecisionMaker



class UserSimulator:
    def __init__(self, user_id, starting_cash, tickers, market_data_store, use_model=False, with_explanation=False):
        self.user_id = user_id
        self.portfolio = Portfolio(starting_cash, tickers)
        self.decision_maker = DecisionMaker(use_model)
        self.market_data_store = market_data_store
        self.with_explanation = with_explanation
        self.history = []
        self._stop_event = False

        self.run_simulation()

    def run_simulation(self):
        date_times = self.market_data_store.get_dates()

        for date_time in date_times:
            if self._stop_event:
                break
            self.process_day(date_time)
            # time.sleep(0.1)

        print(f"✅ Symulacja użytkownika {self.user_id} zakończona.")

    def process_day(self, date_time):
        day_data = self.market_data_store.get_data_for_day(date_time)

        pre_cash = self.portfolio.cash
        pre_shares = dict(self.portfolio.shares)

        for ticker, data in day_data.items():
            decision, num, explanation = self.decision_maker.make_decision(
                ticker, data, self.portfolio, self.with_explanation
            )
            self.execute_decision(ticker, decision, num, float(data['Close']))
            print(f"{self.user_id} ➤ {date_time} ➤ {ticker} ➤ {decision} {num}")

        if self.portfolio.cash != pre_cash or self.portfolio.shares != pre_shares:
            self.portfolio.evaluate(date_time)


    def execute_decision(self, ticker, decision, num, price):
        if decision == "KUPUJ":
            self.portfolio.buy(ticker, num, price)
        elif decision == "SPRZEDAJ":
            self.portfolio.sell(ticker, num, price)

    def calculate_portfolio_details(self, date_time) -> dict:
        """Calculates all portfolio details for given date"""
        portfolio_state = self.portfolio.get_portfolio_state(date_time)
        if not portfolio_state:
            return None

        shares = portfolio_state["shares"]
        cash = portfolio_state["cash"]

        prices = {
            ticker: self.market_data_store.get_price(ticker, date_time)
            for ticker in shares.keys()
        }

        positions = []
        total_value = cash

        for ticker, share_count in shares.items():
            price = prices[ticker]
            value = round(price * share_count, 2)
            positions.append({
                "ticker": ticker,
                "shares": share_count,
                "price": round(price, 2),
                "value": value
            })
            total_value += value

        return {
            "cash": round(cash, 2),
            "total_value": round(total_value, 2),
            "positions": positions,
            "date_time": date_time
        }

    def stop(self):
        self._stop_event = True
