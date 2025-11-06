from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.market_data_service import MarketDataService
from app.shared.types import ValuationInterval, INTERVAL_MAP


class StockService:
    def __init__(self, db: Session):
        self.market_data_service = MarketDataService(db)

    def get_stock_valuation_in_range(
            self,
            ticker: str,
            start: datetime,
            end: datetime,
            interval: ValuationInterval,
    ) -> dict:
        """Zwraca wykres wartości spółki w zadanym zakresie czasu."""
        step = INTERVAL_MAP.get(interval)
        if not step:
            raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")

        valuations = []

        # Zawsze dodaj start
        dates_to_calculate = [start]

        # Dodaj punkty pośrednie
        current = start + step
        while current < end:  # '<' zamiast '<=', żeby uniknąć duplikatu z końcem
            dates_to_calculate.append(current)
            current += step

        # Zawsze dodaj end (chyba że jest taki sam jak start)
        if end != start:
            dates_to_calculate.append(end)

        # Oblicz wartości dla wszystkich dat
        for date in dates_to_calculate:
            price = self.market_data_service.get_price(ticker, date)
            if price is not None:
                valuations.append({
                    "datetime": date.isoformat(),
                    "value": price
                })

        if not valuations:
            raise HTTPException(status_code=404, detail="No valuation data found")

        # Oblicz zmiany procentowe NA PODSTAWIE valuation zamiast osobnych zapytań
        if valuations:
            start_value = valuations[0]["value"]
            end_value = valuations[-1]["value"]
            absolute_change = end_value - start_value
            percent_change = (absolute_change / start_value * 100) if start_value != 0 else 0.0
        else:
            start_value = end_value = absolute_change = percent_change = 0

        return {
            "percent_change": round(percent_change, 2),
            "history": valuations
        }
