from datetime import datetime, timezone

LOCALLY = True

TICKERS = [
"AAPL", "NVDA", "MSFT", "JPM", "XOM", "JNJ", "BA", "COST", "TSM", "NKE", "V", "DIS", "NFLX", "PFE", "WMT", "CVX", "GE", "SBUX"
]

STARTING_CASH = 100000.0

ZERO_TIME = datetime(2024, 3, 15, 13, 30, tzinfo=timezone.utc)

END_TIME = datetime(2026, 4, 22, 20, 30)
# START_TIME = datetime(2025, 3, 19, 13, 30, tzinfo=timezone.utc)
# #START_TIME = datetime(2026, 3, 11, 14, 30, tzinfo=timezone.utc)
# END_TIME = datetime(2026, 4, 28, 20, 30, tzinfo=timezone.utc)








