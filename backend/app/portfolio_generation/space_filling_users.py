from __future__ import annotations

from typing import Mapping

import numpy as np

from app.portfolio_generation.top_m import (
    INVESTMENT_TIME_MAX_DAYS,
    INVESTMENT_TIME_MIN_DAYS,
    REBALANCE_TIME_MAX_SHARE,
    REBALANCE_TIME_MIN_SHARE,
    TOP_M_MAX_SHARE,
    TOP_M_MIN_SHARE,
    build_profile,
)


def _top_m_range(archetypes: Mapping, archetype_key: str) -> tuple[float, float]:
    configured = archetypes.get(archetype_key, {}).get(
        "top_m_share",
        (TOP_M_MIN_SHARE, TOP_M_MAX_SHARE),
    )
    return float(configured[0]), float(configured[1])


def _investment_time_range(archetypes: Mapping, archetype_key: str) -> tuple[int, int]:
    configured = archetypes.get(archetype_key, {}).get(
        "investment_time_days",
        (INVESTMENT_TIME_MIN_DAYS, INVESTMENT_TIME_MAX_DAYS),
    )
    return int(configured[0]), int(configured[1])


def _rebalance_time_share_range(archetypes: Mapping, archetype_key: str) -> tuple[float, float]:
    configured = archetypes.get(archetype_key, {}).get(
        "rebalance_time_share",
        (REBALANCE_TIME_MIN_SHARE, REBALANCE_TIME_MAX_SHARE),
    )
    return float(configured[0]), float(configured[1])


def generate_space_filling_users(
    archetype_key: str,
    count: int,
    archetypes: Mapping,
    seed: int | None = 42,
) -> dict[str, dict]:
    if archetype_key == "benchmark":
        return {
            "benchmark": build_profile(
                "benchmark",
                top_m_share=TOP_M_MAX_SHARE,
                investment_time_days=INVESTMENT_TIME_MAX_DAYS,
                rebalance_time_share=REBALANCE_TIME_MIN_SHARE,
                name="benchmark",
                profile_id="0",
            )
        }

    if archetype_key != "random":
        raise ValueError(f"Unsupported archetype: {archetype_key}")

    if count <= 0:
        raise ValueError("count must be greater than zero")

    low, high = _top_m_range(archetypes, archetype_key)
    investment_low, investment_high = _investment_time_range(archetypes, archetype_key)
    rebalance_low, rebalance_high = _rebalance_time_share_range(archetypes, archetype_key)
    rng = np.random.default_rng(seed)
    top_m_shares = rng.uniform(low, high, size=count)
    investment_days = rng.integers(investment_low, investment_high + 1, size=count)
    rebalance_time_shares = rng.uniform(rebalance_low, rebalance_high, size=count)

    generated_users: dict[str, dict] = {}
    for index, (top_m_share, investment_time_days, rebalance_time_share) in enumerate(
        zip(top_m_shares, investment_days, rebalance_time_shares),
        start=1,
    ):
        user_id = f"random_{index:06d}"
        generated_users[user_id] = build_profile(
            "random",
            top_m_share=float(top_m_share),
            investment_time_days=int(investment_time_days),
            rebalance_time_share=float(rebalance_time_share),
            name=user_id,
            profile_id=str(index),
        )

    return generated_users
