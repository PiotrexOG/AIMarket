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
        """Znajduje wiersz dokładnie dla daty lub najbliższą wcześniejszą."""
        rows = self.data[ticker]
        # parsujemy wszystkie daty
        closest_row = None
        for row in rows:
            row_datetime = datetime.strptime(row['Datetime'], "%Y-%m-%d %H:%M:%S")
            if row_datetime <= date_time:
                if closest_row is None or row_datetime > datetime.strptime(closest_row['Datetime'],
                                                                           "%Y-%m-%d %H:%M:%S"):
                    closest_row = row
        return closest_row

    def get_data_for_day(self, date_time):
        """Pobiera dane dla wszystkich tickerów na konkretną datę i godzinę"""
        return {ticker: self._find_row_by_datetime(ticker, date_time)
                for ticker in self.tickers}

    def get_price(self, ticker, date_time):
        """Pobiera cenę zamknięcia dla konkretnego tickera i daty"""
        row = self._find_row_by_datetime(ticker, date_time)
        return float(row['Close']) if row else None
