from datetime import datetime
import pytz

TICKERS = {
    "AAPL": 100,
    "TSLA": 90,
    "NVDA": 70
}

START_DATE="2023-10-02"
END_DATE="2023-12-31"


start_time = datetime(2023, 10, 2, 9, 30, tzinfo=pytz.timezone("America/New_York"))
end_time = datetime(2023, 12, 31, 23, 59, tzinfo=pytz.timezone("America/New_York"))
