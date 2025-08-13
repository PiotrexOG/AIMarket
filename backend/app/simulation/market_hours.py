from datetime import datetime, time
import pytz
import holidays

from app.config import TICKERS_EXCHANGE_NAME

# Mapa exchange (z yfinance.info["exchange"]) -> godziny handlu i strefy czasowe
EXCHANGE_HOURS = {
    "NasdaqGS": {
        "open": time(9, 30),
        "close": time(16, 0),
        "tz": pytz.timezone("America/New_York"),
        "holidays": holidays.US()
    },
    "NYSE": {
        "open": time(9, 30),
        "close": time(16, 0),
        "tz": pytz.timezone("America/New_York"),
        "holidays": holidays.US()
    },
    "WAR": {
        "open": time(9, 0),
        "close": time(17, 5),
        "tz": pytz.timezone("Europe/Warsaw"),
        "holidays": holidays.Poland()
    },
    "CCC": {  # Crypto (BTC-USD itd.)
        "open": time(0, 0),
        "close": time(23, 59),
        "tz": pytz.UTC,
        "holidays": None  # 24/7
    },
    "CCY": {  # Forex
        "open": time(0, 0),
        "close": time(23, 59),
        "tz": pytz.UTC,
        "holidays": None  # 24/5
    }
}

def is_market_open_by_exchange(ticker_str: str, dt: datetime) -> bool:
    """
    Sprawdza, czy instrument (określony przez exchange z Yahoo Finance) jest otwarty w danym momencie.

    Parametry:
    - ticker_str: np. "AAPL", "TSLA"
    - dt: obiekt datetime z przypisaną strefą czasową (tzinfo)

    Zwraca:
    - True jeśli giełda otwarta, False jeśli zamknięta
    """
    exchange = TICKERS_EXCHANGE_NAME.get(ticker_str)

    if dt.tzinfo is None:
        raise ValueError("Parametr dt musi mieć przypisaną strefę czasową (tzinfo)")

    if exchange not in EXCHANGE_HOURS:
        raise ValueError(f"Nieznana giełda: {exchange}")

    market = EXCHANGE_HOURS[exchange]
    market_tz = market["tz"]
    dt_local = dt.astimezone(market_tz)

    if market["holidays"] and dt_local.date() in market["holidays"]:
        return False

    if dt_local.weekday() >= 5 and market["holidays"] is not None:
        return False  # weekend (dla giełd zamkniętych)

    current_time = dt_local.time()
    is_open = market["open"] <= current_time <= market["close"]
    return is_open
