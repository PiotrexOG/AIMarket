from datetime import datetime, timezone

from app.decisionMakers.LLMGEMINIDM import LLMGEMINIDM
from app.decisionMakers.randomDecisionMaker import RandomDecisionMaker

REAL_TIME = False
LOCALLY = True

#TICKERS = ["AAPL", "TSLA", "NVDA"]
TICKERS = ["AAPL"]

DEBUG_RESET = True

STARTING_CASH = 10000.0
USERS = {
    "Piotr": RandomDecisionMaker,
    #"Adam": RandomDecisionMaker
    #"Jerzy": LLMGEMINIDM,
}

# ZERO_TIME = datetime(2024, 2, 1, 13, 30, tzinfo=timezone.utc)
# START_TIME = datetime(2025, 1, 1, 13, 30, tzinfo=timezone.utc)
# END_TIME = datetime(2025, 12, 28, 20, 30, tzinfo=timezone.utc)

ZERO_TIME = datetime(2025, 2, 1, 13, 30, tzinfo=timezone.utc)
START_TIME = datetime(2025, 2, 10, 13, 30, tzinfo=timezone.utc)
END_TIME = datetime(2025, 2, 28, 20, 30, tzinfo=timezone.utc)

