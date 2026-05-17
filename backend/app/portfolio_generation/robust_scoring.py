from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.spatial import cKDTree


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_PATH = BASE_DIR / "archetype_results" / "results.json"
DEFAULT_OUTPUT_PATH = BASE_DIR / "archetype_results" / "results_with_robust_scores.json"


FEATURE_COLUMNS = (
    "short_term_weight",
    "medium_term_weight",
    "long_term_weight",
    "metric_relative_technical_strength",
    "metric_relative_fundamental_support",
    "metric_relative_valuation_sustainability",
    "metric_relative_structural_risk",
    "metric_relative_conviction",
    "metric_relative_asymmetry_profile",
    "min_exposure",
    "aggression_slope",
    "exposure_baseline",
    "rebalance_threshold",
    "softmax_temp",
)


@dataclass(frozen=True)
class FeatureBounds:
    low: float
    high: float


FEATURE_BOUNDS = {
    "short_term_weight": FeatureBounds(0.0, 1.0),
    "medium_term_weight": FeatureBounds(0.0, 1.0),
    "long_term_weight": FeatureBounds(0.0, 1.0),
    "metric_relative_technical_strength": FeatureBounds(0.0, 1.0),
    "metric_relative_fundamental_support": FeatureBounds(0.0, 1.0),
    "metric_relative_valuation_sustainability": FeatureBounds(0.0, 1.0),
    "metric_relative_structural_risk": FeatureBounds(0.0, 1.0),
    "metric_relative_conviction": FeatureBounds(0.0, 1.0),
    "metric_relative_asymmetry_profile": FeatureBounds(0.0, 1.0),
    "min_exposure": FeatureBounds(0.10, 1.0),
    "aggression_slope": FeatureBounds(0.0, 1.0),
    "exposure_baseline": FeatureBounds(3.0, 7.0),
    "rebalance_threshold": FeatureBounds(0.0, 0.20),
    "softmax_temp": FeatureBounds(0.01, 2.0),
}


def load_results(path: Path = DEFAULT_RESULTS_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("results JSON must contain a list of rows")

    return data


def _flatten_row(row: dict) -> dict[str, float]:
    metric_weights = row["metric_weights"]
    return {
        "short_term_weight": float(row["short_term_weight"]),
        "medium_term_weight": float(row["medium_term_weight"]),
        "long_term_weight": float(row["long_term_weight"]),
        "metric_relative_technical_strength": float(metric_weights["relative_technical_strength"]),
        "metric_relative_fundamental_support": float(metric_weights["relative_fundamental_support"]),
        "metric_relative_valuation_sustainability": float(metric_weights["relative_valuation_sustainability"]),
        "metric_relative_structural_risk": float(metric_weights["relative_structural_risk"]),
        "metric_relative_conviction": float(metric_weights["relative_conviction"]),
        "metric_relative_asymmetry_profile": float(metric_weights["relative_asymmetry_profile"]),
        "min_exposure": float(row["min_exposure"]),
        "aggression_slope": float(row["aggression_slope"]),
        "exposure_baseline": float(row["exposure_baseline"]),
        "rebalance_threshold": float(row["rebalance_threshold"]),
        "softmax_temp": float(row["softmax_temp"]),
    }


def _rows_to_matrix(rows: Iterable[dict]) -> np.ndarray:
    flat_rows = [_flatten_row(row) for row in rows]
    matrix = np.array(
        [[flat_row[column] for column in FEATURE_COLUMNS] for flat_row in flat_rows],
        dtype=np.float64,
    )
    return matrix


def _scale_to_unit_box(matrix: np.ndarray) -> np.ndarray:
    lows = np.array([FEATURE_BOUNDS[column].low for column in FEATURE_COLUMNS], dtype=np.float64)
    highs = np.array([FEATURE_BOUNDS[column].high for column in FEATURE_COLUMNS], dtype=np.float64)
    widths = highs - lows
    return (matrix - lows) / widths


def _resolve_hit_threshold(rows: list[dict], fallback: float | None) -> float:
    benchmark_rows = [
        row for row in rows
        if row.get("archetype_key") == "benchmark" or row.get("name") == "benchmark"
    ]
    if benchmark_rows:
        return float(benchmark_rows[0]["change_ratio"])

    if fallback is None:
        raise ValueError(
            "No benchmark row found. Pass hit_threshold explicitly, "
            "for example the benchmark change_ratio from a separate run."
        )

    return float(fallback)


def add_robust_scores(
    rows: list[dict],
    *,
    k_neighbors: int = 128,
    hit_threshold: float | None = None,
) -> list[dict]:
    """
    Add local robust metrics for each sampled point.

    The point itself is excluded from its neighborhood, so metrics describe the
    surrounding region rather than simply repeating the point's own result.
    """
    if len(rows) <= k_neighbors:
        raise ValueError("Need more rows than k_neighbors")

    threshold = _resolve_hit_threshold(rows, hit_threshold)
    feature_matrix = _rows_to_matrix(rows)
    scaled_matrix = _scale_to_unit_box(feature_matrix)
    outcomes = np.array([float(row["change_ratio"]) for row in rows], dtype=np.float64)

    tree = cKDTree(scaled_matrix)
    _, neighbor_indices = tree.query(scaled_matrix, k=k_neighbors + 1)
    neighbor_indices = neighbor_indices[:, 1:]
    neighbor_outcomes = outcomes[neighbor_indices]

    local_mean = neighbor_outcomes.mean(axis=1)
    local_std = neighbor_outcomes.std(axis=1)
    local_median = np.median(neighbor_outcomes, axis=1)
    local_q10 = np.quantile(neighbor_outcomes, 0.10, axis=1)
    local_q90 = np.quantile(neighbor_outcomes, 0.90, axis=1)
    local_hit_rate = (neighbor_outcomes >= threshold).mean(axis=1)
    robust_scores = build_robust_score(
        local_mean=local_mean,
        local_std=local_std,
        local_median=local_median,
        local_q10=local_q10,
        local_q90=local_q90,
        local_hit_rate=local_hit_rate,
    )

    scored_rows = []
    for index, row in enumerate(rows):
        scored_row = dict(row)
        scored_row["robust_metrics"] = {
            "neighbor_count": int(k_neighbors),
            "hit_threshold": round(float(threshold), 6),
            "local_mean": round(float(local_mean[index]), 6),
            "local_std": round(float(local_std[index]), 6),
            "local_median": round(float(local_median[index]), 6),
            "local_q10": round(float(local_q10[index]), 6),
            "local_q90": round(float(local_q90[index]), 6),
            "local_hit_rate": round(float(local_hit_rate[index]), 6),
        }
        scored_row["robust_score"] = round(float(robust_scores[index]), 6)
        scored_rows.append(scored_row)

    return scored_rows


def build_robust_score(
    *,
    local_mean: np.ndarray,
    local_std: np.ndarray,
    local_median: np.ndarray,
    local_q10: np.ndarray,
    local_q90: np.ndarray,
    local_hit_rate: np.ndarray,
) -> np.ndarray:
    """
    Central place for changing the ranking formula used before GMM.

    Current default:
        robust_score = local_mean
    """
    return local_mean


def save_results(rows: list[dict], path: Path = DEFAULT_OUTPUT_PATH) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    rows = load_results()
    scored_rows = add_robust_scores(
        rows,
        k_neighbors=128,
        # If your current results file has no benchmark row, set it here manually.
        # Example: hit_threshold=0.2445
        hit_threshold=0.2445,
    )
    save_results(scored_rows)
    print(f"Saved {len(scored_rows)} rows to {DEFAULT_OUTPUT_PATH}")
