import numpy as np
import pandas as pd

from .plot_config import Z_CRITICAL_95


def _safe_correlation(group, x_column, y_column, method):
    clean = group[[x_column, y_column]].dropna()
    if len(clean) < 3:
        return np.nan
    if (
        clean[x_column].nunique() < 2
        or clean[y_column].nunique() < 2
    ):
        return np.nan
    return clean[x_column].corr(clean[y_column], method=method)


def _newey_west_mean_stats(values, lags):
    clean = pd.Series(values, dtype=float).dropna()
    observation_count = int(len(clean))
    if observation_count < 2:
        return {
            "mean_ic": clean.mean() if observation_count else np.nan,
            "naive_standard_error": np.nan,
            "newey_west_standard_error": np.nan,
            "ci_lower_95": np.nan,
            "ci_upper_95": np.nan,
            "effective_observations": np.nan,
        }

    selected_lags = max(0, min(int(lags), observation_count - 1))
    residuals = clean.to_numpy(dtype=float) - float(clean.mean())
    gamma_zero = float(np.dot(residuals, residuals) / observation_count)
    long_run_variance = gamma_zero
    for lag in range(1, selected_lags + 1):
        weight = 1.0 - lag / (selected_lags + 1.0)
        autocovariance = float(
            np.dot(residuals[lag:], residuals[:-lag]) / observation_count
        )
        long_run_variance += 2.0 * weight * autocovariance

    sample_std = float(clean.std(ddof=1))
    naive_standard_error = sample_std / np.sqrt(observation_count)
    long_run_variance = max(long_run_variance, 0.0)
    newey_west_standard_error = np.sqrt(long_run_variance / observation_count)
    reported_standard_error = max(
        naive_standard_error,
        newey_west_standard_error,
    )
    z_critical = Z_CRITICAL_95
    mean_ic = float(clean.mean())
    if reported_standard_error > 0:
        effective_observations = observation_count * (
            naive_standard_error / reported_standard_error
        ) ** 2
    else:
        effective_observations = np.nan

    return {
        "mean_ic": mean_ic,
        "naive_standard_error": naive_standard_error,
        "newey_west_standard_error": newey_west_standard_error,
        "reported_standard_error": reported_standard_error,
        "ci_lower_95": mean_ic - z_critical * reported_standard_error,
        "ci_upper_95": mean_ic + z_critical * reported_standard_error,
        "raw_newey_west_ci_lower_95": (
            mean_ic - z_critical * newey_west_standard_error
        ),
        "raw_newey_west_ci_upper_95": (
            mean_ic + z_critical * newey_west_standard_error
        ),
        "effective_observations": effective_observations,
    }


def _autocorrelation_by_lag(values, max_lag):
    clean = pd.Series(values, dtype=float).dropna().reset_index(drop=True)
    max_lag = max(0, min(int(max_lag), len(clean) - 2))
    rows = []
    for lag in range(1, max_lag + 1):
        correlation = clean.autocorr(lag=lag)
        rows.append({
            "lag": lag,
            "autocorrelation": correlation,
        })
    return pd.DataFrame(rows)


def _score_return_horizon_metadata(data, correlations):
    starts = (
        data["horizon_week_start"].dropna()
        if "horizon_week_start" in data.columns
        else pd.Series(dtype=float)
    )
    ends = (
        data["horizon_week_end"].dropna()
        if "horizon_week_end" in data.columns
        else pd.Series(dtype=float)
    )
    first_timestamp = correlations["timestamp"].min()
    last_timestamp = correlations["timestamp"].max()
    gaps = (
        correlations["timestamp"]
        .sort_values()
        .diff()
        .dropna()
        .dt.total_seconds()
        / 86400.0
    )
    horizon_week_start = int(starts.min()) if not starts.empty else np.nan
    horizon_week_end = int(ends.max()) if not ends.empty else np.nan
    return {
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "median_observation_gap_days": float(gaps.median())
        if not gaps.empty
        else np.nan,
        "horizon_week_start": horizon_week_start,
        "horizon_week_end": horizon_week_end,
    }


def _newey_west_lags_from_horizon(metadata, observation_count):
    horizon_week_end = metadata["horizon_week_end"]
    if pd.isna(horizon_week_end):
        automatic_lags = int(np.floor(4 * (observation_count / 100) ** (2 / 9)))
        return max(0, min(observation_count - 1, automatic_lags))
    structural_lags = int(horizon_week_end) - 1
    return max(0, min(structural_lags, observation_count - 1))


def _score_return_horizon_correlations(horizon_points):
    required = {
        "timestamp",
        "score",
        "score_percentile",
        "forward_annualized_return",
        "forward_return_percentile",
        "horizon_weeks",
        "horizon_days",
    }
    if horizon_points is None or horizon_points.empty:
        return pd.DataFrame()
    if not required.issubset(horizon_points.columns):
        return pd.DataFrame()

    clean = horizon_points.dropna(subset=list(required)).copy()
    if clean.empty:
        return pd.DataFrame()

    rows = []
    for (horizon_weeks, timestamp), group in clean.groupby(
        ["horizon_weeks", "timestamp"],
        sort=True,
    ):
        rows.append({
            "horizon_weeks": int(horizon_weeks),
            "horizon_days": float(group["horizon_days"].mean()),
            "timestamp": timestamp,
            "pearson": _safe_correlation(
                group,
                "score",
                "forward_annualized_return",
                "pearson",
            ),
            "spearman": _safe_correlation(
                group,
                "score_percentile",
                "forward_return_percentile",
                "spearman",
            ),
            "score_percentile_pearson_ic": _safe_correlation(
                group,
                "score_percentile",
                "forward_annualized_return",
                "pearson",
            ),
            "benchmark_annualized_return": (
                group["forward_annualized_return"].mean()
            ),
        })

    correlations = pd.DataFrame(rows)
    return correlations.dropna(subset=["pearson"]).sort_values(
        ["horizon_weeks", "timestamp"]
    )


def _score_return_horizon_hac_summary(correlations, timeframe):
    metrics = [
        ("pearson", "Pearson IC"),
        ("spearman", "Spearman IC"),
        ("score_percentile_pearson_ic", "Pearson IC percentyla score"),
    ]
    summary_rows = []
    autocorrelation_frames = []
    z_critical = Z_CRITICAL_95

    for horizon_weeks, horizon_group in correlations.groupby(
        "horizon_weeks",
        sort=True,
    ):
        observation_count = int(len(horizon_group))
        newey_west_lags = max(
            0,
            min(int(horizon_weeks) - 1, observation_count - 1),
        )
        first_timestamp = horizon_group["timestamp"].min()
        last_timestamp = horizon_group["timestamp"].max()
        gaps = (
            horizon_group["timestamp"]
            .sort_values()
            .diff()
            .dropna()
            .dt.total_seconds()
            / 86400.0
        )
        for column, label in metrics:
            if column not in horizon_group.columns:
                continue
            stats = _newey_west_mean_stats(
                horizon_group[column],
                newey_west_lags,
            )
            summary_rows.append({
                "timeframe": timeframe,
                "metric": column,
                "metric_label": label,
                "horizon_weeks": int(horizon_weeks),
                "horizon_days": float(horizon_group["horizon_days"].mean()),
                "aggregation_method": "per_horizon_max_available_dates",
                "official_result": False,
                "mean_ic": stats["mean_ic"],
                "naive_standard_error": stats["naive_standard_error"],
                "newey_west_standard_error": stats[
                    "newey_west_standard_error"
                ],
                "reported_standard_error": stats["reported_standard_error"],
                "ci_lower_95": stats["ci_lower_95"],
                "ci_upper_95": stats["ci_upper_95"],
                "raw_newey_west_ci_lower_95": stats[
                    "raw_newey_west_ci_lower_95"
                ],
                "raw_newey_west_ci_upper_95": stats[
                    "raw_newey_west_ci_upper_95"
                ],
                "observations": observation_count,
                "horizon_count": 1,
                "effective_observations": stats["effective_observations"],
                "newey_west_lags": newey_west_lags,
                "lag_selection": "horizon_weeks_minus_1_capped_by_sample",
                "reported_standard_error_rule": "max_naive_or_newey_west",
                "first_timestamp": first_timestamp,
                "last_timestamp": last_timestamp,
                "median_observation_gap_days": float(gaps.median())
                if not gaps.empty
                else np.nan,
                "confidence_level": 0.95,
                "critical_value_type": "normal_approximation",
            })
            autocorrelation = _autocorrelation_by_lag(
                horizon_group[column],
                newey_west_lags,
            )
            if not autocorrelation.empty:
                autocorrelation["timeframe"] = timeframe
                autocorrelation["horizon_weeks"] = int(horizon_weeks)
                autocorrelation["metric"] = column
                autocorrelation["metric_label"] = label
                autocorrelation_frames.append(autocorrelation)

    summary = pd.DataFrame(summary_rows)
    if summary.empty:
        return summary, pd.DataFrame()

    official_rows = []
    for (metric, metric_label), group in summary.groupby(
        ["metric", "metric_label"],
        sort=False,
    ):
        mean_ic = float(group["mean_ic"].mean())
        newey_west_standard_error = float(
            group["newey_west_standard_error"].mean()
        )
        reported_standard_error = float(
            group["reported_standard_error"].mean()
        )
        official_rows.append({
            "timeframe": timeframe,
            "metric": metric,
            "metric_label": metric_label,
            "horizon_weeks": np.nan,
            "horizon_days": float(group["horizon_days"].mean()),
            "aggregation_method": "mean_across_horizon_hac_estimates",
            "official_result": True,
            "mean_ic": mean_ic,
            "naive_standard_error": float(group["naive_standard_error"].mean()),
            "newey_west_standard_error": newey_west_standard_error,
            "reported_standard_error": reported_standard_error,
            "ci_lower_95": mean_ic - z_critical * reported_standard_error,
            "ci_upper_95": mean_ic + z_critical * reported_standard_error,
            "raw_newey_west_ci_lower_95": (
                mean_ic - z_critical * newey_west_standard_error
            ),
            "raw_newey_west_ci_upper_95": (
                mean_ic + z_critical * newey_west_standard_error
            ),
            "observations": int(group["observations"].sum()),
            "horizon_count": int(group["horizon_weeks"].nunique()),
            "effective_observations": float(
                group["effective_observations"].mean()
            ),
            "newey_west_lags": float(group["newey_west_lags"].mean()),
            "lag_selection": "mean_of_per_horizon_lags",
            "reported_standard_error_rule": "mean_per_horizon_reported_se",
            "first_timestamp": group["first_timestamp"].min(),
            "last_timestamp": group["last_timestamp"].max(),
            "median_observation_gap_days": float(
                group["median_observation_gap_days"].mean()
            ),
            "confidence_level": 0.95,
            "critical_value_type": "normal_approximation",
        })

    summary = pd.concat(
        [summary, pd.DataFrame(official_rows)],
        ignore_index=True,
    )
    autocorrelations = (
        pd.concat(autocorrelation_frames, ignore_index=True)
        if autocorrelation_frames
        else pd.DataFrame()
    )
    return summary, autocorrelations


def _official_result_mask(summary):
    official_result = summary["official_result"]
    if pd.api.types.is_bool_dtype(official_result):
        return official_result.fillna(False)
    return official_result.astype(str).str.lower().isin({"true", "1", "yes"})


def _format_ci_half_width(standard_error):
    if pd.isna(standard_error):
        return "n/a"
    return f"+/-{Z_CRITICAL_95 * float(standard_error):.3f}"


def _metric_horizon_summary(summary, metric):
    official_mask = _official_result_mask(summary)
    metric_summary = summary[
        (summary["metric"] == metric)
        & (~official_mask)
    ].copy()
    if metric_summary.empty:
        return metric_summary
    return metric_summary.dropna(subset=["horizon_weeks", "mean_ic"]).sort_values(
        "horizon_weeks"
    )


def _metric_official_summary(summary, metric):
    official_mask = _official_result_mask(summary)
    official = summary[
        (summary["metric"] == metric)
        & official_mask
    ]
    return official.iloc[0] if not official.empty else None
