import random

from app.portfolio_generation.top_m import (
    INVESTMENT_TIME_MAX_DAYS,
    INVESTMENT_TIME_MIN_DAYS,
    REBALANCE_TIME_MAX_SHARE,
    REBALANCE_TIME_MIN_SHARE,
    TOP_M_MAX_SHARE,
    TOP_M_MIN_SHARE,
    build_profile,
    sample_investment_time_days,
    sample_rebalance_time_share,
    sample_top_m_share,
)


random.seed(42)


def _top_m_range(archetypes: dict, archetype_key: str) -> tuple[float, float]:
    configured = archetypes.get(archetype_key, {}).get(
        "top_m_share",
        (TOP_M_MIN_SHARE, TOP_M_MAX_SHARE),
    )
    return float(configured[0]), float(configured[1])


def _investment_time_range(archetypes: dict, archetype_key: str) -> tuple[int, int]:
    configured = archetypes.get(archetype_key, {}).get(
        "investment_time_days",
        (INVESTMENT_TIME_MIN_DAYS, INVESTMENT_TIME_MAX_DAYS),
    )
    return int(configured[0]), int(configured[1])


def _rebalance_time_share_range(archetypes: dict, archetype_key: str) -> tuple[float, float]:
    configured = archetypes.get(archetype_key, {}).get(
        "rebalance_time_share",
        (REBALANCE_TIME_MIN_SHARE, REBALANCE_TIME_MAX_SHARE),
    )
    return float(configured[0]), float(configured[1])


def generate_users(archetype_key, count, archetypes):
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

    low, high = _top_m_range(archetypes, archetype_key)
    investment_low, investment_high = _investment_time_range(archetypes, archetype_key)
    rebalance_low, rebalance_high = _rebalance_time_share_range(archetypes, archetype_key)
    generated_users = {}

    for index in range(1, count + 1):
        top_m_share = sample_top_m_share()
        top_m_share = min(high, max(low, top_m_share))
        investment_days = sample_investment_time_days()
        investment_days = min(investment_high, max(investment_low, investment_days))
        rebalance_time_share = sample_rebalance_time_share()
        rebalance_time_share = min(
            rebalance_high,
            max(rebalance_low, rebalance_time_share),
        )
        user_id = f"random_{index:06d}"
        generated_users[user_id] = build_profile(
            "random",
            top_m_share=top_m_share,
            investment_time_days=investment_days,
            rebalance_time_share=rebalance_time_share,
            name=user_id,
            profile_id=str(index),
        )

    return generated_users
