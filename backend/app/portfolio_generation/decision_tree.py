from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = BASE_DIR / "archetype_results" / "results_with_robust_scores.json"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "archetype_blueprints" / "archetypes_gmm.json"


METRIC_TO_SHORT = {
    "relative_technical_strength": "tech",
    "relative_fundamental_support": "fund",
    "relative_valuation_sustainability": "val",
    "relative_structural_safety": "safe",
    "relative_conviction": "conv",
    "relative_asymmetry_profile": "asym",
}


FEATURE_COLUMNS = [
    "short_term_weight",
    "medium_term_weight",
    "long_term_weight",
    "metric_relative_technical_strength",
    "metric_relative_fundamental_support",
    "metric_relative_valuation_sustainability",
    "metric_relative_structural_safety",
    "metric_relative_conviction",
    "metric_relative_asymmetry_profile",
    "min_exposure",
    "aggression_slope",
    "exposure_baseline",
    "rebalance_threshold",
    "softmax_temp",
]


def load_json(path: Path = DEFAULT_INPUT_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input JSON must contain a list of rows")

    return data


def flatten_rows(rows: Iterable[dict]) -> pd.DataFrame:
    flat_rows = []
    for row in rows:
        metrics = row["metric_weights"]
        robust = row.get("robust_metrics", {})

        flat_rows.append(
            {
                "short_term_weight": float(row["short_term_weight"]),
                "medium_term_weight": float(row["medium_term_weight"]),
                "long_term_weight": float(row["long_term_weight"]),
                "metric_relative_technical_strength": float(metrics["relative_technical_strength"]),
                "metric_relative_fundamental_support": float(metrics["relative_fundamental_support"]),
                "metric_relative_valuation_sustainability": float(metrics["relative_valuation_sustainability"]),
                "metric_relative_structural_safety": float(metrics["relative_structural_safety"]),
                "metric_relative_conviction": float(metrics["relative_conviction"]),
                "metric_relative_asymmetry_profile": float(metrics["relative_asymmetry_profile"]),
                "min_exposure": float(row["min_exposure"]),
                "aggression_slope": float(row["aggression_slope"]),
                "exposure_baseline": float(row["exposure_baseline"]),
                "rebalance_threshold": float(row["rebalance_threshold"]),
                "softmax_temp": float(row["softmax_temp"]),
                "change_ratio": float(row["change_ratio"]),
                "local_mean": float(robust.get("local_mean", np.nan)),
                "local_std": float(robust.get("local_std", np.nan)),
                "local_median": float(robust.get("local_median", np.nan)),
                "local_q10": float(robust.get("local_q10", np.nan)),
                "local_q90": float(robust.get("local_q90", np.nan)),
                "local_hit_rate": float(robust.get("local_hit_rate", np.nan)),
                "robust_score": float(row["robust_score"]),
            }
        )

    df = pd.DataFrame(flat_rows)
    if df["robust_score"].isna().any():
        raise ValueError("Every row must contain robust_score before running GMM")
    return df


def _summary(values: pd.Series) -> dict[str, float]:
    return {
        "mean": round(float(values.mean()), 6),
        "spread": round(float((values.quantile(0.75) - values.quantile(0.25)) / 2), 6),
        "median": round(float(values.median()), 6),
        "q25": round(float(values.quantile(0.25)), 6),
        "q75": round(float(values.quantile(0.75)), 6),
        "q10": round(float(values.quantile(0.10)), 6),
        "q90": round(float(values.quantile(0.90)), 6),
    }


def _mean_spread_only(values: pd.Series) -> dict[str, float]:
    summary = _summary(values)
    return {
        "mean": summary["mean"],
        "spread": summary["spread"],
    }


def _prepare_top_df(
    rows: list[dict],
    *,
    top_percentile: float = 0.95,
) -> tuple[pd.DataFrame, np.ndarray]:
    df = flatten_rows(rows)

    threshold = df["robust_score"].quantile(top_percentile)
    top_df = df[df["robust_score"] >= threshold].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(top_df[FEATURE_COLUMNS])
    return top_df, X_scaled


def select_cluster_count_by_bic(
    rows: list[dict],
    *,
    top_percentile: float = 0.95,
    min_clusters: int = 2,
    max_clusters: int = 10,
    random_state: int = 42,
) -> tuple[int, dict[int, float]]:
    top_df, X_scaled = _prepare_top_df(rows, top_percentile=top_percentile)
    if len(top_df) < min_clusters:
        raise ValueError(
            f"Too few rows after filtering top {top_percentile:.0%}; "
            f"got {len(top_df)} rows."
        )

    upper = min(max_clusters, len(top_df))
    bic_by_clusters: dict[int, float] = {}
    for n_clusters in range(min_clusters, upper + 1):
        gmm = GaussianMixture(
            n_components=n_clusters,
            covariance_type="full",
            random_state=random_state,
            n_init=10,
        )
        gmm.fit(X_scaled)
        bic_by_clusters[n_clusters] = float(gmm.bic(X_scaled))

    best_n_clusters = min(bic_by_clusters, key=bic_by_clusters.get)
    return best_n_clusters, bic_by_clusters


def generate_gmm_archetypes(
    rows: list[dict],
    *,
    n_clusters: int | None = None,
    top_percentile: float = 0.95,
    min_cluster_size: int = 25,
    random_state: int = 42,
    min_clusters: int = 2,
    max_clusters: int = 10,
) -> dict:
    top_df, X_scaled = _prepare_top_df(rows, top_percentile=top_percentile)

    bic_by_clusters = None
    if n_clusters is None:
        n_clusters, bic_by_clusters = select_cluster_count_by_bic(
            rows,
            top_percentile=top_percentile,
            min_clusters=min_clusters,
            max_clusters=max_clusters,
            random_state=random_state,
        )

    if len(top_df) < n_clusters:
        raise ValueError(
            f"Too few rows after filtering top {top_percentile:.0%}; "
            f"got {len(top_df)} rows for {n_clusters} clusters."
        )

    gmm = GaussianMixture(
        n_components=n_clusters,
        covariance_type="full",
        random_state=random_state,
        n_init=10,
    )
    gmm.fit(X_scaled)

    top_df["cluster"] = gmm.predict(X_scaled)
    top_df["cluster_confidence"] = gmm.predict_proba(X_scaled).max(axis=1)

    cluster_stats = (
        top_df.groupby("cluster")
        .agg(
            cluster_size=("cluster", "size"),
            avg_robust_score=("robust_score", "mean"),
            avg_local_mean=("local_mean", "mean"),
            avg_local_median=("local_median", "mean"),
            avg_local_q10=("local_q10", "mean"),
            avg_local_q90=("local_q90", "mean"),
            avg_local_std=("local_std", "mean"),
            avg_local_hit_rate=("local_hit_rate", "mean"),
        )
        .sort_values("avg_robust_score", ascending=False)
    )

    archetypes: dict[str, dict] = {}
    rank = 1
    for cluster_id, stats in cluster_stats.iterrows():
        cluster_df = top_df[top_df["cluster"] == cluster_id]
        if len(cluster_df) < min_cluster_size:
            continue

        archetype_name = f"gmm_archetype_{rank}"
        rank += 1

        metric_weights = {}
        for full_name, short_name in METRIC_TO_SHORT.items():
            metric_weights[short_name] = _mean_spread_only(
                cluster_df[f"metric_{full_name}"]
            )

        archetypes[archetype_name] = {
            "metadata": {
                "cluster_id": int(cluster_id),
                "selected_n_clusters": int(n_clusters),
                "bic_by_clusters": (
                    {str(k): round(v, 6) for k, v in bic_by_clusters.items()}
                    if bic_by_clusters is not None
                    else None
                ),
                "cluster_size": int(stats["cluster_size"]),
                "avg_robust_score": round(float(stats["avg_robust_score"]), 6),
                "avg_local_mean": round(float(stats["avg_local_mean"]), 6),
                "avg_local_median": round(float(stats["avg_local_median"]), 6),
                "avg_local_q10": round(float(stats["avg_local_q10"]), 6),
                "avg_local_q90": round(float(stats["avg_local_q90"]), 6),
                "avg_local_std": round(float(stats["avg_local_std"]), 6),
                "avg_local_hit_rate": round(float(stats["avg_local_hit_rate"]), 6),
                "avg_cluster_confidence": round(float(cluster_df["cluster_confidence"].mean()), 6),
            },
            "time_weights": {
                "short": _mean_spread_only(cluster_df["short_term_weight"]),
                "medium": _mean_spread_only(cluster_df["medium_term_weight"]),
                "long": _mean_spread_only(cluster_df["long_term_weight"]),
            },
            "metric_weights": metric_weights,
            "min_exposure": _mean_spread_only(cluster_df["min_exposure"]),
            "aggression_slope": _mean_spread_only(cluster_df["aggression_slope"]),
            "exposure_baseline": _mean_spread_only(cluster_df["exposure_baseline"]),
            "rebalance_threshold": _mean_spread_only(cluster_df["rebalance_threshold"]),
            "temp": _mean_spread_only(cluster_df["softmax_temp"]),
        }

    return archetypes


def save_json(data: dict, path: Path = DEFAULT_OUTPUT_PATH) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    rows = load_json()
    archetypes = generate_gmm_archetypes(
        rows,
        n_clusters=None,
        top_percentile=0.95,
        min_cluster_size=50,
        random_state=42,
    )
    save_json(archetypes)
    print(f"Saved {len(archetypes)} archetypes to {DEFAULT_OUTPUT_PATH}")
