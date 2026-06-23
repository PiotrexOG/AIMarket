import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import (
    TRADING_DAYS_PER_YEAR,
    annualize_return,
)
from app.testy.score_tests.common.metrics import round_or_none


DEFAULT_HORIZON_START = 195
DEFAULT_HORIZON_END = 205
ENTRY_TOP_N = 1

TOP_THRESHOLDS = (0.50, 0.70, 0.90)
CORRELATION_METRICS = [
    "mean_rank_share_from_top",
    "worst_rank_share_from_top",
    "mean_score_percentile",
    "worst_score_percentile",
    "max_rank_share_drop_from_entry",
    "horizon_share_score_below_entry",
    "horizon_share_below_top_50",
    "horizon_share_below_top_70",
    "horizon_share_below_top_90",
    "longest_horizon_share_below_top_50",
    "longest_horizon_share_below_top_70",
    "longest_horizon_share_below_top_90",
]


def _weighted_mean(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return None
    return float(np.average(values[valid], weights=weights[valid]))


def _safe_corr(group, metric, method):
    clean = group[[metric, "annualized_return"]].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    if (
        len(clean) < 3
        or clean[metric].nunique() < 2
        or clean["annualized_return"].nunique() < 2
    ):
        return None
    return round_or_none(clean[metric].corr(clean["annualized_return"], method=method))


def _prepare_score_history(return_panel):
    columns = [
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "score_zscore",
    ]
    required = set(columns)
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame(columns=[
            *columns,
            "rank_position",
            "available_count",
            "rank_share_from_top",
        ])

    history = (
        return_panel[columns]
        .dropna(subset=["timeframe", "ticker", "start_timestamp", "score"])
        .drop_duplicates(["timeframe", "ticker", "start_timestamp"])
        .sort_values(
            ["timeframe", "start_timestamp", "score", "ticker"],
            ascending=[True, True, False, True],
        )
        .reset_index(drop=True)
    )
    history["rank_position"] = (
        history.groupby(["timeframe", "start_timestamp"]).cumcount() + 1
    )
    history["available_count"] = history.groupby(
        ["timeframe", "start_timestamp"]
    )["ticker"].transform("count")
    history["rank_share_from_top"] = (
        history["rank_position"] / history["available_count"]
    )
    return history


def _prepare_top_entry_observations(
    return_panel,
    horizon_start,
    horizon_end,
    annualization_days,
):
    if return_panel.empty:
        return pd.DataFrame()

    ranked = (
        return_panel[
            return_panel["horizon_days"].between(horizon_start, horizon_end)
        ]
        .dropna(subset=["score", "future_return"])
        .sort_values(
            ["timeframe", "horizon_days", "start_timestamp", "score", "ticker"],
            ascending=[True, True, True, False, True],
        )
        .copy()
    )
    if ranked.empty:
        return pd.DataFrame()

    ranked["entry_rank_position"] = (
        ranked.groupby(["timeframe", "horizon_days", "start_timestamp"]).cumcount()
        + 1
    )
    ranked["entry_available_count"] = ranked.groupby(
        ["timeframe", "horizon_days", "start_timestamp"]
    )["ticker"].transform("count")
    ranked = ranked[ranked["entry_rank_position"] <= ENTRY_TOP_N].copy()
    ranked["entry_rank_share_from_top"] = (
        ranked["entry_rank_position"] / ranked["entry_available_count"]
    )
    ranked["annualization_days"] = int(annualization_days)
    ranked["annualized_return"] = [
        annualize_return(total_return, horizon_days, annualization_days)
        for total_return, horizon_days in zip(
            ranked["future_return"],
            ranked["horizon_days"],
        )
    ]
    ranked = ranked.dropna(subset=["annualized_return"])
    ranked["observation_id"] = (
        ranked.groupby(["timeframe", "horizon_days"]).cumcount() + 1
    )
    return ranked.reset_index(drop=True)


def _build_path_for_entry(entry, history):
    start_timestamp = pd.Timestamp(entry["start_timestamp"])
    end_timestamp = start_timestamp + pd.to_timedelta(
        int(entry["horizon_days"]),
        unit="D",
    )
    path = history[
        (history["timeframe"] == entry["timeframe"])
        & (history["ticker"] == entry["ticker"])
        & (history["start_timestamp"] >= start_timestamp)
        & (history["start_timestamp"] <= end_timestamp)
    ].copy()
    if path.empty:
        return path

    path = path.sort_values("start_timestamp").reset_index(drop=True)
    next_timestamps = path["start_timestamp"].shift(-1)
    path["next_score_timestamp"] = next_timestamps.fillna(end_timestamp)
    path["next_score_timestamp"] = pd.to_datetime(
        np.minimum(
            path["next_score_timestamp"].to_numpy(dtype="datetime64[ns]"),
            np.datetime64(end_timestamp),
        )
    )
    path["elapsed_days"] = (
        pd.to_datetime(path["start_timestamp"]) - start_timestamp
    ).dt.days.clip(lower=0)
    path["segment_days"] = (
        path["next_score_timestamp"] - pd.to_datetime(path["start_timestamp"])
    ).dt.days.clip(lower=0)
    path["segment_horizon_share"] = (
        path["segment_days"] / float(entry["horizon_days"])
    )
    path["entry_score"] = float(entry["score"])
    path["entry_score_percentile"] = float(entry["score_percentile"])
    path["entry_rank_share_from_top"] = float(entry["entry_rank_share_from_top"])
    path["rank_share_drop_from_entry"] = (
        path["rank_share_from_top"] - path["entry_rank_share_from_top"]
    )
    path["score_percentile_change_from_entry"] = (
        path["score_percentile"] - path["entry_score_percentile"]
    )
    path["is_score_below_entry"] = path["score"] < float(entry["score"])
    for threshold in TOP_THRESHOLDS:
        suffix = int(threshold * 100)
        path[f"is_below_top_{suffix}"] = (
            path["rank_share_from_top"] > threshold
        )
    return path


def _longest_weighted_true_share(path, flag_column, horizon_days):
    longest = 0
    current = 0
    for is_flagged, segment_days in zip(path[flag_column], path["segment_days"]):
        if bool(is_flagged):
            current += int(segment_days)
            longest = max(longest, current)
        else:
            current = 0
    return float(longest / horizon_days) if horizon_days else None


def _summarize_entry_path(entry, path):
    horizon_days = int(entry["horizon_days"])
    segment_days = path["segment_days"].to_numpy(dtype=float)
    covered_days = float(np.nansum(segment_days))

    row = {
        "timeframe": entry["timeframe"],
        "horizon_days": horizon_days,
        "annualization_days": int(entry["annualization_days"]),
        "observation_id": int(entry["observation_id"]),
        "start_timestamp": entry["start_timestamp"],
        "future_timestamp": entry["future_timestamp"],
        "ticker": entry["ticker"],
        "entry_score": float(entry["score"]),
        "entry_score_percentile": float(entry["score_percentile"]),
        "entry_score_zscore": float(entry["score_zscore"]),
        "entry_rank_position": int(entry["entry_rank_position"]),
        "entry_available_count": int(entry["entry_available_count"]),
        "entry_rank_share_from_top": float(entry["entry_rank_share_from_top"]),
        "current_price": float(entry["current_price"]),
        "future_price": float(entry["future_price"]),
        "future_return": float(entry["future_return"]),
        "annualized_return": float(entry["annualized_return"]),
        "path_point_count": int(len(path)),
        "path_covered_days": covered_days,
        "path_covered_horizon_share": covered_days / horizon_days,
        "mean_score": _weighted_mean(path["score"], segment_days),
        "mean_score_percentile": _weighted_mean(
            path["score_percentile"],
            segment_days,
        ),
        "mean_rank_share_from_top": _weighted_mean(
            path["rank_share_from_top"],
            segment_days,
        ),
        "worst_score_percentile": float(path["score_percentile"].min()),
        "worst_rank_share_from_top": float(path["rank_share_from_top"].max()),
        "max_rank_share_drop_from_entry": float(
            path["rank_share_drop_from_entry"].max()
        ),
        "horizon_share_score_below_entry": float(
            np.nansum(
                path.loc[path["is_score_below_entry"], "segment_days"]
            )
            / horizon_days
        ),
    }

    for threshold in TOP_THRESHOLDS:
        suffix = int(threshold * 100)
        flag_column = f"is_below_top_{suffix}"
        below_days = float(np.nansum(path.loc[path[flag_column], "segment_days"]))
        row[f"horizon_share_below_top_{suffix}"] = below_days / horizon_days
        row[f"longest_horizon_share_below_top_{suffix}"] = (
            _longest_weighted_true_share(path, flag_column, horizon_days)
        )

    return row


def _build_observations_and_paths(entries, history):
    observation_rows = []
    path_frames = []

    for _, entry in entries.iterrows():
        path = _build_path_for_entry(entry, history)
        if path.empty:
            continue

        observation_rows.append(_summarize_entry_path(entry, path))
        path = path.copy()
        path["timeframe"] = entry["timeframe"]
        path["horizon_days"] = int(entry["horizon_days"])
        path["observation_id"] = int(entry["observation_id"])
        path["entry_start_timestamp"] = entry["start_timestamp"]
        path["future_timestamp"] = entry["future_timestamp"]
        path["future_return"] = float(entry["future_return"])
        path["annualized_return"] = float(entry["annualized_return"])
        path_frames.append(path)

    observations = pd.DataFrame(observation_rows)
    path_points = (
        pd.concat(path_frames, ignore_index=True)
        if path_frames
        else pd.DataFrame()
    )
    return observations, path_points


def _build_correlations_by_horizon(observations):
    rows = []
    if observations.empty:
        return pd.DataFrame()

    for (timeframe, horizon_days), group in observations.groupby(
        ["timeframe", "horizon_days"],
        sort=False,
    ):
        for metric in CORRELATION_METRICS:
            rows.append({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "metric": metric,
                "observation_count": int(group[[metric, "annualized_return"]].dropna().shape[0]),
                "pearson_to_annualized_return": _safe_corr(group, metric, "pearson"),
                "spearman_to_annualized_return": _safe_corr(group, metric, "spearman"),
                "mean_metric_value": round_or_none(group[metric].mean()),
                "mean_annualized_return": round_or_none(
                    group["annualized_return"].mean()
                ),
            })

    return pd.DataFrame(rows)


def _build_horizon_average(correlations_by_horizon):
    columns = [
        "timeframe",
        "horizon_start",
        "horizon_end",
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
    for (timeframe, metric), group in correlations_by_horizon.groupby(
        ["timeframe", "metric"],
        sort=False,
    ):
        rows.append({
            "timeframe": timeframe,
            "horizon_start": int(group["horizon_days"].min()),
            "horizon_end": int(group["horizon_days"].max()),
            "horizon_count": int(group["horizon_days"].nunique()),
            "aggregation_method": "equal_weight_mean_across_horizons",
            "metric": metric,
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

    return pd.DataFrame(rows, columns=columns).sort_values(
        ["timeframe", "metric"]
    ).reset_index(drop=True)


def _build_bucket_summary(observations):
    rows = []
    if observations.empty:
        return pd.DataFrame()

    bucket_metrics = [
        "worst_rank_share_from_top",
        "horizon_share_below_top_70",
        "longest_horizon_share_below_top_70",
        "max_rank_share_drop_from_entry",
    ]

    for (timeframe, horizon_days), group in observations.groupby(
        ["timeframe", "horizon_days"],
        sort=False,
    ):
        for metric in bucket_metrics:
            clean = group.dropna(subset=[metric, "annualized_return"])
            if clean.empty:
                continue
            bucket_count = min(4, clean[metric].nunique())
            if bucket_count < 2:
                continue
            bucketed = clean.copy()
            bucketed["metric_bucket"] = pd.qcut(
                bucketed[metric],
                q=bucket_count,
                duplicates="drop",
            )
            for bucket, bucket_group in bucketed.groupby("metric_bucket", observed=True):
                rows.append({
                    "timeframe": timeframe,
                    "horizon_days": int(horizon_days),
                    "metric": metric,
                    "bucket": str(bucket),
                    "observation_count": int(len(bucket_group)),
                    "min_metric_value": round_or_none(bucket_group[metric].min()),
                    "max_metric_value": round_or_none(bucket_group[metric].max()),
                    "mean_metric_value": round_or_none(bucket_group[metric].mean()),
                    "mean_annualized_return": round_or_none(
                        bucket_group["annualized_return"].mean()
                    ),
                    "median_annualized_return": round_or_none(
                        bucket_group["annualized_return"].median()
                    ),
                })

    return pd.DataFrame(rows)


def _round_numeric_columns(df):
    if df.empty:
        return df
    result = df.copy()
    for column in result.select_dtypes(include=[np.number]).columns:
        if column not in {
            "horizon_days",
            "annualization_days",
            "observation_id",
            "entry_rank_position",
            "entry_available_count",
            "rank_position",
            "available_count",
            "path_point_count",
        }:
            result[column] = result[column].round(6)
    return result


def calculate(
    context,
    horizon_start=DEFAULT_HORIZON_START,
    horizon_end=DEFAULT_HORIZON_END,
    annualization_days=TRADING_DAYS_PER_YEAR,
):
    history = _prepare_score_history(context.return_panel)
    entries = _prepare_top_entry_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        annualization_days=annualization_days,
    )
    observations, path_points = _build_observations_and_paths(entries, history)
    correlations_by_horizon = _build_correlations_by_horizon(observations)
    horizon_average = _build_horizon_average(correlations_by_horizon)
    bucket_summary = _build_bucket_summary(observations)

    return {
        "observations": _round_numeric_columns(observations),
        "path_points": _round_numeric_columns(path_points),
        "correlations_by_horizon": _round_numeric_columns(correlations_by_horizon),
        "horizon_average": _round_numeric_columns(horizon_average),
        "bucket_summary": _round_numeric_columns(bucket_summary),
    }
