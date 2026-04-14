from datetime import datetime, timezone

from sqlalchemy import false

from app.decisionMakers.tickerMaster.GEMINI_MASTER import GEMINI_MASTER
from app.decisionMakers.randomDecisionMaker import RandomDecisionMaker
from app.testy.archetypes import ARCHETYPES
from app.testy.random_users import generate_users

REAL_TIME = False
LOCALLY = True

# TICKERS = ["AAPL"]

TICKERS = [
"AAPL", "NVDA", "MSFT", "JPM", "XOM", "JNJ", "BA", "COST", "TSM", "NKE", "V", "DIS", "NFLX", "PFE", "WMT", "CVX", "GE", "SBUX"
]


DEBUG_RESET = True

GENERATE_NEW_INDIVIDUAL = False

GENERATE_NEW_CROSS = False

FETCH_NEW_DATA = False

STARTING_CASH = 100000.0

ZERO_TIME = datetime(2024, 3, 15, 13, 30, tzinfo=timezone.utc)
START_TIME = datetime(2025, 3, 19, 13, 30, tzinfo=timezone.utc)
#START_TIME = datetime(2026, 3, 11, 14, 30, tzinfo=timezone.utc)
END_TIME = datetime(2026, 4, 13, 20, 30, tzinfo=timezone.utc)


#USER_PROFILES = {"benchmark": {"name": "benchmark", "start_time": START_TIME, "risk_tolerance": 1.0}}
USER_PROFILES = {}

for arc_name in ARCHETYPES.keys():
    USER_PROFILES.update(generate_users(arc_name, 1))

USERS = {name: name for name in USER_PROFILES.keys()}






