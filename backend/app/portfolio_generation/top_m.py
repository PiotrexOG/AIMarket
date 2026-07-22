from __future__ import annotations

import math
from typing import Iterable


TOP_M_MIN_SHARE = 1.0 / 18.0
TOP_M_MAX_SHARE = 1.0
INVESTMENT_TIME_MIN_DAYS = 100
INVESTMENT_TIME_MAX_DAYS = 300
REBALANCE_TIME_MIN_SHARE = 0.20
REBALANCE_TIME_MAX_SHARE = 0.60
RELATIVE_SCORE_PERCENTILE_CHANGE_THRESHOLD = -0.15


def clamp_top_m_share(value: float) -> float:
    return min(TOP_M_MAX_SHARE, max(TOP_M_MIN_SHARE, float(value)))


def calculate_average_score(relative_scores: dict) -> float:
    values = [float(value) for value in relative_scores.values()]
    if not values:
        return 0.0
    return round(math.fsum(values) / len(values), 10)


def build_profile(
    archetype_key: str,
    *,
    top_m_share: float,
    investment_time_days: float = INVESTMENT_TIME_MAX_DAYS,
    rebalance_time_share: float = REBALANCE_TIME_MIN_SHARE,
    name: str | None = None,
    profile_id: str | None = None,
) -> dict:
    return {
        "name": name or archetype_key,
        "id": profile_id,
        "archetype_key": archetype_key,
        "top_m_share": round(float(top_m_share), 3),
        "investment_time_days": int(round(float(investment_time_days))),
        "rebalance_time_share": round(float(rebalance_time_share), 4),
    }


def fractional_top_m_weights(
    tickers_by_score: Iterable[str],
    top_m_share: float,
) -> dict[str, float]:
    tickers = list(tickers_by_score)
    if not tickers:
        return {}

    target_count = len(tickers) * clamp_top_m_share(top_m_share)
    full_count = int(math.floor(target_count))
    fractional_count = target_count - full_count

    raw_weights: dict[str, float] = {}
    for index, ticker in enumerate(tickers):
        rank = index + 1
        if rank <= full_count:
            raw_weights[ticker] = 1.0
        elif rank == full_count + 1:
            raw_weights[ticker] = fractional_count
        else:
            raw_weights[ticker] = 0.0

    selected_count = math.fsum(raw_weights.values())
    if selected_count <= 0:
        return {}

    return {
        ticker: weight / selected_count
        for ticker, weight in raw_weights.items()
        if weight > 0.0
    }
