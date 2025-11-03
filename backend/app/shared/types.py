from datetime import timedelta
from typing import Literal

ValuationInterval = Literal["30m", "1h", "4h", "1d", "1w"]

# Definicja dostępnych interwałów
INTERVAL_MAP = {
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
    "1w": timedelta(days=7),
}