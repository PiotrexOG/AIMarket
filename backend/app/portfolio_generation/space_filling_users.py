from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Mapping

import numpy as np
from scipy.stats import qmc


TIME_KEYS = ("short", "medium", "long")
METRIC_KEYS = ("tech", "fund", "val", "risk", "conv", "asym")


@dataclass(frozen=True)
class ScalarBounds:
    min_exposure: tuple[float, float]
    aggression_slope: tuple[float, float]
    exposure_baseline: tuple[float, float]
    rebalance_threshold: tuple[float, float]
    softmax_temp: tuple[float, float]


def _as_range(value: tuple[float, float] | list[float]) -> tuple[float, float]:
    return float(value[0]), float(value[1])


def _sobol_points(count: int, dimensions: int, seed: int | None) -> np.ndarray:
    """
    Generate the first `count` Sobol points.

    Sobol has the best balance properties for powers of two. We therefore generate
    the next power of two and trim the tail when the caller requests another count.
    """
    if count <= 0:
        raise ValueError("count must be greater than zero")

    sampler = qmc.Sobol(d=dimensions, scramble=True, seed=seed)
    exponent = ceil(log2(count))
    return sampler.random_base2(m=exponent)[:count]


def _simplex_from_breaks(unit_points: np.ndarray) -> np.ndarray:
    """
    Map d-1 values in [0, 1] onto a d-dimensional simplex.

    We treat the values as cut points on a unit stick, sort them, then use the
    segment lengths as weights. The result is non-negative and sums exactly to 1.
    """
    sorted_breaks = np.sort(unit_points, axis=1)
    zeros = np.zeros((unit_points.shape[0], 1), dtype=np.float64)
    ones = np.ones((unit_points.shape[0], 1), dtype=np.float64)
    boundaries = np.concatenate((zeros, sorted_breaks, ones), axis=1)
    return np.diff(boundaries, axis=1)


def _scale(values: np.ndarray, low: float, high: float) -> np.ndarray:
    return low + values * (high - low)


def _get_scalar_bounds(archetype: Mapping) -> ScalarBounds:
    min_exposure = _as_range(archetype["min_exposure"])
    aggression_slope = _as_range(archetype["aggression_slope"])
    exposure_baseline = _as_range(archetype["exposure_baseline"])
    rebalance_threshold = _as_range(archetype["rebalance_threshold"])

    temp_low, temp_high = _as_range(archetype["temp"])
    softmax_temp = (max(0.01, temp_low), temp_high)

    return ScalarBounds(
        min_exposure=min_exposure,
        aggression_slope=aggression_slope,
        exposure_baseline=exposure_baseline,
        rebalance_threshold=rebalance_threshold,
        softmax_temp=softmax_temp,
    )


def generate_space_filling_users(
    archetype_key: str,
    count: int,
    archetypes: Mapping,
    seed: int | None = 42,
) -> dict[str, dict]:
    """
    Generate a broad quasi-random sample of the full parameter space.

    Effective dimensions:
    - 2 for 3 time weights on the simplex
    - 5 for 6 metric weights on the simplex
    - 5 independent scalar parameters
    """
    if archetype_key == "benchmark":
        return {
            "benchmark": {
                "name": "benchmark",
                "id": "0",
                "archetype_key": "benchmark",
                "time_weights": {
                    "short_term_14d": 0.0,
                    "medium_term_50d": 0.0,
                    "long_term_200d": 0.0,
                },
                "metric_weights": {
                    "relative_technical_strength": 0.0,
                    "relative_fundamental_support": 0.0,
                    "relative_valuation_sustainability": 0.0,
                    "relative_structural_risk": 0.0,
                    "relative_conviction": 0.0,
                    "relative_asymmetry_profile": 0.0,
                },
                "min_exposure": 0.0,
                "aggression_slope": 0.0,
                "exposure_baseline": 0.0,
                "rebalance_threshold": 0.0,
                "softmax_temp": 0.0,
            }
        }

    archetype = archetypes[archetype_key]
    points = _sobol_points(count=count, dimensions=12, seed=seed)

    time_weights = _simplex_from_breaks(points[:, 0:2])
    metric_weights = _simplex_from_breaks(points[:, 2:7])
    scalar_points = points[:, 7:12]
    bounds = _get_scalar_bounds(archetype)

    min_exposure = _scale(scalar_points[:, 0], *bounds.min_exposure)
    aggression_slope = _scale(scalar_points[:, 1], *bounds.aggression_slope)
    exposure_baseline = _scale(scalar_points[:, 2], *bounds.exposure_baseline)
    rebalance_threshold = _scale(scalar_points[:, 3], *bounds.rebalance_threshold)
    softmax_temp = _scale(scalar_points[:, 4], *bounds.softmax_temp)

    generated_users: dict[str, dict] = {}
    for index in range(count):
        user_id = f"{archetype_key}_{index + 1:06d}"
        generated_users[user_id] = {
            "archetype_key": archetype_key,
            "time_weights": {
                "short_term_14d": round(float(time_weights[index, 0]), 6),
                "medium_term_50d": round(float(time_weights[index, 1]), 6),
                "long_term_200d": round(float(time_weights[index, 2]), 6),
            },
            "metric_weights": {
                "relative_technical_strength": round(float(metric_weights[index, 0]), 6),
                "relative_fundamental_support": round(float(metric_weights[index, 1]), 6),
                "relative_valuation_sustainability": round(float(metric_weights[index, 2]), 6),
                "relative_structural_risk": round(float(metric_weights[index, 3]), 6),
                "relative_conviction": round(float(metric_weights[index, 4]), 6),
                "relative_asymmetry_profile": round(float(metric_weights[index, 5]), 6),
            },
            "min_exposure": round(float(min_exposure[index]), 6),
            "aggression_slope": round(float(aggression_slope[index]), 6),
            "exposure_baseline": round(float(exposure_baseline[index]), 6),
            "rebalance_threshold": round(float(rebalance_threshold[index]), 6),
            "softmax_temp": round(float(softmax_temp[index]), 6),
        }

    return generated_users
