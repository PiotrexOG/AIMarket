from datetime import datetime, timedelta, timezone

import pytz
import yfinance as yf
import pandas as pd

class YahooClient:
    def __init__(self):
        self.timezone = timezone.utc

    def fetch_history(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
        interval: str
    ) -> pd.DataFrame:
        """
        Pobiera dane historyczne z Yahoo Finance dla danego tickera.
        """
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(
            start=start.strftime("%Y-%m-%d"),
            end=(end + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval=interval
        )

        if df.empty:
            return pd.DataFrame()  # brak danych

        # Reset index i dodanie kolumny Ticker
        df.reset_index(inplace=True)
        df['Ticker'] = ticker

        # Wybór kolumn i formatowanie
        df = df[['Datetime', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df['Datetime'] = pd.to_datetime(df['Datetime']).dt.tz_convert("UTC")
        df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].round(2)

        return df
