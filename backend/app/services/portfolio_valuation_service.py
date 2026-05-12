from datetime import datetime

from app.dto.portfolio_dto import PortfolioValuation, PositionDetail
from app.services.layers.market_data_service import MarketDataService


class PortfolioValuationService:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    def calculate_portfolio_details(self, cash: float, shares: dict[str, float], date_time: datetime) -> PortfolioValuation:
        prices = {t: self.market_data_service.get_price(t, date_time) for t in shares.keys()}
        positions: list[PositionDetail] = []
        cash = round(cash, 2)
        total_value = cash

        for ticker, amount in shares.items():
            price = prices.get(ticker)
            if price is None or amount is None:
                continue
            value = round(amount * price, 2)
            position = PositionDetail(
                ticker=ticker,
                shares=round(amount,2),
                price=round(price, 2),
                value=value
            )
            positions.append(position)
            total_value = round(total_value + value, 2)

        return PortfolioValuation(cash=cash, portfolio_value=total_value, positions=positions, date=date_time)


