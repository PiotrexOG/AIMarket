import pandas as pd

from app.testy.score_tests.common.metrics import round_or_none

from .config import (
    CORRELATION_METRICS,
    ENTRY_BUCKET_COLUMNS,
    LIVE_CORRELATION_METRICS,
)
from .utilities import _first_existing_columns, _safe_corr_pair


def _build_correlations_by_horizon(
    observations,
    return_metric="annualized_return",
):
    rows = []
    if observations.empty:
        return pd.DataFrame()
    if return_metric not in observations.columns:
        return pd.DataFrame()

    group_columns = [
        *_first_existing_columns(observations, ENTRY_BUCKET_COLUMNS),
        "timeframe",
        "horizon_weeks",
    ]
    for group_key, group in observations.groupby(
        group_columns,
        sort=False,
    ):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        for metric in CORRELATION_METRICS:
            rows.append({
                **group_values,
                "horizon_weeks": int(group_values["horizon_weeks"]),
                "horizon_days": round_or_none(group["horizon_days"].mean()),
                "metric": metric,
                "observation_count": int(
                    group[[metric, return_metric]].dropna().shape[0]
                ),
                "pearson_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "pearson",
                ),
                "spearman_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "spearman",
                ),
                "mean_metric_value": round_or_none(group[metric].mean()),
                "mean_annualized_return": round_or_none(
                    group[return_metric].mean()
                ),
            })

    return pd.DataFrame(rows)


def _build_horizon_average(correlations_by_horizon):
    columns = [
        *ENTRY_BUCKET_COLUMNS,
        "timeframe",
        "horizon_week_start",
        "horizon_week_end",
        "horizon_count",
        "aggregation_method",
        "metric",
        "mean_observation_count",
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
        "mean_metric_value",
        "mean_annualized_return",
    ]
    if correlations_by_horizon.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    group_columns = [
        *_first_existing_columns(correlations_by_horizon, ENTRY_BUCKET_COLUMNS),
        "timeframe",
        "metric",
    ]
    for group_key, group in correlations_by_horizon.groupby(
        group_columns,
        sort=False,
    ):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        rows.append({
            **group_values,
            "horizon_week_start": int(group["horizon_weeks"].min()),
            "horizon_week_end": int(group["horizon_weeks"].max()),
            "horizon_count": int(group["horizon_weeks"].nunique()),
            "aggregation_method": "equal_weight_mean_across_horizons",
            "mean_observation_count": round_or_none(
                group["observation_count"].mean()
            ),
            "mean_pearson_to_annualized_return": round_or_none(
                group["pearson_to_annualized_return"].mean()
            ),
            "mean_spearman_to_annualized_return": round_or_none(
                group["spearman_to_annualized_return"].mean()
            ),
            "mean_metric_value": round_or_none(group["mean_metric_value"].mean()),
            "mean_annualized_return": round_or_none(
                group["mean_annualized_return"].mean()
            ),
        })

    sort_columns = [
        *_first_existing_columns(pd.DataFrame(rows), ["entry_percentile_bucket_id"]),
        "timeframe",
        "metric",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values(
        sort_columns
    ).reset_index(drop=True)


def _build_live_progress_correlations_by_horizon(
    live_progress_observations,
    return_metric="annualized_return",
):
    rows = []
    if live_progress_observations.empty:
        return pd.DataFrame()
    if return_metric not in live_progress_observations.columns:
        return pd.DataFrame()

    group_columns = [
        *_first_existing_columns(
            live_progress_observations,
            ENTRY_BUCKET_COLUMNS,
        ),
        "timeframe",
        "horizon_weeks",
        "progress_bucket_start_percent",
    ]
    grouped = live_progress_observations.groupby(
        group_columns,
        sort=False,
    )
    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        bucket_row = group.iloc[0]
        for metric in LIVE_CORRELATION_METRICS:
            rows.append({
                **group_values,
                "horizon_weeks": int(group_values["horizon_weeks"]),
                "horizon_days": round_or_none(group["horizon_days"].mean()),
                "cutoff_weeks": round_or_none(group["cutoff_weeks"].mean()),
                "progress_bucket_start_percent": float(
                    group_values["progress_bucket_start_percent"]
                ),
                "progress_bucket_end_percent": float(
                    bucket_row["progress_bucket_end_percent"]
                ),
                "progress_bucket_mid_percent": float(
                    bucket_row["progress_bucket_mid_percent"]
                ),
                "progress_bucket_label": bucket_row["progress_bucket_label"],
                "progress_percent": round_or_none(
                    group["progress_percent"].mean()
                ),
                "progress_share": round_or_none(group["progress_share"].mean()),
                "cutoff_days": round_or_none(group["cutoff_days"].mean()),
                "metric": metric,
                "observation_count": int(
                    group[[metric, return_metric]].dropna().shape[0]
                ),
                "pearson_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "pearson",
                ),
                "spearman_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "spearman",
                ),
            })

    return pd.DataFrame(rows)


def _build_live_progress_average(correlations_by_horizon):
    columns = [
        *ENTRY_BUCKET_COLUMNS,
        "timeframe",
        "progress_bucket_start_percent",
        "progress_bucket_end_percent",
        "progress_bucket_mid_percent",
        "progress_bucket_label",
        "mean_cutoff_weeks",
        "progress_percent",
        "progress_share",
        "metric",
        "horizon_week_start",
        "horizon_week_end",
        "horizon_count",
        "mean_cutoff_days",
        "mean_observation_count",
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
    ]
    if correlations_by_horizon.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    group_columns = [
        *_first_existing_columns(correlations_by_horizon, ENTRY_BUCKET_COLUMNS),
        "timeframe",
        "progress_bucket_start_percent",
        "metric",
    ]
    grouped = correlations_by_horizon.groupby(
        group_columns,
        sort=False,
    )
    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        bucket_row = group.iloc[0]
        rows.append({
            **group_values,
            "progress_bucket_start_percent": float(
                group_values["progress_bucket_start_percent"]
            ),
            "progress_bucket_end_percent": float(
                bucket_row["progress_bucket_end_percent"]
            ),
            "progress_bucket_mid_percent": float(
                bucket_row["progress_bucket_mid_percent"]
            ),
            "progress_bucket_label": bucket_row["progress_bucket_label"],
            "mean_cutoff_weeks": round_or_none(group["cutoff_weeks"].mean()),
            "progress_percent": round_or_none(group["progress_percent"].mean()),
            "progress_share": round_or_none(group["progress_share"].mean()),
            "horizon_week_start": int(group["horizon_weeks"].min()),
            "horizon_week_end": int(group["horizon_weeks"].max()),
            "horizon_count": int(group["horizon_weeks"].nunique()),
            "mean_cutoff_days": round_or_none(group["cutoff_days"].mean()),
            "mean_observation_count": round_or_none(
                group["observation_count"].mean()
            ),
            "mean_pearson_to_annualized_return": round_or_none(
                group["pearson_to_annualized_return"].mean()
            ),
            "mean_spearman_to_annualized_return": round_or_none(
                group["spearman_to_annualized_return"].mean()
            ),
        })

    sort_columns = [
        *_first_existing_columns(pd.DataFrame(rows), ["entry_percentile_bucket_id"]),
        "timeframe",
        "metric",
        "progress_bucket_start_percent",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values(
        sort_columns
    ).reset_index(drop=True)
