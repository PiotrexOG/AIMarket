import random

random.seed(42)


def generate_users(archetype_key, count, archetypes):
    # --- 1. OBSŁUGA BENCHMARKU ---
    if archetype_key == "benchmark":
        return {"benchmark": {
            "name": "benchmark",
            "id": "0",
            "archetype_key": "benchmark",
            "time_weights": {"short_term_14d": 0, "medium_term_50d": 0, "long_term_200d": 0},
            "metric_weights": {
                "relative_technical_strength": 0,
                "relative_fundamental_support": 0,
                "relative_valuation_sustainability": 0,
                "relative_structural_safety": 0,
                "relative_conviction": 0,
                "relative_asymmetry_profile": 0,
            },
            "min_exposure": 0,
            "aggression_slope": 0,
            "exposure_baseline": 0,
            "rebalance_threshold": 0,
            "softmax_temp": 0
        }}

    generated_users = {}
    arc = archetypes[archetype_key]

    for i in range(1, count + 1):
        # Pomocnicza funkcja: p to teraz tuple (min, max)
        def sample(p):
            return random.uniform(p[0], p[1])

        # --- 2. WAGI CZASOWE (Time Weights) ---
        # Losujemy z tupli (min, max)
        tw_raw = {k: max(0.0, sample(v)) for k, v in arc["time_weights"].items()}
        tw_sum = sum(tw_raw.values()) or 1.0
        tw = {k: round(v / tw_sum, 3) for k, v in tw_raw.items()}

        # --- 3. WAGI METRYK (Metric Weights) ---
        mw_raw = {k: max(0.0, sample(v)) for k, v in arc["metric_weights"].items()}
        mw_sum = sum(mw_raw.values()) or 1.0

        mw = {
            "relative_technical_strength": round(mw_raw["tech"] / mw_sum, 3),
            "relative_fundamental_support": round(mw_raw["fund"] / mw_sum, 3),
            "relative_valuation_sustainability": round(mw_raw["val"] / mw_sum, 3),
            "relative_structural_safety": round(mw_raw["safe"] / mw_sum, 3),
            "relative_conviction": round(mw_raw["conv"] / mw_sum, 3),
            "relative_asymmetry_profile": round(mw_raw["asym"] / mw_sum, 3),
        }

        # --- 4. POZOSTAŁE PARAMETRY ---
        user_id = f"{archetype_key}_{i:02d}"
        generated_users[user_id] = {
            "archetype_key": archetype_key,
            "time_weights": {
                "short_term_14d": tw["short"],
                "medium_term_50d": tw["medium"],
                "long_term_200d": tw["long"]
            },
            "metric_weights": mw,
            "min_exposure": round(max(0.0, sample(arc["min_exposure"])), 2),
            "aggression_slope": round(max(0.0, sample(arc["aggression_slope"])), 2),
            "exposure_baseline": round(max(0.0, sample(arc["exposure_baseline"])), 2),
            "rebalance_threshold": round(max(0.0, sample(arc["rebalance_threshold"])), 4),
            "softmax_temp": round(max(0.01, sample(arc["temp"])), 2)
        }

    return generated_users