# from app.core import market_hours
# from app.core.portfolio import Portfolio
# from app.core.decision_maker import DecisionMaker
# from datetime import datetime
#
#
# class UserSimulator:
#     def __init__(self, user_id: int, starting_cash: float, market_data_store, use_model: bool = False, with_explanation: bool = False):
#         self.user_id = user_id
#         self.portfolio = Portfolio(starting_cash)
#         self.decision_maker = DecisionMaker(use_model)
#         self.market_data_store = market_data_store
#         self.with_explanation = with_explanation
#
#     def process_day(self, date_time: datetime) -> None:
#         if not market_hours.is_market_open_by_exchange("AAPL", date_time):
#             return  # Skip if market is closed (using AAPL as proxy)
#
#         day_data = self.market_data_store.get_data_for_day(date_time)
#         pre_cash = self.portfolio.cash
#         pre_shares = dict(self.portfolio.shares)
#
#         for ticker, data in day_data.items():
#             if not market_hours.is_market_open_by_exchange(ticker, date_time):
#                 continue
#
#             decision, num, explanation = self.decision_maker.make_decision(
#                 ticker, data, self.portfolio, self.with_explanation
#             )
#             self.execute_decision(ticker, decision, num, float(data["Close"]))
#             self._print_decision(ticker, decision, num, date_time)
#
#         if self._portfolio_changed(pre_cash, pre_shares):
#             self.portfolio.evaluate(date_time)
#
#     def execute_decision(self, ticker: str, decision: str, num: int, price: float) -> None:
#         if decision == "KUPUJ":
#             self.portfolio.buy(ticker, num, price)
#         elif decision == "SPRZEDAJ":
#             self.portfolio.sell(ticker, num, price)
#
#     def calculate_portfolio_details(self, date_time: datetime) -> dict | None:
#         portfolio_state = self.portfolio.get_portfolio_state(date_time)
#         if not portfolio_state:
#             return None
#
#         shares = portfolio_state["shares"]
#         cash = portfolio_state["cash"]
#
#         prices = {
#             ticker: self.market_data_store.get_price(ticker, date_time)
#             for ticker in shares
#         }
#
#         positions = []
#         total_value = cash
#
#         for ticker, share_count in shares.items():
#             price = prices[ticker]
#             value = round(price * share_count, 2)
#             positions.append({
#                 "ticker": ticker,
#                 "shares": share_count,
#                 "price": round(price, 2),
#                 "value": value
#             })
#             total_value += value
#
#         return {
#             "cash": round(cash, 2),
#             "total_value": round(total_value, 2),
#             "positions": positions,
#             "date_time": date_time
#         }
#
#     def _portfolio_changed(self, pre_cash: float, pre_shares: dict) -> bool:
#         return self.portfolio.cash != pre_cash or self.portfolio.shares != pre_shares
#
#     def _print_decision(self, ticker: str, decision: str, num: int, date_time: datetime) -> None:
#         print(f"{self.user_id} ➤ {date_time} ➤ {ticker} ➤ {decision} {num}")
