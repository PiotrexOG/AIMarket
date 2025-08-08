from datetime import datetime
import pytz

TICKERS = ["AAPL", "TSLA", "NVDA"]
STARTING_CASH = 10000.0
NO_USERS = 2

start_time = datetime(2023, 10, 1, 9, 30, tzinfo=pytz.timezone("America/New_York"))
end_time = datetime(2023, 10, 5, 23, 59, tzinfo=pytz.timezone("America/New_York"))
