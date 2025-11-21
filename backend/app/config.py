from datetime import datetime, timezone

from app.decisionMakers.LLMGEMINIDM import LLMGEMINIDM
from app.decisionMakers.randomDecisionMaker import RandomDecisionMaker

REAL_TIME = False
LOCALLY = True

TICKERS = ["AAPL", "TSLA", "NVDA"]

DEBUG_RESET = True

STARTING_CASH = 10000.0
USERS = {
    "Piotr": RandomDecisionMaker,
    "Adam": RandomDecisionMaker,
    "Jerzy": LLMGEMINIDM,
}

ZERO_TIME = datetime(2023, 12, 1, 13, 30, tzinfo=timezone.utc)
START_TIME = datetime(2024, 10, 1, 13, 30, tzinfo=timezone.utc)
END_TIME = datetime(2025, 10, 1, 20, 30, tzinfo=timezone.utc)

