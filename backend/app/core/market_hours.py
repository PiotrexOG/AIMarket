from datetime import datetime, time
import pytz
import holidays

from datetime import timezone
import yfinance as yf

from app.config.config import TICKERS

TICKERS_EXCHANGE_NAME = {}
for ticker_symbol in TICKERS:
    ticker = yf.Ticker(ticker_symbol)
    exchange = ticker.info.get("fullExchangeName", "Unknown Exchange")  # Domyślna wartość, jeśli brak danych
    TICKERS_EXCHANGE_NAME[ticker_symbol] = exchange

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
        "tz": timezone.utc,  # ZMIANA: timezone.utc zamiast pytz.UTC
        "holidays": None
    },
    "CCY": {  # Forex
        "open": time(0, 0),
        "close": time(23, 59),
        "tz": timezone.utc,  # ZMIANA: timezone.utc zamiast pytz.UTC
        "holidays": None
    }
}

def is_market_open_by_exchange(ticker_str: str, dt_utc: datetime) -> bool:
    """
    Sprawdza, czy instrument jest otwarty w danym momencie.
    """
    if dt_utc.tzinfo is None:
        raise ValueError("Parametr dt_utc musi mieć przypisaną strefę czasową (UTC)")

    # ZMIANA: Używaj timezone.utc zamiast pytz.UTC
    if dt_utc.tzinfo != timezone.utc:
        raise ValueError("Parametr dt_utc musi być w UTC")

    exchange = TICKERS_EXCHANGE_NAME.get(ticker_str)
    if exchange not in EXCHANGE_HOURS:
        raise ValueError(f"Nieznana giełda: {exchange}")

    market = EXCHANGE_HOURS[exchange]
    market_tz = market["tz"]

    # konwersja z UTC -> lokalna strefa giełdy
    dt_local = dt_utc.astimezone(market_tz)

    # sprawdzanie świąt i weekendów
    if market["holidays"] and dt_local.date() in market["holidays"]:
        return False

    if dt_local.weekday() >= 5 and market["holidays"] is not None:
        return False  # weekend (tylko dla giełd z przerwami)

    # sprawdzanie godzin
    current_time = dt_local.time()
    return market["open"] <= current_time <= market["close"]
