from datetime import datetime, timezone

from sqlalchemy import false

from app.decisionMakers.tickerMaster.GEMINI_MASTER import GEMINI_MASTER
from app.decisionMakers.randomDecisionMaker import RandomDecisionMaker

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
END_TIME = datetime(2026, 3, 12, 20, 30, tzinfo=timezone.utc)


USER_PROFILES = {
    "benchmark": {
        "name": "benchmark",
        "start_time": START_TIME,
        "risk_tolerance": 1.0
    },
    "conservative_long_term": {
        "time_weights": {
            "short_term_14d": 0.05,
            "medium_term_50d": 0.25,
            "long_term_200d": 0.7
        },

        "metric_weights": {
            "relative_fundamental_support": 0.5,
            "relative_structural_risk": 0.4,
            "relative_valuation_sustainability": 0.3,
            "relative_technical_strength": 0.1
        },

        "risk_tolerance": 0.4,
        "rebalance_threshold": 0.04,

        "min_score_threshold": 5.5,  # 🔥 bardzo selektywny
        "softmax_temp": 1.5  # bardziej równomierny
    },
    "aggressive_trader": {
        "time_weights": {
            "short_term_14d": 0.8,
            "medium_term_50d": 0.15,
            "long_term_200d": 0.05
        },

        "metric_weights": {
            "relative_technical_strength": 0.6,
            "relative_asymmetry_profile": 0.4,
            "relative_conviction": 0.3
        },

        "risk_tolerance": 1.0,
        "rebalance_threshold": 0.005,

        "min_score_threshold": 3.5,  # 🔥 bierze prawie wszystko
        "softmax_temp": 0.5  # 🔥 koncentracja
    },
    "moderate_midterm": {
        "time_weights": {
            "short_term_14d": 0.25,
            "medium_term_50d": 0.5,
            "long_term_200d": 0.25
        },

        "metric_weights": {
            "relative_fundamental_support": 0.3,
            "relative_structural_risk": 0.25,
            "relative_valuation_sustainability": 0.2,
            "relative_technical_strength": 0.25,
        },

        "risk_tolerance": 0.7,
        "rebalance_threshold": 0.02,

        "min_score_threshold": 4.5,
        "softmax_temp": 1.0
    }
}

USERS = {
    "benchmark": "benchmark",
    "moderate_midterm": "moderate_midterm",
    "conservative_long_term": "conservative_long_term",
    "aggressive_trader": "aggressive_trader"
}






