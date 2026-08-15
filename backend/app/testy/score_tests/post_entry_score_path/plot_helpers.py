from pathlib import Path

import numpy as np
import pandas as pd

from app.testy.score_tests.common.output_paths import (
    POST_ENTRY_SCORE_PATH_DIR,
    horizon_dir,
)

from .plot_config import (
    ALL_SCORES_ONLY_TIMEFRAME,
    ALL_SCORES_SLUG,
    ENTRY_MIN_SCORE_PERCENTILE,
    ENTRY_MIN_SCORE_PERCENTILE_70_SLUG,
    MAX_PROGRESS_BUCKET_PERCENT,
    MIN_PROGRESS_BUCKET_PERCENT,
    PLOT_MODE_FULL,
    PLOT_MODE_ONLY_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE,
    PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE,
    PROGRESS_BUCKET_PERCENTAGE_POINTS,
    USE_ENTRY_PERCENTILE_BUCKETS,
)


def _entry_percentile_bins_and_labels(data=None):
    if USE_ENTRY_PERCENTILE_BUCKETS and data is not None and not data.empty:
        start_percent = int(
            np.floor(data["entry_score_percentile"].min() * 10) * 10
        )
    elif (
        data is not None
        and not data.empty
        and "entry_min_score_percentile" in data.columns
    ):
        start_percent = int(
            round(float(data["entry_min_score_percentile"].iloc[0]) * 100)
        )
    else:
        start_percent = int(round(ENTRY_MIN_SCORE_PERCENTILE * 100))
    step_percent = 10
    start_percent = max(0, min(90, start_percent))
    boundaries = list(range(start_percent, 101, step_percent))
    if boundaries[-1] != 100:
        boundaries.append(100)

    bins = [value / 100 for value in boundaries]
    bins[-1] = 1.000001
    labels = [
        f"{left}-{right}%"
        for left, right in zip(boundaries[:-1], boundaries[1:])
    ]
    return bins, labels


def _entry_min_score_percentile(data):
    if (
        data is not None
        and not data.empty
        and "entry_min_score_percentile" in data.columns
    ):
        return float(data["entry_min_score_percentile"].iloc[0])
    return ENTRY_MIN_SCORE_PERCENTILE


def _filter_results_for_entry_bucket(results, bucket_id):
    filtered = {}
    for key, value in results.items():
        if (
            isinstance(value, pd.DataFrame)
            and "entry_percentile_bucket_id" in value.columns
        ):
            filtered[key] = value[
                value["entry_percentile_bucket_id"] == bucket_id
            ].copy()
        else:
            filtered[key] = value
    return filtered


def _plot_mode_for_entry_bucket_slug(slug):
    if slug == ALL_SCORES_SLUG:
        return PLOT_MODE_ONLY_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE
    if slug == ENTRY_MIN_SCORE_PERCENTILE_70_SLUG:
        return PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE
    return PLOT_MODE_FULL


def _filter_all_scores_only_plot_data(data):
    if data is None or data.empty or "timeframe" not in data.columns:
        return data
    return data[data["timeframe"] == ALL_SCORES_ONLY_TIMEFRAME]


def _horizon_range_title_label(horizon_label):
    horizon_part = Path(horizon_label).parts[0]
    if horizon_part.endswith("w"):
        horizon_part = horizon_part[:-1]
        return f"{horizon_part} tygodni"
    return str(horizon_part).replace("_", " ")


def _score_scope_title_label(horizon_label):
    parts = Path(horizon_label).parts
    if len(parts) < 2:
        return None

    score_scope = parts[1]
    if score_scope == ALL_SCORES_SLUG:
        return "wszystkie"
    prefix = "entry_min_score_percentile_"
    if score_scope.startswith(prefix):
        return f"top {int(score_scope.removeprefix(prefix))} percentyl"
    return score_scope.replace("_", " ")


def _plot_context_title_label(horizon_label):
    context = _horizon_range_title_label(horizon_label)
    score_scope = _score_scope_title_label(horizon_label)
    if score_scope is not None and score_scope != "wszystkie":
        context = f"{context}, {score_scope} scores"
    return context


def _post_entry_dir(horizon_label, *sections):
    return horizon_dir(POST_ENTRY_SCORE_PATH_DIR, horizon_label, *sections)


def _target_progress_bucket_start(progress_percent):
    bucket_start = np.floor(
        progress_percent / PROGRESS_BUCKET_PERCENTAGE_POINTS
    ) * PROGRESS_BUCKET_PERCENTAGE_POINTS
    return max(
        float(MIN_PROGRESS_BUCKET_PERCENT),
        min(
            float(MAX_PROGRESS_BUCKET_PERCENT - PROGRESS_BUCKET_PERCENTAGE_POINTS),
            float(bucket_start),
        ),
    )


def _filter_progress_bucket(data, progress_percent):
    if "progress_bucket_start_percent" not in data.columns:
        return (
            data[data["progress_percent"] == progress_percent],
            f"{progress_percent}%",
            f"{progress_percent}pct",
        )

    bucket_start = _target_progress_bucket_start(progress_percent)
    bucket_end = bucket_start + PROGRESS_BUCKET_PERCENTAGE_POINTS
    return (
        data[data["progress_bucket_start_percent"] == bucket_start],
        f"{bucket_start:.0f}-{bucket_end:.0f}%",
        f"{bucket_start:.0f}_{bucket_end:.0f}pct",
    )


def _progress_x_column(data):
    if "progress_bucket_mid_percent" in data.columns:
        return "progress_bucket_mid_percent"
    return "progress_percent"


def _set_progress_x_ticks(ax, data):
    if {
        "progress_bucket_start_percent",
        "progress_bucket_mid_percent",
        "progress_bucket_label",
    }.issubset(data.columns):
        labels = (
            data[
                [
                    "progress_bucket_start_percent",
                    "progress_bucket_mid_percent",
                    "progress_bucket_label",
                ]
            ]
            .drop_duplicates()
            .sort_values("progress_bucket_start_percent")
        )
        ax.set_xticks(labels["progress_bucket_mid_percent"])
        ax.set_xticklabels(labels["progress_bucket_label"], rotation=45)
        return

    ax.set_xticks(range(5, 101, 5))
    ax.set_xticklabels(
        [f"{value}%" for value in range(5, 101, 5)],
        rotation=45,
    )
