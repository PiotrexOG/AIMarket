from __future__ import annotations

import math
import random
from typing import Iterable


TOP_M_MIN_SHARE = 1.0 / 18.0
TOP_M_MAX_SHARE = 1.0

FIXED_METRIC_WEIGHTS = {
    "relative_technical_strength": 1.0 / 6.0,
    "relative_fundamental_support": 1.0 / 6.0,
    "relative_valuation_sustainability": 1.0 / 6.0,
    "relative_structural_safety": 1.0 / 6.0,
    "relative_conviction": 1.0 / 6.0,
    "relative_asymmetry_profile": 1.0 / 6.0,
}


def clamp_top_m_share(value: float) -> float:
    return min(TOP_M_MAX_SHARE, max(TOP_M_MIN_SHARE, float(value)))


def sample_top_m_share(rng: random.Random | None = None) -> float:
    generator = rng or random
    return generator.uniform(TOP_M_MIN_SHARE, TOP_M_MAX_SHARE)


def build_profile(
    archetype_key: str,
    *,
    top_m_share: float,
    name: str | None = None,
    profile_id: str | None = None,
) -> dict:
    return {
        "name": name or archetype_key,
        "id": profile_id,
        "archetype_key": archetype_key,
        "top_m_share": round(clamp_top_m_share(top_m_share), 10),
        "metric_weights": dict(FIXED_METRIC_WEIGHTS),
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
