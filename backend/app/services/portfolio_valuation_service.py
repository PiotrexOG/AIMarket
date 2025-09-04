from datetime import datetime

from app.dto.portfolio_dto import PortfolioValuation
from app.services.market_data_service import MarketDataService


class PortfolioValuationService:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    def calculate_portfolio_details(self, cash: float, shares: dict[str, float], date_time: datetime) -> PortfolioValuation:
        prices = {t: self.market_data_service.get_price(t, date_time) for t in shares.keys()}
        positions = []
        cash = round(cash, 2)
        total_value = cash

        for ticker, amount in shares.items():
            price = prices.get(ticker)
            if price is None:
                continue
            value = round(amount * price, 2)
            positions.append({
                "ticker": ticker,
                "shares": amount,
                "price": round(price, 2),
                "value": value,
            })
            total_value = round(total_value + value, 2)

        return PortfolioValuation(cash=cash, portfolio_value=total_value, positions=positions, date=date_time)


