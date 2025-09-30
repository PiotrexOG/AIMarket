from datetime import datetime, timezone
import yfinance as yf

TICKERS = ["AAPL", "TSLA", "NVDA"]

TICKERS_EXCHANGE_NAME = {}

for ticker_symbol in TICKERS:
    ticker = yf.Ticker(ticker_symbol)
    exchange = ticker.info.get("fullExchangeName", "Unknown Exchange")  # Domyślna wartość, jeśli brak danych
    TICKERS_EXCHANGE_NAME[ticker_symbol] = exchange

DEBUG_RESET = True
REAL_TIME = False

LOCALLY = True

STARTING_CASH = 10000.0
NO_USERS = 2

# NY 2023-10-02 09:30 -> UTC 2023-10-02 13:30
START_TIME = datetime(2023, 10, 2, 13, 30, tzinfo=timezone.utc)

# NY 2023-10-03 23:59 -> UTC 2023-10-04 03:59
END_TIME = datetime(2023, 12, 4, 20, 30, tzinfo=timezone.utc)
