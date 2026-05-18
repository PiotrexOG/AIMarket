from datetime import datetime

from app.dto.portfolio_dto import PortfolioValuation, PositionDetail
from app.services.layers.market_data_service import MarketDataService


class PortfolioValuationService:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    def calculate_portfolio_details(
        self,
        cash: float,
        shares: dict[str, float],
        date_time: datetime
    ) -> PortfolioValuation:

        prices = {
            t: self.market_data_service.get_price(t, date_time)
            for t in shares.keys()
        }

        cash = round(cash, 2)

        # 1. Najpierw policz wartości pozycji
        calculated_positions = []

        for ticker, amount in shares.items():
            price = prices.get(ticker)

            if price is None or amount is None:
                continue

            value = round(amount * price, 2)

            calculated_positions.append({
                "ticker": ticker,
                "shares": amount,
                "price": price,
                "value": value,
            })

        # 2. Oblicz total_value
        total_stock_value = sum(p["value"] for p in calculated_positions)
        total_value = round(cash + total_stock_value, 2)

        # 3. Utwórz finalne pozycje
        positions: list[PositionDetail] = []

        for p in calculated_positions:
            position = PositionDetail(
                ticker=p["ticker"],
                shares=round(p["shares"], 2),
                price=round(p["price"], 2),
                value=p["value"],
                value_of_portfolio=round(p["value"] / total_value, 4),
            )

            positions.append(position)

        positions.sort(key=lambda p: p.value, reverse=True)

        return PortfolioValuation(
            cash=cash,
            portfolio_value=total_value,
            positions=positions,
            date=date_time,
        )


