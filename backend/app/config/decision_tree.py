import json
from typing import List

import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture


METRIC_MAP = {
    "tech": "relative_technical_strength",
    "fund": "relative_fundamental_support",
    "val": "relative_valuation_sustainability",
    "risk": "relative_structural_risk",
    "conv": "relative_conviction",
    "asym": "relative_asymmetry_profile"
}


# =========================================================
# LOAD JSON
# =========================================================

def load_archetypes_json(file_path: str) -> List[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON musi zawierać listę obiektów")

    return data


# =========================================================
# FLATTEN
# =========================================================

def flatten_data(data: List[dict]) -> pd.DataFrame:
    rows = []

    for item in data:
        row = {
            "short_term_weight": float(item["short_term_weight"]),
            "medium_term_weight": float(item["medium_term_weight"]),
            "long_term_weight": float(item["long_term_weight"]),
            "risk_tolerance": float(item["risk_tolerance"]),
            "rebalance_threshold": float(item["rebalance_threshold"]),
            "min_score_threshold": float(item["min_score_threshold"]),
            "softmax_temp": float(item["softmax_temp"]),
            "change_ratio": float(item["change_ratio"])
        }

        for k, v in item["metric_weights"].items():
            row[f"metric_{k}"] = float(v)

        rows.append(row)

    return pd.DataFrame(rows)


# =========================================================
# BUILD SCORE
# =========================================================

def build_score(df: pd.DataFrame) -> pd.Series:
    """
    Możesz tutaj później dodać:
    - sharpe
    - stability
    - drawdown
    - winrate

    Na razie używamy samego change_ratio
    """

    return df["change_ratio"]


# =========================================================
# MAIN GMM ARCHETYPES
# =========================================================

def generate_gmm_archetypes(
    data: List[dict],
    n_clusters: int = 4,
    top_percentile: float = 0.90,
    random_state: int = 42
):

    # -----------------------------------------------------
    # 1. DataFrame
    # -----------------------------------------------------

    df = flatten_data(data)

    # -----------------------------------------------------
    # 2. Build score
    # -----------------------------------------------------

    df["score"] = build_score(df)

    # -----------------------------------------------------
    # 3. Select TOP strategies
    # -----------------------------------------------------

    threshold = df["score"].quantile(top_percentile)

    top_df = df[df["score"] >= threshold].copy()

    if len(top_df) < n_clusters:
        raise ValueError(
            f"Za mało danych po filtracji TOP {top_percentile * 100:.0f}%"
        )

    # -----------------------------------------------------
    # 4. Features
    # -----------------------------------------------------

    features = [
        c for c in top_df.columns
        if c not in ["change_ratio", "score"]
    ]

    X = top_df[features]

    # -----------------------------------------------------
    # 5. Normalize
    # -----------------------------------------------------

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    # -----------------------------------------------------
    # 6. Gaussian Mixture Model
    # -----------------------------------------------------

    gmm = GaussianMixture(
        n_components=n_clusters,
        covariance_type="full",
        random_state=random_state,
        n_init=10
    )

    gmm.fit(X_scaled)

    # -----------------------------------------------------
    # 7. Cluster assign
    # -----------------------------------------------------

    top_df["cluster"] = gmm.predict(X_scaled)

    # probability membership
    probabilities = gmm.predict_proba(X_scaled)

    # confidence
    top_df["cluster_confidence"] = probabilities.max(axis=1)

    # -----------------------------------------------------
    # 8. Archetypes
    # -----------------------------------------------------

    archetypes = {}

    cluster_performance = (
        top_df
        .groupby("cluster")["change_ratio"]
        .mean()
        .sort_values(ascending=False)
    )

    sorted_clusters = cluster_performance.index.tolist()

    for rank, cluster_id in enumerate(sorted_clusters):

        cluster_data = top_df[top_df["cluster"] == cluster_id]

        archetype_name = f"top_strategy_{rank + 1}"

        params = {}

        for col in features:

            values = cluster_data[col]

            params[col] = {
                "median": float(values.median()),
                "mean": float(values.mean()),
                "std": float(values.std()),

                "q10": float(values.quantile(0.10)),
                "q25": float(values.quantile(0.25)),
                "q75": float(values.quantile(0.75)),
                "q90": float(values.quantile(0.90))
            }

        # ---------------------------------------------
        # metric weights cleaner structure
        # ---------------------------------------------

        metric_weights = {}

        for json_key, dto_key in METRIC_MAP.items():

            col = "metric_" + dto_key

            values = cluster_data[col]

            metric_weights[json_key] = {
                "median": float(values.median()),
                "q25": float(values.quantile(0.25)),
                "q75": float(values.quantile(0.75))
            }

        archetypes[archetype_name] = {

            "cluster_id": int(cluster_id),

            "avg_change_ratio": float(
                cluster_data["change_ratio"].mean()
            ),

            "median_change_ratio": float(
                cluster_data["change_ratio"].median()
            ),

            "cluster_size": int(len(cluster_data)),

            "avg_confidence": float(
                cluster_data["cluster_confidence"].mean()
            ),

            "time_weights": {
                "short": params["short_term_weight"],
                "medium": params["medium_term_weight"],
                "long": params["long_term_weight"]
            },

            "metric_weights": metric_weights,

            "risk_tolerance": params["risk_tolerance"],

            "rebalance_threshold": params["rebalance_threshold"],

            "min_score_threshold": params["min_score_threshold"],

            "softmax_temp": params["softmax_temp"]
        }

    return archetypes


# =========================================================
# SAVE JSON
# =========================================================

def save_json(data: dict, filename: str):

    text = json.dumps(
        data,
        indent=4,
        ensure_ascii=False
    )

    # compact lists
    import re

    text = re.sub(
        r"\[\s+([^\[\]]+?)\s+\]",
        lambda m: "[" + " ".join(m.group(1).split()) + "]",
        text
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    data = load_archetypes_json("1000rand.json")

    archetypes = generate_gmm_archetypes(
        data=data,

        # liczba archetypów
        n_clusters=4,

        # bierzemy top 10%
        top_percentile=0.90,

        random_state=42
    )

    save_json(
        archetypes,
        "1000_archetypes_gmm.json"
    )

    print("DONE")