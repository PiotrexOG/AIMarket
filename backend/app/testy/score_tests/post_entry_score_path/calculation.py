import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import (
    CALENDAR_DAYS_PER_YEAR,
    annualize_return,
)
from app.testy.score_tests.common.metrics import round_or_none


ENTRY_MIN_SCORE_PERCENTILE = 0.60
PROGRESS_PERCENTAGES = tuple(range(5, 101, 5))

CORRELATION_METRICS = [
    "mean_score_percentile",
    "score_percentile_change",
    "relative_score_percentile_change",
]

LIVE_CORRELATION_METRICS = [
    "mean_score_percentile",
    "score_percentile_change",
    "relative_score_percentile_change",
]

WEEKLY_START_CORRELATION_METRICS = [
    "relative_score_percentile_change",
]

WEEKLY_START_RETURN_METRICS = [
    "annualized_return",
    "remaining_annualized_return",
    "annualized_alpha",
]


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


def _prepare_score_history(return_panel):
    columns = [
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "score_zscore",
        "current_price",
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
    horizon_end
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
    ranked["benchmark_return"] = ranked.groupby(
        ["timeframe", "horizon_days", "start_timestamp"]
    )["future_return"].transform("mean")
    ranked["annualized_benchmark_return"] = [
        annualize_return(total_return, horizon_days)
        for total_return, horizon_days in zip(
            ranked["benchmark_return"],
            ranked["horizon_days"],
        )
    ]
    ranked = ranked[
        ranked["score_percentile"] >= ENTRY_MIN_SCORE_PERCENTILE
    ].copy()
    ranked["annualized_return"] = [
        annualize_return(total_return, horizon_days)
        for total_return, horizon_days in zip(
            ranked["future_return"],
            ranked["horizon_days"],
        )
    ]
    ranked = ranked.dropna(subset=["annualized_return"])
    ranked["annualized_alpha"] = (
        ranked["annualized_return"] - ranked["annualized_benchmark_return"]
    )
    ranked["observation_id"] = (
        ranked.groupby(["timeframe", "horizon_days"]).cumcount() + 1
    )
    return ranked.reset_index(drop=True)


def _build_history_lookup(history):
    return {
        key: group.reset_index(drop=True)
        for key, group in history.groupby(
            ["timeframe", "ticker"],
            sort=False,
        )
    }


def _build_path_for_entry(entry, history_lookup):
    start_timestamp = pd.Timestamp(entry["start_timestamp"])
    end_timestamp = start_timestamp + pd.to_timedelta(
        int(entry["horizon_days"]),
        unit="D",
    )
    ticker_history = history_lookup.get(
        (entry["timeframe"], entry["ticker"])
    )
    if ticker_history is None:
        return pd.DataFrame()
    path = ticker_history[
        (ticker_history["start_timestamp"] >= start_timestamp)
        & (ticker_history["start_timestamp"] <= end_timestamp)
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

    mean_score_percentile = _weighted_mean(
        path["score_percentile"],
        segment_days,
    )
    score_percentile_drop = (
        float(entry["score_percentile"]) - mean_score_percentile
        if mean_score_percentile is not None
        else None
    )
    relative_score_percentile_drop = (
        score_percentile_drop / float(entry["score_percentile"])
        if score_percentile_drop is not None
        and float(entry["score_percentile"]) > 0
        else None
    )
    score_percentile_change = (
        -score_percentile_drop
        if score_percentile_drop is not None
        else None
    )
    relative_score_percentile_change = (
        -relative_score_percentile_drop
        if relative_score_percentile_drop is not None
        else None
    )

    row = {
        "timeframe": entry["timeframe"],
        "horizon_days": horizon_days,
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
        "benchmark_return": float(entry["benchmark_return"]),
        "annualized_benchmark_return": (
            float(entry["annualized_benchmark_return"])
            if pd.notna(entry["annualized_benchmark_return"])
            else None
        ),
        "annualized_alpha": (
            float(entry["annualized_alpha"])
            if pd.notna(entry["annualized_alpha"])
            else None
        ),
        "path_point_count": int(len(path)),
        "path_covered_days": covered_days,
        "path_covered_horizon_share": covered_days / horizon_days,
        "mean_score_percentile": mean_score_percentile,
        "score_percentile_drop": score_percentile_drop,
        "relative_score_percentile_drop": relative_score_percentile_drop,
        "score_percentile_change": score_percentile_change,
        "relative_score_percentile_change": relative_score_percentile_change,
    }

    return row


def _summarize_live_progress(entry, path):
    rows = []
    horizon_days = int(entry["horizon_days"])
    elapsed_days = path["elapsed_days"].to_numpy(dtype=float)
    segment_days = path["segment_days"].to_numpy(dtype=float)
    score_percentiles = path["score_percentile"].to_numpy(dtype=float)
    price_timestamps = pd.to_datetime(path["start_timestamp"])
    prices = path["current_price"].to_numpy(dtype=float)

    for progress_percent in PROGRESS_PERCENTAGES:
        cutoff_days = horizon_days * progress_percent / 100.0
        cutoff_timestamp = pd.Timestamp(
            entry["start_timestamp"]
        ) + pd.to_timedelta(cutoff_days, unit="D")
        live_segment_days = _overlap_days(
            elapsed_days,
            segment_days,
            0.0,
            cutoff_days,
        )
        entry_score_percentile = float(entry["score_percentile"])
        mean_score_percentile = _weighted_mean(
            score_percentiles,
            live_segment_days,
        )
        score_percentile_change = (
            mean_score_percentile - entry_score_percentile
            if mean_score_percentile is not None
            else None
        )
        relative_score_percentile_change = (
            score_percentile_change / entry_score_percentile
            if score_percentile_change is not None
            and entry_score_percentile > 0
            else None
        )
        price_mask = (
            (price_timestamps <= cutoff_timestamp)
            & np.isfinite(prices)
            & (prices > 0)
        )
        if price_mask.any():
            price_index = int(np.flatnonzero(price_mask)[-1])
            price_at_cutoff = float(prices[price_index])
            price_timestamp = price_timestamps.iloc[price_index]
            price_elapsed_days = float(elapsed_days[price_index])
        else:
            price_at_cutoff = None
            price_timestamp = pd.NaT
            price_elapsed_days = None

        remaining_days = horizon_days - cutoff_days
        remaining_return = (
            float(entry["future_price"]) / price_at_cutoff - 1.0
            if price_at_cutoff is not None
            else None
        )
        remaining_annualized_return = (
            annualize_return(remaining_return, remaining_days)
            if remaining_return is not None and remaining_days > 0
            else None
        )
        entry_price = float(entry["current_price"])
        price_change_to_cutoff = (
            price_at_cutoff / entry_price - 1.0
            if price_at_cutoff is not None and entry_price > 0
            else None
        )
        rows.append({
            "timeframe": entry["timeframe"],
            "horizon_days": horizon_days,
            "observation_id": int(entry["observation_id"]),
            "start_timestamp": entry["start_timestamp"],
            "future_timestamp": entry["future_timestamp"],
            "ticker": entry["ticker"],
            "progress_percent": progress_percent,
            "progress_share": progress_percent / 100.0,
            "cutoff_days": cutoff_days,
            "cutoff_timestamp": cutoff_timestamp,
            "entry_score_percentile": entry_score_percentile,
            "mean_score_percentile": mean_score_percentile,
            "score_percentile_change": score_percentile_change,
            "relative_score_percentile_change": (
                relative_score_percentile_change
            ),
            "price_at_cutoff": price_at_cutoff,
            "price_timestamp": price_timestamp,
            "price_elapsed_days": price_elapsed_days,
            "price_horizon_share": (
                price_elapsed_days / horizon_days
                if price_elapsed_days is not None
                else None
            ),
            "entry_price": entry_price,
            "price_change_to_cutoff": price_change_to_cutoff,
            "future_price": float(entry["future_price"]),
            "remaining_days": remaining_days,
            "remaining_return": remaining_return,
            "remaining_annualized_return": remaining_annualized_return,
            "future_return": float(entry["future_return"]),
            "annualized_return": float(entry["annualized_return"]),
            "benchmark_return": float(entry["benchmark_return"]),
            "annualized_benchmark_return": (
                float(entry["annualized_benchmark_return"])
                if pd.notna(entry["annualized_benchmark_return"])
                else None
            ),
            "annualized_alpha": (
                float(entry["annualized_alpha"])
                if pd.notna(entry["annualized_alpha"])
                else None
            ),
        })

    return rows


def _build_observations_and_paths(entries, history):
    observation_rows = []
    live_progress_rows = []
    path_frames = []

    history_lookup = _build_history_lookup(history)
    for _, entry in entries.iterrows():
        path = _build_path_for_entry(entry, history_lookup)
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
        path["benchmark_return"] = float(entry["benchmark_return"])
        path["annualized_benchmark_return"] = (
            float(entry["annualized_benchmark_return"])
            if pd.notna(entry["annualized_benchmark_return"])
            else None
        )
        path["annualized_alpha"] = (
            float(entry["annualized_alpha"])
            if pd.notna(entry["annualized_alpha"])
            else None
        )
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


def _build_weekly_start_correlations(live_progress_observations):
    columns = [
        "timeframe",
        "start_week",
        "week_end",
        "progress_percent",
        "progress_share",
        "metric",
        "return_metric",
        "observation_count",
        "pearson",
        "spearman",
        "mean_metric_value",
        "mean_return_value",
        "mean_annualized_benchmark_return",
        "below_benchmark_share",
    ]
    if live_progress_observations.empty:
        return pd.DataFrame(columns=columns)

    data = live_progress_observations.copy()
    data["start_week"] = (
        pd.to_datetime(data["start_timestamp"])
        .dt.to_period("W-SUN")
        .dt.start_time
    )
    data["week_end"] = data["start_week"] + pd.Timedelta(days=6)
    rows = []
    grouped = data.groupby(
        ["timeframe", "start_week", "progress_percent"],
        sort=True,
    )
    available_return_metrics = [
        metric
        for metric in WEEKLY_START_RETURN_METRICS
        if metric in data.columns
    ]

    for (timeframe, start_week, progress_percent), group in grouped:
        for metric in WEEKLY_START_CORRELATION_METRICS:
            if metric not in group.columns:
                continue
            for return_metric in available_return_metrics:
                clean = group[[metric, return_metric]].replace(
                    [np.inf, -np.inf],
                    np.nan,
                ).dropna()
                rows.append({
                    "timeframe": timeframe,
                    "start_week": pd.Timestamp(start_week),
                    "week_end": pd.Timestamp(start_week) + pd.Timedelta(days=6),
                    "progress_percent": int(progress_percent),
                    "progress_share": progress_percent / 100.0,
                    "metric": metric,
                    "return_metric": return_metric,
                    "observation_count": int(len(clean)),
                    "pearson": _safe_corr_pair(
                        group,
                        metric,
                        return_metric,
                        "pearson",
                    ),
                    "spearman": _safe_corr_pair(
                        group,
                        metric,
                        return_metric,
                        "spearman",
                    ),
                    "mean_metric_value": round_or_none(clean[metric].mean()),
                    "mean_return_value": round_or_none(
                        clean[return_metric].mean()
                    ),
                    "mean_annualized_benchmark_return": round_or_none(
                        group["annualized_benchmark_return"].mean()
                    )
                    if "annualized_benchmark_return" in group.columns
                    else None,
                    "below_benchmark_share": round_or_none(
                        (group["annualized_alpha"] < 0).mean()
                    )
                    if "annualized_alpha" in group.columns
                    else None,
                })

    return pd.DataFrame(rows, columns=columns).sort_values(
        ["timeframe", "metric", "return_metric", "progress_percent", "start_week"]
    ).reset_index(drop=True)


def _fit_drop_regression(group):
    columns = [
        "entry_score_percentile",
        "score_percentile_drop",
        "annualized_return",
    ]
    clean = group[columns].replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 8:
        return None

    entry = clean["entry_score_percentile"].to_numpy(dtype=float)
    drop = clean["score_percentile_drop"].to_numpy(dtype=float)
    response = clean["annualized_return"].to_numpy(dtype=float)
    design = np.column_stack([
        np.ones(len(clean)),
        entry,
        drop,
        entry * drop,
    ])
    if np.linalg.matrix_rank(design) < design.shape[1]:
        return None

    coefficients, _, _, _ = np.linalg.lstsq(design, response, rcond=None)
    fitted = design @ coefficients
    residual_sum_squares = float(np.sum((response - fitted) ** 2))
    total_sum_squares = float(np.sum((response - response.mean()) ** 2))
    r_squared = (
        1.0 - residual_sum_squares / total_sum_squares
        if total_sum_squares > 0
        else None
    )
    return {
        "observation_count": int(len(clean)),
        "intercept": float(coefficients[0]),
        "entry_score_percentile_coefficient": float(coefficients[1]),
        "score_percentile_drop_coefficient": float(coefficients[2]),
        "entry_drop_interaction_coefficient": float(coefficients[3]),
        "r_squared": r_squared,
    }


def _build_drop_regressions_by_horizon(observations):
    rows = []
    if observations.empty:
        return pd.DataFrame()

    for (timeframe, horizon_days), group in observations.groupby(
        ["timeframe", "horizon_days"],
        sort=False,
    ):
        regression = _fit_drop_regression(group)
        if regression is None:
            continue
        rows.append({
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
            **regression,
        })
    return pd.DataFrame(rows)


def _build_drop_regression_average(regressions):
    columns = [
        "timeframe",
        "horizon_start",
        "horizon_end",
        "horizon_count",
        "mean_observation_count",
        "mean_intercept",
        "mean_entry_score_percentile_coefficient",
        "mean_score_percentile_drop_coefficient",
        "score_drop_negative_coefficient_share",
        "mean_entry_drop_interaction_coefficient",
        "mean_r_squared",
    ]
    if regressions.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for timeframe, group in regressions.groupby("timeframe", sort=False):
        drop_coefficients = group["score_percentile_drop_coefficient"].dropna()
        rows.append({
            "timeframe": timeframe,
            "horizon_start": int(group["horizon_days"].min()),
            "horizon_end": int(group["horizon_days"].max()),
            "horizon_count": int(group["horizon_days"].nunique()),
            "mean_observation_count": group["observation_count"].mean(),
            "mean_intercept": group["intercept"].mean(),
            "mean_entry_score_percentile_coefficient": (
                group["entry_score_percentile_coefficient"].mean()
            ),
            "mean_score_percentile_drop_coefficient": (
                drop_coefficients.mean()
            ),
            "score_drop_negative_coefficient_share": (
                (drop_coefficients < 0).mean()
                if not drop_coefficients.empty
                else None
            ),
            "mean_entry_drop_interaction_coefficient": (
                group["entry_drop_interaction_coefficient"].mean()
            ),
            "mean_r_squared": group["r_squared"].mean(),
        })
    return pd.DataFrame(rows, columns=columns)


def _round_numeric_columns(df):
    if df.empty:
        return df
    result = df.copy()
    for column in result.select_dtypes(include=[np.number]).columns:
        if column not in {
            "horizon_days",
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
    horizon_start,
    horizon_end
):
    history = _prepare_score_history(context.return_panel)
    entries = _prepare_top_entry_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
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
    weekly_start_correlations = _build_weekly_start_correlations(
        live_progress_observations
    )
    drop_regressions_by_horizon = _build_drop_regressions_by_horizon(
        observations
    )
    drop_regression_average = _build_drop_regression_average(
        drop_regressions_by_horizon
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
        "weekly_start_correlations": _round_numeric_columns(
            weekly_start_correlations
        ),
        "drop_regressions_by_horizon": _round_numeric_columns(
            drop_regressions_by_horizon
        ),
        "drop_regression_average": _round_numeric_columns(
            drop_regression_average
        ),
    }
