from datetime import datetime, timezone

REAL_TIME = False
LOCALLY = True

TICKERS = [
"AAPL", "NVDA", "MSFT", "JPM", "XOM", "JNJ", "BA", "COST", "TSM", "NKE", "V", "DIS", "NFLX", "PFE", "WMT", "CVX", "GE", "SBUX"
]


DEBUG_RESET = False

GENERATE_NEW_INDIVIDUAL = False

GENERATE_NEW_CROSS = False

FETCH_NEW_DATA = False

STARTING_CASH = 100000.0

USERS_PER_ARCHETYPE = 5

ZERO_TIME = datetime(2024, 3, 15, 13, 30, tzinfo=timezone.utc)
START_TIME = datetime(2025, 3, 19, 13, 30, tzinfo=timezone.utc)
#START_TIME = datetime(2026, 4, 8, 13, 30, tzinfo=timezone.utc)
#START_TIME = datetime(2026, 3, 11, 14, 30, tzinfo=timezone.utc)
END_TIME = datetime(2026, 4, 13, 20, 30, tzinfo=timezone.utc)









