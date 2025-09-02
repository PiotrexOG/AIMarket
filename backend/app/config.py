from datetime import datetime
import pytz
import yfinance as yf

TICKERS = ["AAPL", "TSLA", "NVDA"]

TICKERS_EXCHANGE_NAME = {}

for ticker_symbol in TICKERS:
    ticker = yf.Ticker(ticker_symbol)
    exchange = ticker.info.get("fullExchangeName", "Unknown Exchange")  # Domyślna wartość, jeśli brak danych
    TICKERS_EXCHANGE_NAME[ticker_symbol] = exchange


STARTING_CASH = 10000.0
NO_USERS = 2

tz = pytz.timezone("America/New_York")
START_TIME = tz.localize(datetime(2023, 10, 2, 9, 30))
END_TIME = tz.localize(datetime(2023, 12, 31, 23, 59))

