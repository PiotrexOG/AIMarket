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
PROGRESS_PERCENTAGES = tuple(range(5, 101, 5))

CORRELATION_METRICS = [
    "mean_score_percentile",
    "worst_score_percentile",
]

LIVE_CORRELATION_METRICS = [
    "current_score_percentile",
    "worst_score_percentile",
    "mean_score_percentile",
    "rolling_mean_score_percentile_40",
    "ewma_score_percentile_halflife_40",
]

ROLLING_WINDOW_SHARES = (0.20, 0.40)
EWMA_HALFLIFE_SHARES = (0.10, 0.20, 0.40)


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


def _ewma_time_weights(
    segment_starts,
    segment_days,
    cutoff_days,
    half_life_days,
):
    segment_ends = np.minimum(segment_starts + segment_days, cutoff_days)
    valid = (segment_starts < cutoff_days) & (segment_ends > segment_starts)
    weights = np.zeros_like(segment_starts, dtype=float)
    if not valid.any() or half_life_days <= 0:
        return weights

    decay = np.log(2.0) / half_life_days
    starts = segment_starts[valid]
    ends = segment_ends[valid]
    weights[valid] = (
        np.exp(-decay * (cutoff_days - ends))
        - np.exp(-decay * (cutoff_days - starts))
    ) / decay
    return weights


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
        return pd.DataFrame(columns=columns)

    return (
        return_panel[columns]
        .dropna(subset=["timeframe", "ticker", "start_timestamp", "score"])
        .drop_duplicates(["timeframe", "ticker", "start_timestamp"])
        .sort_values(["timeframe", "ticker", "start_timestamp"])
        .reset_index(drop=True)
    )


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
    return path


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
        "current_price": float(entry["current_price"]),
        "future_price": float(entry["future_price"]),
        "future_return": float(entry["future_return"]),
        "annualized_return": float(entry["annualized_return"]),
        "path_point_count": int(len(path)),
        "path_covered_days": covered_days,
        "path_covered_horizon_share": covered_days / horizon_days,
        "mean_score_percentile": _weighted_mean(
            path["score_percentile"],
            segment_days,
        ),
        "worst_score_percentile": float(path["score_percentile"].min()),
    }

    return row


def _summarize_live_progress(entry, path):
    rows = []
    horizon_days = int(entry["horizon_days"])
    elapsed_days = path["elapsed_days"].to_numpy(dtype=float)
    segment_days = path["segment_days"].to_numpy(dtype=float)
    score_percentiles = path["score_percentile"].to_numpy(dtype=float)

    for progress_percent in PROGRESS_PERCENTAGES:
        cutoff_days = horizon_days * progress_percent / 100.0
        live_segment_days = _overlap_days(
            elapsed_days,
            segment_days,
            0.0,
            cutoff_days,
        )
        observed_mask = elapsed_days <= cutoff_days
        observed_percentiles = score_percentiles[observed_mask]
        observed_percentiles = observed_percentiles[
            np.isfinite(observed_percentiles)
        ]
        current_percentile = (
            float(observed_percentiles[-1])
            if observed_percentiles.size
            else None
        )

        row = {
            "timeframe": entry["timeframe"],
            "horizon_days": horizon_days,
            "observation_id": int(entry["observation_id"]),
            "start_timestamp": entry["start_timestamp"],
            "future_timestamp": entry["future_timestamp"],
            "ticker": entry["ticker"],
            "progress_percent": progress_percent,
            "progress_share": progress_percent / 100.0,
            "cutoff_days": cutoff_days,
            "current_score_percentile": current_percentile,
            "mean_score_percentile": _weighted_mean(
                score_percentiles,
                live_segment_days,
            ),
            "worst_score_percentile": (
                float(np.nanmin(observed_percentiles))
                if observed_percentiles.size
                else None
            ),
            "future_return": float(entry["future_return"]),
            "annualized_return": float(entry["annualized_return"]),
        }

        for window_share in ROLLING_WINDOW_SHARES:
            suffix = int(window_share * 100)
            window_days = horizon_days * window_share
            rolling_weights = _overlap_days(
                elapsed_days,
                segment_days,
                max(0.0, cutoff_days - window_days),
                cutoff_days,
            )
            row[f"rolling_mean_score_percentile_{suffix}"] = _weighted_mean(
                score_percentiles,
                rolling_weights,
            )

        for half_life_share in EWMA_HALFLIFE_SHARES:
            suffix = int(half_life_share * 100)
            ewma_weights = _ewma_time_weights(
                elapsed_days,
                segment_days,
                cutoff_days,
                horizon_days * half_life_share,
            )
            row[f"ewma_score_percentile_halflife_{suffix}"] = _weighted_mean(
                score_percentiles,
                ewma_weights,
            )

        rows.append(row)

    return rows


def _build_observations_and_paths(entries, history):
    observation_rows = []
    live_progress_rows = []
    path_frames = []

    for _, entry in entries.iterrows():
        path = _build_path_for_entry(entry, history)
        if path.empty:
            continue

        observation_rows.append(_summarize_entry_path(entry, path))
        live_progress_rows.extend(_summarize_live_progress(entry, path))
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
    return observations, path_points, pd.DataFrame(live_progress_rows)


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


def _build_live_progress_correlations_by_horizon(live_progress_observations):
    rows = []
    if live_progress_observations.empty:
        return pd.DataFrame()

    grouped = live_progress_observations.groupby(
        ["timeframe", "horizon_days", "progress_percent"],
        sort=False,
    )
    for (timeframe, horizon_days, progress_percent), group in grouped:
        for metric in LIVE_CORRELATION_METRICS:
            rows.append({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "progress_percent": int(progress_percent),
                "progress_share": progress_percent / 100.0,
                "cutoff_days": round_or_none(group["cutoff_days"].mean()),
                "metric": metric,
                "observation_count": int(
                    group[[metric, "annualized_return"]].dropna().shape[0]
                ),
                "pearson_to_annualized_return": _safe_corr(
                    group,
                    metric,
                    "pearson",
                ),
                "spearman_to_annualized_return": _safe_corr(
                    group,
                    metric,
                    "spearman",
                ),
            })

    return pd.DataFrame(rows)


def _build_live_progress_average(correlations_by_horizon):
    columns = [
        "timeframe",
        "progress_percent",
        "progress_share",
        "metric",
        "horizon_start",
        "horizon_end",
        "horizon_count",
        "mean_cutoff_days",
        "mean_observation_count",
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
    ]
    if correlations_by_horizon.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    grouped = correlations_by_horizon.groupby(
        ["timeframe", "progress_percent", "metric"],
        sort=False,
    )
    for (timeframe, progress_percent, metric), group in grouped:
        rows.append({
            "timeframe": timeframe,
            "progress_percent": int(progress_percent),
            "progress_share": progress_percent / 100.0,
            "metric": metric,
            "horizon_start": int(group["horizon_days"].min()),
            "horizon_end": int(group["horizon_days"].max()),
            "horizon_count": int(group["horizon_days"].nunique()),
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

    return pd.DataFrame(rows, columns=columns).sort_values(
        ["timeframe", "metric", "progress_percent"]
    ).reset_index(drop=True)


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
    observations, path_points, live_progress_observations = (
        _build_observations_and_paths(entries, history)
    )
    correlations_by_horizon = _build_correlations_by_horizon(observations)
    horizon_average = _build_horizon_average(correlations_by_horizon)
    live_progress_correlations_by_horizon = (
        _build_live_progress_correlations_by_horizon(live_progress_observations)
    )
    live_progress_average = _build_live_progress_average(
        live_progress_correlations_by_horizon
    )

    return {
        "observations": _round_numeric_columns(observations),
        "path_points": _round_numeric_columns(path_points),
        "correlations_by_horizon": _round_numeric_columns(correlations_by_horizon),
        "horizon_average": _round_numeric_columns(horizon_average),
        "live_progress_observations": _round_numeric_columns(
            live_progress_observations
        ),
        "live_progress_correlations_by_horizon": _round_numeric_columns(
            live_progress_correlations_by_horizon
        ),
        "live_progress_average": _round_numeric_columns(live_progress_average),
    }
