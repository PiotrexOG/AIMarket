import random

from app.testy.archetypes import ARCHETYPES


def generate_users(archetype_key, count):

    if archetype_key == "benchmark":
        return {"benchmark": {"name": "benchmark"}}

    generated_users = {}
    arc = ARCHETYPES[archetype_key]

    for i in range(1, count + 1):
        # 1. Losowanie wag czasowych i normalizacja
        tw_raw = {k: random.uniform(v[0], v[1]) for k, v in arc["time_weights"].items()}
        tw_sum = sum(tw_raw.values())
        tw = {k: round(v / tw_sum, 3) for k, v in tw_raw.items()}

        # 2. Losowanie wag metryk i normalizacja
        mw_raw = {k: random.uniform(v[0], v[1]) for k, v in arc["metric_weights"].items()}
        mw_sum = sum(mw_raw.values())
        mw = {
            "relative_technical_strength": round(mw_raw["tech"] / mw_sum, 3),
            "relative_fundamental_support": round(mw_raw["fund"] / mw_sum, 3),
            "relative_valuation_sustainability": round(mw_raw["val"] / mw_sum, 3),
            "relative_structural_risk": round(mw_raw["risk"] / mw_sum, 3),
            "relative_conviction": round(mw_raw["conv"] / mw_sum, 3),
            "relative_asymmetry_profile": round(mw_raw["asym"] / mw_sum, 3),
        }

        user_id = f"{archetype_key}_{i:02d}"
        generated_users[user_id] = {
            "archetype_key": archetype_key,
            "time_weights": {
                "short_term_14d": tw["short"],
                "medium_term_50d": tw["medium"],
                "long_term_200d": tw["long"]
            },
            "metric_weights": mw,
            "risk_tolerance": round(random.uniform(*arc["risk_tolerance"]), 2),
            "rebalance_threshold": round(random.uniform(*arc["rebalance_range"]), 4),
            "min_score_threshold": round(random.uniform(*arc["min_score"]), 2),
            "softmax_temp": round(random.uniform(*arc["temp"]), 2)
        }
    return generated_users
