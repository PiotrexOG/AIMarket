import numpy as np

from app.testy.score_tests.common.metrics import round_or_none

from .config import (
    MAX_PROGRESS_BUCKET_PERCENT,
    MIN_PROGRESS_BUCKET_PERCENT,
    PROGRESS_BUCKET_PERCENTAGE_POINTS,
    PROGRESS_WEEK_STEP,
)


def _first_existing_columns(df, columns):
    return [column for column in columns if column in df.columns]


def _first_value_or_none(group, column):
    return group[column].iloc[0] if column in group.columns else None

def _weighted_mean(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return None
    return float(np.average(values[valid], weights=weights[valid]))


def _overlap_days(segment_starts, segment_days, window_start, window_end):
    segment_ends = segment_starts + segment_days
    return np.maximum(
        0.0,
        np.minimum(segment_ends, window_end) - np.maximum(segment_starts, window_start),
    )


def _progress_weeks_for_horizon(horizon_weeks):
    return tuple(range(PROGRESS_WEEK_STEP, int(horizon_weeks), PROGRESS_WEEK_STEP))


def _progress_bucket(progress_percent):
    if (
        progress_percent < MIN_PROGRESS_BUCKET_PERCENT
        or progress_percent >= MAX_PROGRESS_BUCKET_PERCENT
    ):
        return None

    bucket_start = np.floor(
        progress_percent / PROGRESS_BUCKET_PERCENTAGE_POINTS
    ) * PROGRESS_BUCKET_PERCENTAGE_POINTS
    bucket_start = max(
        float(MIN_PROGRESS_BUCKET_PERCENT),
        min(
            float(MAX_PROGRESS_BUCKET_PERCENT - PROGRESS_BUCKET_PERCENTAGE_POINTS),
            float(bucket_start),
        ),
    )
    bucket_end = bucket_start + PROGRESS_BUCKET_PERCENTAGE_POINTS
    return {
        "progress_bucket_start_percent": bucket_start,
        "progress_bucket_end_percent": bucket_end,
        "progress_bucket_mid_percent": (bucket_start + bucket_end) / 2.0,
        "progress_bucket_label": f"{bucket_start:.0f}-{bucket_end:.0f}%",
    }


def _safe_corr(group, metric, method):
    return _safe_corr_pair(group, metric, "annualized_return", method)


def _safe_corr_pair(group, metric, return_metric, method):
    clean = group[[metric, return_metric]].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    if (
        len(clean) < 3
        or clean[metric].nunique() < 2
        or clean[return_metric].nunique() < 2
    ):
        return None
    return round_or_none(clean[metric].corr(clean[return_metric], method=method))
