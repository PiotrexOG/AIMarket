import os
import csv
import yfinance as yf
from datetime import datetime
from app.core.data_loader import fetch_data, load_market_data

class MarketDataStore:
    def __init__(self, tickers, start_date, end_date):
        self.tickers = tickers
        self.data = {}
        for ticker in tickers:
            file_name = f"{ticker}.csv"
            if not os.path.exists(file_name):
                fetch_data(start_date, end_date, ticker, "1h")
            self.data[ticker] = load_market_data(ticker)

    def _find_row_by_datetime(self, ticker, date_time):
        """Pomocnicza funkcja do znajdowania wiersza po dacie"""
        for row in self.data[ticker]:
            row_datetime = datetime.strptime(row['Datetime'], "%Y-%m-%d %H:%M:%S")
            if row_datetime == date_time:
                return row
        return None

    def get_data_for_day(self, date_time):
        """Pobiera dane dla wszystkich tickerów na konkretną datę i godzinę"""
        return {ticker: self._find_row_by_datetime(ticker, date_time)
                for ticker in self.tickers}

    def get_price(self, ticker, date_time):
        """Pobiera cenę zamknięcia dla konkretnego tickera i daty"""
        row = self._find_row_by_datetime(ticker, date_time)
        return float(row['Close']) if row else None

    def get_length(self):
        return len(next(iter(self.data.values())))

    def get_dates(self):
        return [datetime.strptime(row["Datetime"], "%Y-%m-%d %H:%M:%S")
                for row in self.data["AAPL"]]
