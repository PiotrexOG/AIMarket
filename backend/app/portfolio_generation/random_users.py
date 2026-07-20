import random

from app.portfolio_generation.top_m import (
    TOP_M_MAX_SHARE,
    TOP_M_MIN_SHARE,
    build_profile,
    sample_top_m_share,
)


random.seed(42)


def _top_m_range(archetypes: dict, archetype_key: str) -> tuple[float, float]:
    configured = archetypes.get(archetype_key, {}).get(
        "top_m_share",
        (TOP_M_MIN_SHARE, TOP_M_MAX_SHARE),
    )
    return float(configured[0]), float(configured[1])


def generate_users(archetype_key, count, archetypes):
    if archetype_key == "benchmark":
        return {
            "benchmark": build_profile(
                "benchmark",
                top_m_share=TOP_M_MAX_SHARE,
                name="benchmark",
                profile_id="0",
            )
        }

    if archetype_key != "random":
        raise ValueError(f"Unsupported archetype: {archetype_key}")

    low, high = _top_m_range(archetypes, archetype_key)
    generated_users = {}

    for index in range(1, count + 1):
        top_m_share = sample_top_m_share()
        top_m_share = min(high, max(low, top_m_share))
        user_id = f"random_{index:06d}"
        generated_users[user_id] = build_profile(
            "random",
            top_m_share=top_m_share,
            name=user_id,
            profile_id=str(index),
        )

    return generated_users
