import random
import numpy as np

random.seed(42)


def generate_users(archetype_key, count, archetypes):
    if archetype_key == "benchmark":
        return {"benchmark": {"name": "benchmark"}}

    generated_users = {}
    arc = archetypes[archetype_key]

    for i in range(1, count + 1):
        if archetype_key == "random":

            # --- METODA DLA ARCHEPROTYPU RANDOM ---
            # Losujemy wagi tak, aby każdy układ (nawet skrajny) był równie prawdopodobny

            # 1. Time Weights (3 parametry)
            tw_values = sorted([random.random() for _ in range(2)])
            tw_pts = [0] + tw_values + [1]
            # Obliczamy różnice między punktami (zawsze sumują się do 1)
            tw_list = [round(tw_pts[j + 1] - tw_pts[j], 3) for j in range(3)]
            tw = {
                "short": tw_list[0],
                "medium": tw_list[1],
                "long": tw_list[2]
            }

            # 2. Metric Weights (6 parametrów)
            mw_values = sorted([random.random() for _ in range(5)])
            mw_pts = [0] + mw_values + [1]
            mw_list = [round(mw_pts[j + 1] - mw_pts[j], 3) for j in range(6)]

            # Mapowanie na konkretne nazwy
            mw = {
                "relative_technical_strength": mw_list[0],
                "relative_fundamental_support": mw_list[1],
                "relative_valuation_sustainability": mw_list[2],
                "relative_structural_risk": mw_list[3],
                "relative_conviction": mw_list[4],
                "relative_asymmetry_profile": mw_list[5],
            }

            print(tw)
            print(mw)
        else:
            # --- STANDARDOWE LOSOWANIE DLA INNYCH ARCHETYPÓW ---
            tw_raw = {k: random.uniform(v[0], v[1]) for k, v in arc["time_weights"].items()}
            tw_sum = sum(tw_raw.values())
            tw = {k: round(v / tw_sum, 3) for k, v in tw_raw.items()}

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

        # Reszta parametrów bez zmian
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