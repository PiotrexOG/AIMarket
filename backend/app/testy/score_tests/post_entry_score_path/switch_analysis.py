import numpy as np
import pandas as pd

from app.testy.score_tests.common.metrics import round_or_none

from .config import ENTRY_BUCKET_COLUMNS, SWITCH_SCORE_CHANGE_THRESHOLDS


def _summarize_switch_group(group):
    annualized_gain = group["switch_to_benchmark_annualized_gain"].to_numpy(
        dtype=float
    )
    return_gain = group["switch_to_benchmark_return_gain"].to_numpy(dtype=float)
    downside_gain = np.minimum(0.0, annualized_gain)
    mean_annualized_gain = float(annualized_gain.mean())
    downside_deviation = float(np.sqrt(np.mean(np.square(downside_gain))))

    if downside_deviation == 0:
        downside_information_ratio = (
            0.0
            if mean_annualized_gain == 0
            else np.inf * np.sign(mean_annualized_gain)
        )
    else:
        downside_information_ratio = mean_annualized_gain / downside_deviation

    return {
        "switch_count": int(len(group)),
        "downside_count": int((annualized_gain < 0).sum()),
        "downside_frequency": float((annualized_gain < 0).mean()),
        "benchmark_win_frequency": float((annualized_gain > 0).mean()),
        "mean_switch_to_benchmark_return_gain": float(return_gain.mean()),
        "mean_switch_to_benchmark_annualized_gain": mean_annualized_gain,
        "median_switch_to_benchmark_annualized_gain": float(
            np.median(annualized_gain)
        ),
        "downside_deviation": downside_deviation,
        "downside_information_ratio": downside_information_ratio,
        "mean_remaining_return": float(group["remaining_return"].mean()),
        "mean_remaining_annualized_return": float(
            group["remaining_annualized_return"].mean()
        ),
        "mean_remaining_benchmark_return": float(
            group["remaining_benchmark_return"].mean()
        ),
        "mean_remaining_annualized_benchmark_return": float(
            group["remaining_annualized_benchmark_return"].mean()
        ),
    }


def _mark_best_switch_thresholds(result, group_columns):
    if result.empty:
        return result

    result = result.copy()
    result["is_max_downside_information_ratio"] = False
    result["is_max_mean_switch_gain"] = False

    grouped = result.groupby(list(group_columns), sort=False)
    for _, group in grouped:
        finite_ratio = group[
            np.isfinite(group["downside_information_ratio"].to_numpy(dtype=float))
        ]
        if not finite_ratio.empty:
            max_ratio_index = finite_ratio["downside_information_ratio"].idxmax()
            result.loc[max_ratio_index, "is_max_downside_information_ratio"] = True

        finite_gain = group[
            np.isfinite(
                group["mean_switch_to_benchmark_annualized_gain"].to_numpy(
                    dtype=float
                )
            )
        ]
        if not finite_gain.empty:
            max_gain_index = finite_gain[
                "mean_switch_to_benchmark_annualized_gain"
            ].idxmax()
            result.loc[max_gain_index, "is_max_mean_switch_gain"] = True

    return result


def _build_switch_to_benchmark_threshold_analysis(
    live_progress_observations,
    thresholds=SWITCH_SCORE_CHANGE_THRESHOLDS,
    group_columns=("timeframe", "progress_percent"),
):
    metadata_columns = [
        "entry_min_score_percentile",
        "entry_percentile_bucket_slug",
        "entry_percentile_bucket_label",
        "entry_percentile_bucket_rank_start",
        "entry_percentile_bucket_rank_end",
        "progress_bucket_end_percent",
        "progress_bucket_mid_percent",
        "progress_bucket_label",
        "progress_percent",
        "progress_share",
        "mean_cutoff_weeks",
    ]
    columns = [
        *group_columns,
        *[
            column
            for column in metadata_columns
            if column not in group_columns
        ],
        "score_change_threshold",
        "score_change_threshold_percent",
        "observation_count",
        "switch_count",
        "switch_share",
        "downside_count",
        "downside_frequency",
        "benchmark_win_frequency",
        "mean_switch_to_benchmark_return_gain",
        "mean_switch_to_benchmark_annualized_gain",
        "median_switch_to_benchmark_annualized_gain",
        "downside_deviation",
        "downside_information_ratio",
        "mean_remaining_return",
        "mean_remaining_annualized_return",
        "mean_remaining_benchmark_return",
        "mean_remaining_annualized_benchmark_return",
        "is_max_downside_information_ratio",
        "is_max_mean_switch_gain",
    ]
    required = [
        "relative_score_percentile_change",
        "switch_to_benchmark_return_gain",
        "switch_to_benchmark_annualized_gain",
        "remaining_return",
        "remaining_annualized_return",
        "remaining_benchmark_return",
        "remaining_annualized_benchmark_return",
    ]
    if (
        live_progress_observations.empty
        or not set(required).issubset(live_progress_observations.columns)
    ):
        return pd.DataFrame(columns=columns)

    data = (
        live_progress_observations.replace([np.inf, -np.inf], np.nan)
        .dropna(subset=required)
        .copy()
    )
    if data.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for group_key, group in data.groupby(list(group_columns), sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        observation_count = int(len(group))
        metadata = {}
        if "progress_bucket_end_percent" in group.columns:
            metadata["progress_bucket_end_percent"] = float(
                group["progress_bucket_end_percent"].iloc[0]
            )
        if "progress_bucket_mid_percent" in group.columns:
            metadata["progress_bucket_mid_percent"] = float(
                group["progress_bucket_mid_percent"].iloc[0]
            )
        if "progress_bucket_label" in group.columns:
            metadata["progress_bucket_label"] = group[
                "progress_bucket_label"
            ].iloc[0]
        if "progress_percent" in group.columns:
            metadata["progress_percent"] = round_or_none(
                group["progress_percent"].mean()
            )
        if "progress_share" in group.columns:
            metadata["progress_share"] = round_or_none(
                group["progress_share"].mean()
            )
        if "cutoff_weeks" in group.columns:
            metadata["mean_cutoff_weeks"] = round_or_none(
                group["cutoff_weeks"].mean()
            )
        for column in ENTRY_BUCKET_COLUMNS:
            if column not in group_columns and column in group.columns:
                metadata[column] = group[column].iloc[0]

        for threshold in thresholds:
            selected = group[
                group["relative_score_percentile_change"] <= threshold
            ]
            if selected.empty:
                continue

            summary = _summarize_switch_group(selected)
            rows.append({
                **group_values,
                **metadata,
                "score_change_threshold": float(threshold),
                "score_change_threshold_percent": round_or_none(
                    float(threshold) * 100
                ),
                "observation_count": observation_count,
                "switch_share": len(selected) / observation_count,
                **summary,
            })

    if not rows:
        return pd.DataFrame(columns=columns)

    result = pd.DataFrame(rows)
    result = _mark_best_switch_thresholds(result, group_columns)
    return (
        result[columns]
        .sort_values([*group_columns, "score_change_threshold"])
        .reset_index(drop=True)
    )
