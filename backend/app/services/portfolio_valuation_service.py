from datetime import datetime
from typing import Optional

from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService


class PortfolioValuationService:
    def __init__(self, portfolio_service: PortfolioService, market_data_service: MarketDataService):
        self.portfolio_service = portfolio_service
        self.market_data_service = market_data_service

    def calculate_portfolio_details(self, portfolio_id: int, date_time: datetime) -> Optional[dict]:
        # 1. pobierz stan portfela na dany dzień
        portfolio_state = self.portfolio_service.get_portfolio_state(portfolio_id, date_time)
        if not portfolio_state:
            return None

        shares = portfolio_state["shares"]
        cash = portfolio_state["cash"]

        # 2. pobierz ceny z rynku dla każdej spółki
        prices = {
            ticker: self.market_data_service.get_price(ticker, date_time)
            for ticker in shares
        }

        # 3. policz wartość pozycji
        positions = []
        total_value = cash

        for ticker, share_count in shares.items():
            price = prices.get(ticker)
            if price is None:
                continue  # np. brak danych rynkowych – można też rzucić wyjątkiem

            value = round(price * share_count, 2)
            positions.append({
                "ticker": ticker,
                "shares": share_count,
                "price": round(price, 2),
                "value": value
            })
            total_value += value

        # 4. zwróć wynik
        return {
            "cash": round(cash, 2),
            "total_value": round(total_value, 2),
            "positions": positions,
            "date_time": date_time
        }
