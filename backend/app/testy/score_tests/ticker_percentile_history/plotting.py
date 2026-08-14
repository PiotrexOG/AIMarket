import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import plot_path, timeframe_label
from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.annualization import annualize_return
from app.testy.score_tests.common.output_paths import (
    TICKER_ANTI_MOMENTUM_SECTION,
    TICKER_FORWARD_RETURN_REFERENCE_SECTION,
    TICKER_INFORMATION_COEFFICIENT_SECTION,
    TICKER_MODEL_VS_MOMENTUM_SECTION,
    TICKER_PEARSON_ZSCORE_SECTION,
    TICKER_PERCENTILE_HISTORY_DIR,
    TICKER_RETURN_ATTRIBUTION_SECTION,
    TICKER_SCORE_PATHS_SECTION,
    TICKER_SPEARMAN_PERCENTILE_SECTION,
)


MOVING_AVERAGE_COLUMN = "moving_average_score_percentile"
DEFAULT_MOVING_AVERAGE_WINDOW = 4
ANTI_MOMENTUM_SKIP_WEEKS = 4
Z_CRITICAL_95 = 1.959963984540054
HAC_DIAGNOSTIC_METRICS = [
    {
        "metric": "pearson",
        "label": "Pearson IC",
        "short_label": "Pearson",
        "color": "#4C78A8",
        "filename_stem": "pearson",
    },
    {
        "metric": "spearman",
        "label": "Spearman IC",
        "short_label": "Spearman",
        "color": "#59A14F",
        "filename_stem": "spearman",
    },
    {
        "metric": "score_percentile_pearson_ic",
        "label": "Pearson IC percentyla score",
        "short_label": "Pearson percentyla score",
        "color": "#F28E2B",
        "filename_stem": "score_percentile_pearson",
    },
]
ANTI_MOMENTUM_WINDOWS = [
    ("jegadeesh_titman", None, None, ANTI_MOMENTUM_SKIP_WEEKS),
]


def _safe_filename(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._") or "unknown"


def _to_utc_naive(values):
    return pd.to_datetime(values, utc=True).dt.tz_localize(None)


def _save_figure(fig, path, **kwargs):
    try:
        fig.savefig(path, **kwargs)
        return path
    except OSError as error:
        if getattr(error, "errno", None) != 22:
            raise
        fallback_path = path.with_name(f"{path.stem}_latest{path.suffix}")
        fig.savefig(fallback_path, **kwargs)
        return fallback_path


def _save_heatmap_csv(heatmap_data, output_dir, directory, filename):
    csv_filename = f"{Path(filename).stem}.csv"
    csv_data = heatmap_data.reset_index()
    save_csv_for_excel(csv_data, plot_path(output_dir, directory, csv_filename))


def _save_combined_plot(
    metric_group,
    price_group,
    ticker,
    timeframe,
    directory,
    output_dir,
    moving_average_window,
):
    percentile_color = "#4C78A8"
    moving_average_color = "#59A14F"
    price_color = "#E15759"

    fig, percentile_ax = plt.subplots(figsize=(13, 7))
    price_ax = percentile_ax.twinx()

    percentile_line = percentile_ax.plot(
        metric_group["timestamp"],
        metric_group["current_score_percentile"],
        color=percentile_color,
        linewidth=2.2,
        label="Surowy percentyl score",
    )[0]
    moving_average_line = None
    if MOVING_AVERAGE_COLUMN in metric_group.columns:
        moving_average_values = metric_group[MOVING_AVERAGE_COLUMN]
        if moving_average_values.notna().any():
            moving_average_line = percentile_ax.plot(
                metric_group["timestamp"],
                moving_average_values,
                color=moving_average_color,
                linewidth=2.4,
                linestyle="--",
                label=(
                    f"{moving_average_window}-punktowa średnia krocząca "
                    "percentyla score"
                ),
            )[0]
    price_line = price_ax.plot(
        price_group["timestamp"],
        price_group["close"],
        color=price_color,
        linewidth=2,
        alpha=0.85,
        label="Cena zamknięcia",
    )[0]

    percentile_ax.set_title(
        f"{ticker}: percentyl score, średnia krocząca i cena "
        f"zamknięcia ({timeframe_label(timeframe)})"
    )
    percentile_ax.set_xlabel("Data")
    percentile_ax.set_ylabel("Percentyl score", color=percentile_color)
    percentile_ax.set_ylim(0, 1)
    percentile_ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    percentile_ax.tick_params(axis="y", colors=percentile_color)
    percentile_ax.grid(True, alpha=0.25)

    price_ax.set_ylabel("Cena zamknięcia", color=price_color)
    price_ax.tick_params(axis="y", colors=price_color)
    legend_handles = [percentile_line, price_line]
    if moving_average_line is not None:
        legend_handles.insert(1, moving_average_line)
    percentile_ax.legend(
        handles=legend_handles,
        loc="best",
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, f"{ticker}_score_percentile_with_price.png"),
        dpi=180,
    )
    plt.close(fig)


def _calculate_full_period_returns(timeframe_score_points, prices):
    if prices is None or prices.empty:
        return pd.Series(dtype=float)

    returns = {}
    start = timeframe_score_points["timestamp"].min()
    end = timeframe_score_points["timestamp"].max()
    for ticker in sorted(timeframe_score_points["ticker"].dropna().unique()):
        ticker_prices = prices[prices["ticker"] == ticker].sort_values("timestamp")
        ticker_prices = ticker_prices[ticker_prices["timestamp"].between(start, end)]
        closes = ticker_prices["close"].dropna()
        if len(closes) < 2 or closes.iloc[0] == 0:
            continue
        returns[ticker] = float(closes.iloc[-1] / closes.iloc[0] - 1)
    return pd.Series(returns, dtype=float)


def _save_all_tickers_moving_average_heatmap(
    timeframe_score_points,
    prices,
    timeframe,
    directory,
    output_dir,
    moving_average_window,
):
    if MOVING_AVERAGE_COLUMN not in timeframe_score_points.columns:
        return

    timeframe_score_points = timeframe_score_points.dropna(
        subset=["ticker", "timestamp", MOVING_AVERAGE_COLUMN]
    )
    if timeframe_score_points.empty:
        return

    heatmap_data = timeframe_score_points.pivot_table(
        index="ticker",
        columns="timestamp",
        values=MOVING_AVERAGE_COLUMN,
        aggfunc="last",
    ).sort_index(axis=1)
    if heatmap_data.empty:
        return

    full_returns = _calculate_full_period_returns(timeframe_score_points, prices)
    sorted_tickers = list(full_returns.sort_values(ascending=False).index)
    sorted_tickers.extend(
        ticker
        for ticker in sorted(heatmap_data.index)
        if ticker not in set(sorted_tickers)
    )
    heatmap_data = heatmap_data.reindex(sorted_tickers)
    _save_heatmap_csv(
        heatmap_data,
        output_dir,
        directory,
        "all_tickers_score_percentile_ma_by_full_return_heatmap.png",
    )

    fig, (heatmap_ax, return_ax, colorbar_ax) = plt.subplots(
        1,
        3,
        figsize=(16, 9),
        gridspec_kw={"width_ratios": [14, 2.4, 0.45]},
    )
    cmap = plt.cm.get_cmap("RdYlGn").copy()
    cmap.set_bad("#F2F2F2")
    image = heatmap_ax.imshow(
        heatmap_data.to_numpy(dtype=float),
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        vmin=0,
        vmax=1,
    )

    y_positions = np.arange(len(heatmap_data.index))
    heatmap_ax.set_yticks(y_positions)
    heatmap_ax.set_yticklabels(heatmap_data.index)
    heatmap_ax.set_ylabel("Ticker, sortowanie według zwrotu z całego okresu")
    heatmap_ax.set_xlabel("Data scoringu")
    heatmap_ax.set_title(
        f"{moving_average_window}-punktowa średnia krocząca percentyla score "
        f"({timeframe_label(timeframe)})"
    )

    date_count = len(heatmap_data.columns)
    tick_count = min(10, date_count)
    tick_positions = (
        np.linspace(0, date_count - 1, tick_count, dtype=int)
        if date_count
        else np.array([], dtype=int)
    )
    heatmap_ax.set_xticks(tick_positions)
    heatmap_ax.set_xticklabels(
        [heatmap_data.columns[position].strftime("%Y-%m-%d") for position in tick_positions],
        rotation=45,
        ha="right",
    )
    heatmap_ax.set_xticks(np.arange(-0.5, date_count, 1), minor=True)
    heatmap_ax.set_yticks(np.arange(-0.5, len(heatmap_data.index), 1), minor=True)
    heatmap_ax.grid(which="minor", color="white", linewidth=0.45)
    heatmap_ax.tick_params(which="minor", bottom=False, left=False)

    ordered_returns = full_returns.reindex(heatmap_data.index)
    return_colors = np.where(ordered_returns >= 0, "#59A14F", "#E15759")
    return_ax.barh(y_positions, ordered_returns, color=return_colors, alpha=0.9)
    return_ax.axvline(0, color="#444444", linewidth=1)
    return_ax.set_title("Zwrot w całym okresie")
    return_ax.set_xlabel("Stopa zwrotu")
    return_ax.set_ylim(len(heatmap_data.index) - 0.5, -0.5)
    return_ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    return_ax.tick_params(axis="y", left=False, labelleft=False)
    return_ax.grid(True, axis="x", alpha=0.25)

    colorbar = fig.colorbar(image, cax=colorbar_ax)
    colorbar.set_label("Średnia krocząca percentyla score")
    colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "all_tickers_score_percentile_ma_by_full_return_heatmap.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


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


def _save_score_return_hac_summary_plot(summary, timeframe, directory, output_dir):
    horizon_summary = summary[~_official_result_mask(summary)].dropna(
        subset=["horizon_weeks"]
    )
    if horizon_summary.empty:
        return

    x_values = np.sort(horizon_summary["horizon_weeks"].unique().astype(float))
    x_min = float(x_values.min())
    x_max = float(x_values.max())

    fig, ax = plt.subplots(figsize=(13, 6.8))
    official_annotations = []
    for config in HAC_DIAGNOSTIC_METRICS:
        metric_summary = _metric_horizon_summary(summary, config["metric"])
        if metric_summary.empty:
            continue

        yerr = [
            (
                metric_summary["mean_ic"]
                - metric_summary["ci_lower_95"]
            ).clip(lower=0),
            (
                metric_summary["ci_upper_95"]
                - metric_summary["mean_ic"]
            ).clip(lower=0),
        ]
        ax.errorbar(
            metric_summary["horizon_weeks"],
            metric_summary["mean_ic"],
            yerr=yerr,
            color=config["color"],
            ecolor=config["color"],
            elinewidth=1.1,
            alpha=0.92,
            linewidth=2,
            marker="o",
            markersize=4,
            capsize=3,
            label=f"{config['label']} według horyzontu",
        )

        official = _metric_official_summary(summary, config["metric"])
        if official is None:
            continue
        ax.axhline(
            official["mean_ic"],
            color=config["color"],
            linewidth=1.5,
            linestyle="--",
            alpha=0.85,
        )
        if (
            pd.notna(official["ci_lower_95"])
            and pd.notna(official["ci_upper_95"])
        ):
            ax.fill_between(
                [x_min, x_max],
                official["ci_lower_95"],
                official["ci_upper_95"],
                color=config["color"],
                alpha=0.08,
            )
            official_annotations.append(
                f"{config['short_label']}: średnia oficjalna "
                f"{official['mean_ic']:.3f}, 95% przedział "
                f"[{official['ci_lower_95']:.3f}, "
                f"{official['ci_upper_95']:.3f}]"
            )

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_ylim(0, 0.5)
    ax.set_xticks(x_values)
    ax.set_xticklabels([str(int(value)).replace("w", "") for value in x_values])
    ax.set_title(
        f"IC score względem przyszłej stopy zwrotu oraz "
        f"przedziały HAC według horyzontu ({timeframe_label(timeframe)})"
    )
    ax.set_xlabel("Horyzont przyszłej stopy zwrotu [tygodnie]")
    ax.set_ylabel("Średni IC")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    if official_annotations:
        ax.text(
            0.99,
            0.98,
            "\n".join(official_annotations),
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": "#DDDDDD",
                "alpha": 0.96,
            },
        )

    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_hac_diagnostics.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)



def _format_ci_half_width_clean(val):
    """Pomocnicza funkcja formatująca precyzję do 2 miejsc po przecinku bez symboli +/-."""
    if val is None or np.isnan(val):
        return "n/a"
    try:
        val_float = float(val)
        return f"{val_float:.2f}"
    except (ValueError, TypeError):
        return "n/a"


import matplotlib.pyplot as plt
import numpy as np


def _format_ci_half_width_clean(val):
    """Pomocnicza funkcja formatująca precyzję do 2 miejsc po przecinku bez symboli +/-."""
    if val is None or np.isnan(val):
        return "n/a"
    try:
        val_float = float(val * 1.96)
        return f"{val_float:.3f}"
    except (ValueError, TypeError):
        return "n/a"


def _save_score_return_autocorrelation_plot(
    autocorrelations,
    summary,
    timeframe,
    directory,
    output_dir,
    config,
):
    metric_acf = autocorrelations[
        autocorrelations["metric"] == config["metric"]
    ]
    if metric_acf.empty:
        return

    heatmap = (
        metric_acf.pivot_table(
            index="lag",
            columns="horizon_weeks",
            values="autocorrelation",
            aggfunc="mean",
        )
        .sort_index()
        .sort_index(axis=1)
    )
    if heatmap.empty:
        return

    metric_summary = _metric_horizon_summary(summary, config["metric"])
    summary_by_horizon = {}
    if not metric_summary.empty:
        for row in metric_summary.itertuples(index=False):
            summary_by_horizon[int(round(float(row.horizon_weeks)))] = row

    horizons = [int(round(float(h))) for h in heatmap.columns]

    se_values = []
    hac_values = []

    for horizon in horizons:
        stats = summary_by_horizon.get(horizon)
        if stats is None:
            se_values.append("n/a")
            hac_values.append("n/a")
        else:
            se_values.append(
                _format_ci_half_width_clean(
                    getattr(stats, "naive_standard_error", None)
                )
            )
            hac_values.append(
                _format_ci_half_width_clean(
                    getattr(stats, "newey_west_standard_error", None)
                )
            )

    fig_width = max(12, len(horizons) * 0.85)
    fig_height = max(7, min(10, 5.0 + len(heatmap.index) * 0.08))

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    image = ax.imshow(
        heatmap.to_numpy(dtype=float),
        aspect="auto",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        origin="lower",
    )

    # 1. Przewracamy standardowe podpisanie osi X (horyzonty)
    ax.set_xticks(np.arange(len(horizons)))
    ax.set_xticklabels(
        [f"{h}w" for h in horizons],
        fontsize=9,
    )
    # 2. Standardowy opis osi X
    ax.set_xlabel(
        "Horyzont przyszłej stopy zwrotu [tygodnie]",
        fontsize=10,
        labelpad=8,
    )

    # Pozycjonowanie osi Y
    y_tick_step = max(1, int(np.ceil(len(heatmap.index) / 14)))
    y_tick_positions = np.arange(0, len(heatmap.index), y_tick_step)

    if y_tick_positions[-1] != len(heatmap.index) - 1:
        y_tick_positions = np.append(
            y_tick_positions,
            len(heatmap.index) - 1,
        )

    ax.set_yticks(y_tick_positions)
    ax.set_yticklabels([
        str(int(heatmap.index[position])) for position in y_tick_positions
    ])

    # Colorbar
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Autokorelacja", fontsize=10)

    # Opisy osi Y i tytuł
    ax.set_ylabel("Opóźnienie", fontsize=10)
    ax.set_title(
        f"Autokorelacja {config['label']} według horyzontu i opóźnienia "
        f"({timeframe_label(timeframe)})"
    )

    # 3. Tabela umieszczona pod podpisem osi X – BEZ nagłówków kolumn (colLabels=None)
    table = ax.table(
        cellText=[
            se_values,
            hac_values,
        ],
        rowLabels=[
            "Przedział 95% (+/-)",
            "HAC 95% (+/-)",
        ],
        colLabels=None,  # Brak górnego wiersza z horyzontami
        cellLoc="center",
        rowLoc="right",
        loc="bottom",
        bbox=[0.0, -0.22, 1.0, 0.10],  # Pozycja poniżej opisu osi X
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)

    # Dopasowanie układu
    plt.tight_layout()

    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            (
                "score_return_correlation_"
                f"{config['filename_stem']}_autocorrelation_by_horizon_lag.png"
            ),
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_score_return_autocorrelation_plots(
    autocorrelations,
    summary,
    timeframe,
    directory,
    output_dir,
):
    if autocorrelations.empty:
        return
    for config in HAC_DIAGNOSTIC_METRICS:
        _save_score_return_autocorrelation_plot(
            autocorrelations,
            summary,
            timeframe,
            directory,
            output_dir,
            config,
        )


def _save_score_return_hac_diagnostics(
    correlations,
    data,
    timeframe,
    directory,
    output_dir,
    horizon_points=None,
):
    if correlations.empty:
        return pd.DataFrame()

    horizon_correlations = _score_return_horizon_correlations(horizon_points)
    summary, autocorrelations = _score_return_horizon_hac_summary(
        horizon_correlations,
        timeframe,
    )

    if summary.empty:
        return summary

    save_csv_for_excel(
        summary,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_hac_summary.csv",
        ),
    )
    if not horizon_correlations.empty:
        save_csv_for_excel(
            horizon_correlations,
            plot_path(
                output_dir,
                directory,
                "score_return_correlation_by_horizon_timestamp.csv",
            ),
        )
    if not autocorrelations.empty:
        save_csv_for_excel(
            autocorrelations,
            plot_path(
                output_dir,
                directory,
                "score_return_correlation_autocorrelation.csv",
            ),
        )

    _save_score_return_hac_summary_plot(
        summary,
        timeframe,
        directory,
        output_dir,
    )
    _save_score_return_autocorrelation_plots(
        autocorrelations,
        summary,
        timeframe,
        directory,
        output_dir,
    )
    return summary


def _format_metric_value(value, metric_format):
    if pd.isna(value):
        return ""
    if np.isclose(value, 0, atol=0.005):
        value = 0.0
    if metric_format == "percent":
        return f"{value:.0%}"
    if metric_format == "signed_percent":
        return f"{value:+.0%}"
    if metric_format == "plain":
        return f"{value:.2f}"
    return f"{value:+.2f}"


def _normalized_excess_by_timestamp(data, weight_column, attribution_column):
    rows = {}
    for timestamp, group in data.groupby("timestamp", sort=True):
        denominator = group[weight_column].abs().sum()
        if pd.isna(denominator) or np.isclose(denominator, 0):
            rows[timestamp] = np.nan
            continue
        rows[timestamp] = group[attribution_column].sum() / denominator
    return pd.Series(rows, dtype=float)


def _zscore_by_group(data, group_column, value_column, output_column):
    result = data.copy()
    mean = result.groupby(group_column)[value_column].transform("mean")
    std = result.groupby(group_column)[value_column].transform(
        lambda values: values.std(ddof=0)
    )
    result[output_column] = (
        (result[value_column] - mean) / std.replace(0, np.nan)
    )
    return result


def _rank_percentile_by_group(data, group_column, value_column, output_column):
    result = data.copy()
    ranks = result.groupby(group_column)[value_column].rank(
        method="average",
        ascending=True,
    )
    counts = result.groupby(group_column)[value_column].transform("count")
    result[output_column] = np.where(
        counts > 1,
        (ranks - 1) / (counts - 1),
        0.5,
    )
    return result


def _price_lookup_by_ticker(prices):
    lookups = {}
    if prices is None or prices.empty:
        return lookups

    clean_prices = (
        prices[["ticker", "timestamp", "close"]]
        .dropna(subset=["ticker", "timestamp", "close"])
        .copy()
    )
    if clean_prices.empty:
        return lookups

    clean_prices["timestamp"] = pd.to_datetime(clean_prices["timestamp"])
    clean_prices = clean_prices.sort_values(["ticker", "timestamp"])
    for ticker, group in clean_prices.groupby("ticker", sort=True):
        series = group.drop_duplicates("timestamp", keep="last").set_index(
            "timestamp"
        )["close"]
        lookups[ticker] = series.sort_index()
    return lookups


def _lookup_price_at_or_before(price_series, timestamp, tolerance_days=3):
    if price_series is None or price_series.empty:
        return np.nan
    timestamp = pd.Timestamp(timestamp)
    value = price_series.asof(timestamp)
    if pd.isna(value):
        return np.nan
    matched_index = price_series.index[price_series.index <= timestamp]
    if matched_index.empty:
        return np.nan
    matched_timestamp = matched_index[-1]
    if timestamp - matched_timestamp > pd.Timedelta(days=tolerance_days):
        return np.nan
    return float(value)


def _mean_trailing_window_return(
    row,
    price_lookup,
    start_week,
    end_week,
    skip_weeks=0,
):
    ticker_prices = price_lookup.get(row["ticker"])
    if ticker_prices is None:
        return np.nan

    timestamp = pd.Timestamp(row["timestamp"])
    end_timestamp = timestamp - pd.Timedelta(weeks=skip_weeks)
    end_price = _lookup_price_at_or_before(ticker_prices, end_timestamp)
    if pd.isna(end_price) or end_price <= 0:
        return np.nan

    trailing_returns = []
    for horizon_week in range(start_week, end_week + 1):
        past_timestamp = end_timestamp - pd.Timedelta(weeks=horizon_week)
        past_price = _lookup_price_at_or_before(ticker_prices, past_timestamp)
        if pd.isna(past_price) or past_price <= 0:
            continue
        total_return = end_price / past_price - 1
        horizon_days = max(1, (end_timestamp - past_timestamp).days)
        annualized = annualize_return(total_return, horizon_days)
        if annualized is not None:
            trailing_returns.append(annualized)

    return float(np.mean(trailing_returns)) if trailing_returns else np.nan


def _momentum_windows_for_row(row):
    windows = []
    for label, start_week, end_week, skip_weeks in ANTI_MOMENTUM_WINDOWS:
        if start_week is None or end_week is None:
            if (
                pd.isna(row.get("horizon_week_start"))
                or pd.isna(row.get("horizon_week_end"))
            ):
                continue
            start_week = int(row["horizon_week_start"])
            end_week = int(row["horizon_week_end"])
        windows.append((label, int(start_week), int(end_week), int(skip_weeks)))
    return windows


def _build_anti_momentum_points(data, prices):
    if prices is None or prices.empty:
        return pd.DataFrame()

    required = {
        "ticker",
        "timestamp",
        "score",
        "score_percentile",
        "mean_forward_annualized_return",
        "forward_return_percentile",
        "horizon_week_start",
        "horizon_week_end",
    }
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame()

    price_lookup = _price_lookup_by_ticker(prices)
    if not price_lookup:
        return pd.DataFrame()

    points = data[
        [
            "ticker",
            "timestamp",
            "score",
            "score_percentile",
            "mean_forward_annualized_return",
            "forward_return_percentile",
            "horizon_week_start",
            "horizon_week_end",
        ]
    ].dropna(subset=["ticker", "timestamp", "score"]).copy()
    if points.empty:
        return pd.DataFrame()

    for label, _, _, _ in ANTI_MOMENTUM_WINDOWS:
        column = f"trailing_{label}_annualized_return"
        points[column] = [
            _mean_trailing_window_return(
                row,
                price_lookup,
                start_week,
                end_week,
                skip_weeks,
            )
            for _, row in points.iterrows()
            for (
                window_label,
                start_week,
                end_week,
                skip_weeks,
            ) in _momentum_windows_for_row(row)
            if window_label == label
        ]
    return points


def _ticker_score_correlation_table(points, ticker_order, value_column):
    rows = []
    for ticker, group in points.groupby("ticker", sort=True):
        correlation = _safe_correlation(
            group,
            "score",
            value_column,
            "pearson",
        )
        clean = group[["score", value_column]].dropna()
        rows.append({
            "ticker": ticker,
            "correlation": correlation,
            "observations": len(clean),
            "mean_score": clean["score"].mean() if not clean.empty else np.nan,
            f"mean_{value_column}": (
                clean[value_column].mean() if not clean.empty else np.nan
            ),
        })

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    ordered_tickers = [
        ticker
        for ticker in ticker_order
        if ticker in set(result["ticker"])
    ]
    ordered_tickers.extend(
        ticker
        for ticker in sorted(result["ticker"])
        if ticker not in set(ordered_tickers)
    )
    return result.set_index("ticker").reindex(ordered_tickers).reset_index()


def _save_ticker_correlation_bar_chart(
    table,
    output_dir,
    directory,
    filename,
    title,
    x_label,
):
    if table.empty or "correlation" not in table.columns:
        return

    clean = table.dropna(subset=["correlation"]).copy()
    if clean.empty:
        return

    save_csv_for_excel(
        table,
        plot_path(output_dir, directory, f"{Path(filename).stem}.csv"),
    )

    y_positions = np.arange(len(clean))
    colors = np.where(clean["correlation"] >= 0, "#59A14F", "#E15759")
    mean_correlation = clean["correlation"].mean()

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(
        y_positions,
        clean["correlation"],
        color=colors,
        alpha=0.9,
    )
    ax.axvline(0, color="#444444", linewidth=1)
    ax.axvline(
        mean_correlation,
        color="#4C78A8",
        linewidth=1.5,
        linestyle="--",
        label=f"Średnia {mean_correlation:.3f}",
    )
    ax.set_xlim(-1, 1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(clean["ticker"])
    ax.set_ylim(len(clean) - 0.5, -0.5)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Ticker")
    ax.grid(True, axis="x", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, filename),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_anti_momentum_correlation_charts(
    data,
    prices,
    ticker_order,
    timeframe,
    directory,
    output_dir,
    horizon_label,
):
    points = _build_anti_momentum_points(data, prices)
    if points.empty:
        return

    anti_momentum_directory = directory / TICKER_ANTI_MOMENTUM_SECTION
    save_csv_for_excel(
        points,
        plot_path(
            output_dir,
            anti_momentum_directory,
            "anti_momentum_points.csv",
        ),
    )

    configs = [
        {
            "value_column": "mean_forward_annualized_return",
            "filename": (
                "score_to_future_annualized_return_correlation_by_ticker.png"
            ),
            "title": (
                f"Korelacja score z przyszłą roczną "
                f"stopą zwrotu według tickerów "
                f"({timeframe_label(timeframe)}, {horizon_label})"
            ),
            "x_label": (
                "Korelacja Pearsona: wynik modelu względem przyszłej "
                "rocznej stopy zwrotu"
            ),
        },
    ]
    for label, start_week, end_week, skip_weeks in ANTI_MOMENTUM_WINDOWS:
        window_label = (
            horizon_label
            if start_week is None or end_week is None
            else f"{start_week}-{end_week} tygodni"
        )
        if skip_weeks:
            window_label = f"{window_label}, pomiń {skip_weeks} tyg."
        column = f"trailing_{label}_annualized_return"
        configs.append(
            {
                "value_column": column,
                "filename": (
                    f"score_to_trailing_{label}_return_correlation_by_ticker.png"
                ),
                "title": (
                    f"Korelacja score z momentum Jegadeesha-Titmana "
                    f"według tickerów ({timeframe_label(timeframe)}, "
                    f"{window_label})"
                ),
                "x_label": (
                    "Korelacja Pearsona: wynik modelu względem historycznej "
                    f"rocznej stopy zwrotu ({window_label})"
                ),
            },
        )

    for config in configs:
        table = _ticker_score_correlation_table(
            points,
            ticker_order,
            config["value_column"],
        )
        _save_ticker_correlation_bar_chart(
            table,
            output_dir,
            anti_momentum_directory,
            config["filename"],
            config["title"],
            config["x_label"],
        )


def _build_model_vs_momentum_comparison(points, momentum_column, window_label):
    required = {
        "ticker",
        "timestamp",
        "score",
        momentum_column,
        "mean_forward_annualized_return",
    }
    if points.empty or not required.issubset(points.columns):
        return pd.DataFrame()

    clean = points.dropna(
        subset=[
            "ticker",
            "timestamp",
            "score",
            momentum_column,
            "mean_forward_annualized_return",
        ]
    ).copy()
    if clean.empty:
        return pd.DataFrame()

    clean = _zscore_by_group(
        clean,
        group_column="timestamp",
        value_column="score",
        output_column="model_score_zscore",
    )
    clean = _zscore_by_group(
        clean,
        group_column="timestamp",
        value_column=momentum_column,
        output_column="momentum_zscore",
    )
    clean = _zscore_by_group(
        clean,
        group_column="timestamp",
        value_column="mean_forward_annualized_return",
        output_column="future_return_zscore",
    )
    clean = _rank_percentile_by_group(
        clean,
        group_column="timestamp",
        value_column="score",
        output_column="model_score_percentile",
    )
    clean = _rank_percentile_by_group(
        clean,
        group_column="timestamp",
        value_column=momentum_column,
        output_column="momentum_percentile",
    )
    clean = _rank_percentile_by_group(
        clean,
        group_column="timestamp",
        value_column="mean_forward_annualized_return",
        output_column="future_return_percentile",
    )
    clean["benchmark_annualized_return"] = clean.groupby("timestamp")[
        "mean_forward_annualized_return"
    ].transform("mean")
    clean["future_excess_return"] = (
        clean["mean_forward_annualized_return"]
        - clean["benchmark_annualized_return"]
    )
    clean["model_long_short_weight"] = clean["model_score_percentile"] - 0.5
    clean["momentum_long_short_weight"] = clean["momentum_percentile"] - 0.5
    clean["model_long_only_weight"] = clean["model_long_short_weight"].clip(
        lower=0.0
    )
    clean["momentum_long_only_weight"] = clean[
        "momentum_long_short_weight"
    ].clip(lower=0.0)
    clean["model_long_short_attribution"] = (
        clean["model_long_short_weight"] * clean["future_excess_return"]
    )
    clean["momentum_long_short_attribution"] = (
        clean["momentum_long_short_weight"] * clean["future_excess_return"]
    )
    clean["model_long_only_attribution"] = (
        clean["model_long_only_weight"] * clean["future_excess_return"]
    )
    clean["momentum_long_only_attribution"] = (
        clean["momentum_long_only_weight"] * clean["future_excess_return"]
    )

    model_long_short = _normalized_excess_by_timestamp(
        clean,
        weight_column="model_long_short_weight",
        attribution_column="model_long_short_attribution",
    )
    momentum_long_short = _normalized_excess_by_timestamp(
        clean,
        weight_column="momentum_long_short_weight",
        attribution_column="momentum_long_short_attribution",
    )
    model_long_only = _normalized_excess_by_timestamp(
        clean,
        weight_column="model_long_only_weight",
        attribution_column="model_long_only_attribution",
    )
    momentum_long_only = _normalized_excess_by_timestamp(
        clean,
        weight_column="momentum_long_only_weight",
        attribution_column="momentum_long_only_attribution",
    )

    rows = []
    for timestamp, group in clean.groupby("timestamp", sort=True):
        rows.append({
            "timestamp": timestamp,
            "momentum_window": window_label,
            "ticker_count": group["ticker"].nunique(),
            "model_pearson_ic": _safe_correlation(
                group,
                "model_score_zscore",
                "future_return_zscore",
                "pearson",
            ),
            "momentum_pearson_ic": _safe_correlation(
                group,
                "momentum_zscore",
                "future_return_zscore",
                "pearson",
            ),
            "model_spearman_ic": _safe_correlation(
                group,
                "model_score_percentile",
                "future_return_percentile",
                "spearman",
            ),
            "momentum_spearman_ic": _safe_correlation(
                group,
                "momentum_percentile",
                "future_return_percentile",
                "spearman",
            ),
            "model_long_short_normalized_excess": model_long_short.get(
                timestamp,
                np.nan,
            ),
            "momentum_long_short_normalized_excess": momentum_long_short.get(
                timestamp,
                np.nan,
            ),
            "model_long_only_normalized_excess": model_long_only.get(
                timestamp,
                np.nan,
            ),
            "momentum_long_only_normalized_excess": momentum_long_only.get(
                timestamp,
                np.nan,
            ),
            "benchmark_annualized_return": group[
                "benchmark_annualized_return"
            ].mean(),
        })

    return pd.DataFrame(rows)


def _plot_model_vs_momentum_panel(
    comparison,
    output_dir,
    directory,
    filename,
    title,
):
    if comparison.empty:
        return

    panels = [
        (
            "model_pearson_ic",
            "momentum_pearson_ic",
            "Pearson IC",
            "Korelacja",
            None,
        ),
        (
            "model_spearman_ic",
            "momentum_spearman_ic",
            "Spearman IC",
            "Korelacja",
            None,
        ),
        (
            "model_long_short_normalized_excess",
            "momentum_long_short_normalized_excess",
            "Znormalizowany nadwyżkowy zwrot long-short",
            "Nadwyżkowy zwrot",
            "percent",
        ),
        (
            "model_long_only_normalized_excess",
            "momentum_long_only_normalized_excess",
            "Znormalizowany nadwyżkowy zwrot long-only",
            "Nadwyżkowy zwrot",
            "percent",
        ),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(15, 9), sharex=True)
    for ax, (model_col, momentum_col, panel_title, y_label, fmt) in zip(
        axes.flatten(),
        panels,
    ):
        panel_data = comparison.dropna(subset=[model_col, momentum_col], how="all")
        if panel_data.empty:
            ax.set_visible(False)
            continue

        model_mean = panel_data[model_col].mean()
        momentum_mean = panel_data[momentum_col].mean()
        ax.plot(
            panel_data["timestamp"],
            panel_data[model_col],
            color="#4C78A8",
            linewidth=2,
            marker="o",
            markersize=3,
            label=f"Model, średnia {model_mean:.3f}"
            if fmt is None
            else f"Model, średnia {model_mean:.1%}",
        )
        ax.plot(
            panel_data["timestamp"],
            panel_data[momentum_col],
            color="#F28E2B",
            linewidth=2,
            marker="o",
            markersize=3,
            label=f"Momentum, średnia {momentum_mean:.3f}"
            if fmt is None
            else f"Momentum, średnia {momentum_mean:.1%}",
        )
        ax.axhline(0, color="#444444", linewidth=1)
        if pd.notna(model_mean):
            ax.axhline(
                model_mean,
                color="#4C78A8",
                linewidth=1.2,
                linestyle="--",
                alpha=0.75,
            )
        if pd.notna(momentum_mean):
            ax.axhline(
                momentum_mean,
                color="#F28E2B",
                linewidth=1.2,
                linestyle="--",
                alpha=0.75,
            )
        if fmt == "percent":
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        else:
            ax.set_ylim(-1, 1)
        ax.set_title(panel_title)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best")

    fig.suptitle(title)
    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, filename),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_model_vs_momentum_comparison_charts(
    data,
    prices,
    timeframe,
    directory,
    output_dir,
    horizon_label,
):
    points = _build_anti_momentum_points(data, prices)
    if points.empty:
        return

    comparison_directory = directory / TICKER_MODEL_VS_MOMENTUM_SECTION
    comparisons = []
    for label, start_week, end_week, skip_weeks in ANTI_MOMENTUM_WINDOWS:
        window_label = (
            horizon_label
            if start_week is None or end_week is None
            else f"{start_week}-{end_week} tygodni"
        )
        if skip_weeks:
            window_label = f"{window_label}, pomiń {skip_weeks} tyg."
        column = f"trailing_{label}_annualized_return"
        comparison = _build_model_vs_momentum_comparison(
            points,
            momentum_column=column,
            window_label=window_label,
        )
        if comparison.empty:
            continue
        comparisons.append(comparison)
        safe_label = _safe_filename(label)
        save_csv_for_excel(
            comparison,
            plot_path(
                output_dir,
                comparison_directory,
                f"model_vs_momentum_{safe_label}_by_timestamp.csv",
            ),
        )
        _plot_model_vs_momentum_panel(
            comparison,
            output_dir,
            comparison_directory,
            f"model_vs_momentum_{safe_label}_comparison.png",
            (
                f"Model względem momentum według daty scoringu "
                f"({timeframe_label(timeframe)}, momentum {window_label})"
            ),
        )

    if not comparisons:
        return

    combined = pd.concat(comparisons, ignore_index=True)
    save_csv_for_excel(
        combined,
        plot_path(
            output_dir,
            comparison_directory,
            "model_vs_momentum_all_windows_by_timestamp.csv",
        ),
    )
    summary = (
        combined.groupby("momentum_window", as_index=False)
        .agg(
            model_pearson_ic_mean=("model_pearson_ic", "mean"),
            momentum_pearson_ic_mean=("momentum_pearson_ic", "mean"),
            model_spearman_ic_mean=("model_spearman_ic", "mean"),
            momentum_spearman_ic_mean=("momentum_spearman_ic", "mean"),
            model_long_short_excess_mean=(
                "model_long_short_normalized_excess",
                "mean",
            ),
            momentum_long_short_excess_mean=(
                "momentum_long_short_normalized_excess",
                "mean",
            ),
            model_long_only_excess_mean=(
                "model_long_only_normalized_excess",
                "mean",
            ),
            momentum_long_only_excess_mean=(
                "momentum_long_only_normalized_excess",
                "mean",
            ),
            timestamp_count=("timestamp", "nunique"),
        )
    )
    save_csv_for_excel(
        summary,
        plot_path(
            output_dir,
            comparison_directory,
            "model_vs_momentum_summary.csv",
        ),
    )


def _save_ticker_date_heatmap(
    data,
    ticker_order,
    value_column,
    timeframe,
    output_dir,
    directory,
    filename,
    title,
    colorbar_label,
    cmap_name,
    vmin=None,
    vmax=None,
    percent_format=False,
    robust=False,
    symmetric=False,
    row_metric=None,
    row_metric_label="ME",
    row_metric_format="signed",
    column_metric=None,
    column_metric_label=None,
    column_metric_format="signed_percent",
):
    heatmap_data = data.pivot_table(
        index="ticker",
        columns="timestamp",
        values=value_column,
        aggfunc="last",
    ).sort_index(axis=1)
    if heatmap_data.empty:
        return

    heatmap_data = heatmap_data.reindex(ticker_order)
    _save_heatmap_csv(heatmap_data, output_dir, directory, filename)
    values = heatmap_data.to_numpy(dtype=float)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return

    if symmetric and vmin is None and vmax is None:
        percentile = 95 if robust else 100
        limit = float(np.nanpercentile(np.abs(finite_values), percentile))
        if np.isclose(limit, 0):
            limit = max(abs(float(np.nanmin(finite_values))), 1.0) * 0.01
        vmin = -limit
        vmax = limit
    elif robust and vmin is None and vmax is None:
        vmin = float(np.nanpercentile(finite_values, 5))
        vmax = float(np.nanpercentile(finite_values, 95))
        if np.isclose(vmin, vmax):
            vmin = float(np.nanmin(finite_values))
            vmax = float(np.nanmax(finite_values))
    if vmin is None:
        vmin = float(np.nanmin(finite_values))
    if vmax is None:
        vmax = float(np.nanmax(finite_values))
    if np.isclose(vmin, vmax):
        spread = max(abs(vmin), 1.0) * 0.01
        vmin -= spread
        vmax += spread

    fig, ax = plt.subplots(figsize=(15.5, 8))
    cmap = plt.cm.get_cmap(cmap_name).copy()
    cmap.set_bad("#F2F2F2")
    image = ax.imshow(
        values,
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )

    y_positions = np.arange(len(heatmap_data.index))
    ax.set_yticks(y_positions)
    ax.set_yticklabels(heatmap_data.index)
    ax.set_ylabel(
        "Ticker, sortowanie według średniej przyszłej rocznej stopy zwrotu"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_title(title)

    date_count = len(heatmap_data.columns)
    tick_count = min(10, date_count)
    tick_positions = (
        np.linspace(0, date_count - 1, tick_count, dtype=int)
        if date_count
        else np.array([], dtype=int)
    )
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(
        [
            heatmap_data.columns[position].strftime("%Y-%m-%d")
            for position in tick_positions
        ],
        rotation=45,
        ha="right",
    )
    ax.set_xticks(np.arange(-0.5, date_count, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(heatmap_data.index), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)

    colorbar_pad = 0.11 if row_metric is not None and not row_metric.empty else 0.02
    colorbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=colorbar_pad)
    colorbar.set_label(colorbar_label)
    if percent_format:
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    if row_metric is not None and not row_metric.empty:
        row_metric = row_metric.reindex(heatmap_data.index)
        metric_ax = ax.twinx()
        metric_ax.set_ylim(ax.get_ylim())
        metric_ax.set_yticks(y_positions)
        metric_ax.set_yticklabels(
            [
                (
                    f"{row_metric_label}="
                    f"{_format_metric_value(value, row_metric_format)}"
                )
                if pd.notna(value)
                else ""
                for value in row_metric
            ]
        )
        metric_ax.tick_params(axis="y", length=0, pad=8)

    if column_metric is not None and not column_metric.empty:
        ax.set_xlabel("")
        column_metric = column_metric.reindex(heatmap_data.columns)
        metric_label = column_metric_label or "Metryka"
        metric_values = pd.DataFrame({
            "timestamp": heatmap_data.columns,
            metric_label: column_metric.to_numpy(),
        })
        metric_filename = f"{Path(filename).stem}_column_metric.csv"
        save_csv_for_excel(
            metric_values,
            plot_path(output_dir, directory, metric_filename),
        )

        metric_ax = ax.twiny()
        metric_ax.set_xlim(ax.get_xlim())
        metric_ax.xaxis.set_ticks_position("bottom")
        metric_ax.xaxis.set_label_position("bottom")
        metric_ax.spines["bottom"].set_position(("outward", 62))
        metric_ax.spines["top"].set_visible(False)
        metric_ax.set_xticks(np.arange(date_count))
        metric_ax.set_xticklabels(
            [
                _format_metric_value(value, column_metric_format)
                for value in column_metric
            ],
            rotation=0,
            ha="center",
            fontsize=7,
        )
        metric_ax.set_xlabel(metric_label)
        metric_ax.tick_params(axis="x", length=0, pad=2)

    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, filename),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_normalized_excess_comparison_plot(
    data,
    timeframe,
    directory,
    output_dir,
    long_short_normalized_excess,
    long_only_normalized_excess,
):
    benchmark = (
        data.groupby("timestamp")["mean_forward_annualized_return"]
        .mean()
        .sort_index()
    )
    if benchmark.empty:
        return

    benchmark_std = benchmark.std(ddof=0)
    if pd.notna(benchmark_std) and not np.isclose(benchmark_std, 0):
        benchmark_zscore = (benchmark - benchmark.mean()) / benchmark_std
    else:
        benchmark_zscore = pd.Series(0.0, index=benchmark.index)

    comparison = pd.DataFrame({
        "timestamp": benchmark.index,
        "long_short_normalized_excess": long_short_normalized_excess.reindex(
            benchmark.index
        ).to_numpy(),
        "long_only_normalized_excess": long_only_normalized_excess.reindex(
            benchmark.index
        ).to_numpy(),
        "benchmark_annualized_return": benchmark.to_numpy(),
        "benchmark_zscore": benchmark_zscore.to_numpy(),
    })
    comparison = comparison.dropna(
        subset=["long_short_normalized_excess", "long_only_normalized_excess"],
        how="all",
    )
    if comparison.empty:
        return

    save_csv_for_excel(
        comparison,
        plot_path(
            output_dir,
            directory,
            "normalized_excess_attribution_by_timestamp.csv",
        ),
    )

    fig, ax = plt.subplots(figsize=(13.5, 6.2))
    benchmark_ax = ax.twinx()
    benchmark_ax.plot(
        comparison["timestamp"],
        comparison["benchmark_zscore"],
        color="#777777",
        linewidth=2,
        linestyle=":",
        marker="s",
        markersize=3,
        alpha=0.85,
        label="Z-score zwrotu benchmarku",
    )
    benchmark_ax.fill_between(
        comparison["timestamp"],
        0,
        comparison["benchmark_zscore"],
        color="#777777",
        alpha=0.08,
    )
    ax.plot(
        comparison["timestamp"],
        comparison["long_short_normalized_excess"],
        color="#4C78A8",
        linewidth=2.3,
        marker="o",
        markersize=3.5,
        label="Znormalizowany nadwyżkowy zwrot long-short",
    )
    ax.plot(
        comparison["timestamp"],
        comparison["long_only_normalized_excess"],
        color="#F28E2B",
        linewidth=2.3,
        marker="o",
        markersize=3.5,
        label="Znormalizowany nadwyżkowy zwrot long-only",
    )

    long_short_mean = comparison["long_short_normalized_excess"].mean()
    long_only_mean = comparison["long_only_normalized_excess"].mean()
    ax.axhline(0, color="#444444", linewidth=1)
    if pd.notna(long_short_mean):
        ax.axhline(
            long_short_mean,
            color="#4C78A8",
            linewidth=1.5,
            linestyle="--",
            alpha=0.8,
            label=f"Średnia long-short {long_short_mean:.1%}",
        )
    if pd.notna(long_only_mean):
        ax.axhline(
            long_only_mean,
            color="#F28E2B",
            linewidth=1.5,
            linestyle="--",
            alpha=0.8,
            label=f"Średnia long-only {long_only_mean:.1%}",
        )
    benchmark_ax.axhline(0, color="#777777", linewidth=0.9, linestyle=":", alpha=0.7)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_title(
        f"Atrybucja znormalizowanego nadwyżkowego zwrotu według daty scoringu "
        f"({timeframe_label(timeframe)})"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_ylabel("Znormalizowany nadwyżkowy zwrot")
    benchmark_ax.set_ylabel("Z-score zwrotu benchmarku")
    benchmark_limit = comparison["benchmark_zscore"].abs().max()
    if pd.notna(benchmark_limit) and benchmark_limit > 0:
        benchmark_ax.set_ylim(
            -max(1.0, float(benchmark_limit) * 1.1),
            max(1.0, float(benchmark_limit) * 1.1),
        )
    ax.grid(True, alpha=0.25)
    handles, labels = ax.get_legend_handles_labels()
    benchmark_handles, benchmark_labels = benchmark_ax.get_legend_handles_labels()
    ax.legend(
        handles + benchmark_handles,
        labels + benchmark_labels,
        loc="best",
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "normalized_excess_attribution_by_timestamp.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_forward_return_heatmap(
    timeframe_forward_returns,
    timeframe_forward_return_horizons,
    prices,
    timeframe,
    directory,
    output_dir,
):
    required = {
        "ticker",
        "timestamp",
        "score",
        "score_percentile",
        "mean_forward_annualized_return",
        "forward_return_percentile",
    }
    if timeframe_forward_returns.empty or not required.issubset(
        timeframe_forward_returns.columns
    ):
        return

    data = timeframe_forward_returns.dropna(
        subset=[
            "ticker",
            "timestamp",
            "score",
            "score_percentile",
            "mean_forward_annualized_return",
            "forward_return_percentile",
        ]
    ).copy()
    if data.empty:
        return

    score_mean = data.groupby("timestamp")["score"].transform("mean")
    score_std = data.groupby("timestamp")["score"].transform(
        lambda values: values.std(ddof=0)
    )
    return_mean = data.groupby("timestamp")[
        "mean_forward_annualized_return"
    ].transform("mean")
    return_std = data.groupby("timestamp")[
        "mean_forward_annualized_return"
    ].transform(lambda values: values.std(ddof=0))
    data["score_zscore"] = (
        (data["score"] - score_mean) / score_std.replace(0, np.nan)
    ).fillna(0.0)
    data["forward_return_zscore"] = (
        (data["mean_forward_annualized_return"] - return_mean)
        / return_std.replace(0, np.nan)
    ).fillna(0.0)
    data["excess_forward_annualized_return"] = (
        data["mean_forward_annualized_return"] - return_mean
    )
    data["zscore_error"] = data["score_zscore"] - data["forward_return_zscore"]
    data["percentile_error"] = (
        data["score_percentile"] - data["forward_return_percentile"]
    )
    data["long_short_weight"] = data["score_percentile"] - 0.5
    data["long_only_weight"] = data["long_short_weight"].clip(lower=0.0)
    data["return_attribution"] = (
        data["long_short_weight"] * data["excess_forward_annualized_return"]
    )
    data["long_only_return_attribution"] = (
        data["long_only_weight"] * data["excess_forward_annualized_return"]
    )

    long_short_normalized_excess = _normalized_excess_by_timestamp(
        data,
        weight_column="long_short_weight",
        attribution_column="return_attribution",
    )
    long_only_normalized_excess = _normalized_excess_by_timestamp(
        data,
        weight_column="long_only_weight",
        attribution_column="long_only_return_attribution",
    )
    ticker_order = list(
        data.groupby("ticker")["mean_forward_annualized_return"]
        .mean()
        .sort_values(ascending=False)
        .index
    )

    horizon_start = data["horizon_week_start"].dropna()
    horizon_end = data["horizon_week_end"].dropna()
    horizon_label = (
        f"{int(horizon_start.min())}-{int(horizon_end.max())}w"
        if not horizon_start.empty and not horizon_end.empty
        else "skonfigurowany horyzont"
    )
    forward_return_reference_directory = (
        directory / TICKER_FORWARD_RETURN_REFERENCE_SECTION
    )
    pearson_directory = directory / TICKER_PEARSON_ZSCORE_SECTION
    spearman_directory = directory / TICKER_SPEARMAN_PERCENTILE_SECTION
    information_coefficient_directory = (
        directory / TICKER_INFORMATION_COEFFICIENT_SECTION
    )
    return_attribution_directory = directory / TICKER_RETURN_ATTRIBUTION_SECTION

    heatmaps = [
        {
            "directory": pearson_directory,
            "column": "score_zscore",
            "filename": "pearson_01_score_zscore_heatmap.png",
            "title": (
                f"Widok Pearsona: wynik standaryzowany score "
                f"({timeframe_label(timeframe)})"
            ),
            "colorbar": "Wynik standaryzowany score",
            "cmap": "RdYlGn",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["score_zscore"].mean(),
            "row_metric_label": "ŚrScoreZ",
        },
        {
            "directory": pearson_directory,
            "column": "forward_return_zscore",
            "filename": "pearson_02_forward_return_zscore_heatmap.png",
            "title": (
                f"Widok Pearsona: z-score przyszłej stopy zwrotu "
                f"({timeframe_label(timeframe)}, {horizon_label})"
            ),
            "colorbar": "Z-score przyszłej stopy zwrotu",
            "cmap": "RdYlGn",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["forward_return_zscore"].mean(),
            "row_metric_label": "ŚrZwrotZ",
        },
        {
            "directory": pearson_directory,
            "column": "zscore_error",
            "filename": "pearson_03_score_minus_return_zscore_heatmap.png",
            "title": (
                f"Widok Pearsona: różnica między wynikiem standaryzowanym score "
                f"a wynikiem standaryzowanym stopy zwrotu ({timeframe_label(timeframe)}, "
                f"{horizon_label})"
            ),
            "colorbar": "Wynik standaryzowany score - wynik standaryzowany przyszłego zwrotu",
            "cmap": "RdYlGn_r",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["zscore_error"].mean(),
            "row_metric_label": "ŚrRóżnZ",
        },
        {
            "directory": spearman_directory,
            "column": "score_percentile",
            "filename": "spearman_01_score_percentile_heatmap.png",
            "title": (
                f"Widok Spearmana: percentyl score "
                f"({timeframe_label(timeframe)})"
            ),
            "colorbar": "Percentyl score",
            "cmap": "RdYlGn",
            "vmin": 0,
            "vmax": 1,
            "percent_format": True,
            "row_metric": data.groupby("ticker")["score_percentile"].mean(),
            "row_metric_label": "ŚrPctWyn",
            "row_metric_format": "percent",
        },
        {
            "directory": spearman_directory,
            "column": "forward_return_percentile",
            "filename": "spearman_02_forward_return_percentile_heatmap.png",
            "title": (
                f"Widok Spearmana: percentyl przyszłej stopy zwrotu "
                f"({timeframe_label(timeframe)}, {horizon_label})"
            ),
            "colorbar": "Percentyl przyszłej stopy zwrotu",
            "cmap": "RdYlGn",
            "vmin": 0,
            "vmax": 1,
            "percent_format": True,
            "row_metric": data.groupby("ticker")["forward_return_percentile"].mean(),
            "row_metric_label": "ŚrPctZw",
            "row_metric_format": "percent",
        },
        {
            "directory": spearman_directory,
            "column": "percentile_error",
            "filename": "spearman_03_score_minus_return_percentile_heatmap.png",
            "title": (
                f"Widok Spearmana: różnica między percentylem score "
                f"a percentylem przyszłej stopy zwrotu "
                f"({timeframe_label(timeframe)}, {horizon_label})"
            ),
            "colorbar": "Percentyl score - percentyl przyszłego zwrotu",
            "cmap": "RdYlGn_r",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["percentile_error"].mean(),
            "row_metric_label": "ŚrRóżnPct",
            "row_metric_format": "signed_percent",
        },
        {
            "directory": forward_return_reference_directory,
            "column": "excess_forward_annualized_return",
            "filename": "excess_forward_annualized_return_heatmap.png",
            "title": (
                f"Przyszły roczny nadwyżkowy zwrot ponad benchmark "
                f"z tej samej daty ({timeframe_label(timeframe)}, {horizon_label})"
            ),
            "colorbar": "Przyszły roczny nadwyżkowy zwrot",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")[
                "excess_forward_annualized_return"
            ].mean(),
            "row_metric_label": "ŚrNadZw",
            "row_metric_format": "signed_percent",
        },
        {
            "directory": return_attribution_directory,
            "column": "return_attribution",
            "filename": "return_contribution_attribution_heatmap.png",
            "title": (
                f"Atrybucja zwrotu long-short: (percentyl score - 0.5) "
                f"x przyszły nadwyżkowy zwrot "
                f"({timeframe_label(timeframe)}, {horizon_label})"
            ),
            "colorbar": "Kontrybucja zwrotu",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["return_attribution"].mean(),
            "row_metric_label": "ŚrKontr",
            "row_metric_format": "signed_percent",
            "column_metric": long_short_normalized_excess,
            "column_metric_label": "Znormalizowany nadwyżkowy zwrot long-short",
            "column_metric_format": "signed_percent",
        },
        {
            "directory": return_attribution_directory,
            "column": "long_only_return_attribution",
            "filename": "long_only_return_contribution_attribution_heatmap.png",
            "title": (
                f"Atrybucja zwrotu long-only: max(percentyl score - 0.5, 0) "
                f"x przyszły nadwyżkowy zwrot "
                f"({timeframe_label(timeframe)}, {horizon_label})"
            ),
            "colorbar": "Kontrybucja zwrotu long-only",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")[
                "long_only_return_attribution"
            ].mean(),
            "row_metric_label": "ŚrKontr",
            "row_metric_format": "signed_percent",
            "column_metric": long_only_normalized_excess,
            "column_metric_label": "Znormalizowany nadwyżkowy zwrot long-only",
            "column_metric_format": "signed_percent",
        },
    ]

    for config in heatmaps:
        _save_ticker_date_heatmap(
            data,
            ticker_order,
            config["column"],
            timeframe,
            output_dir,
            config["directory"],
            config["filename"],
            config["title"],
            config["colorbar"],
            config["cmap"],
            vmin=config.get("vmin"),
            vmax=config.get("vmax"),
            percent_format=config.get("percent_format", False),
            robust=config.get("robust", False),
            symmetric=config.get("symmetric", False),
            row_metric=config.get("row_metric"),
            row_metric_label=config.get("row_metric_label", "ME"),
            row_metric_format=config.get("row_metric_format", "signed"),
            column_metric=config.get("column_metric"),
            column_metric_label=config.get("column_metric_label"),
            column_metric_format=config.get(
                "column_metric_format",
                "signed_percent",
            ),
        )

    _save_normalized_excess_comparison_plot(
        data,
        timeframe,
        return_attribution_directory,
        output_dir,
        long_short_normalized_excess,
        long_only_normalized_excess,
    )
    _save_score_return_correlation_by_timestamp_plot(
        data,
        timeframe_forward_return_horizons,
        timeframe,
        information_coefficient_directory,
        output_dir,
    )
    _save_anti_momentum_correlation_charts(
        data,
        prices,
        ticker_order,
        timeframe,
        directory,
        output_dir,
        horizon_label,
    )
    _save_model_vs_momentum_comparison_charts(
        data,
        prices,
        timeframe,
        directory,
        output_dir,
        horizon_label,
    )


def _save_score_return_correlation_by_timestamp_plot(
    data,
    timeframe_forward_return_horizons,
    timeframe,
    directory,
    output_dir,
):
    required = {
        "timestamp",
        "score_zscore",
        "forward_return_zscore",
        "score_percentile",
        "forward_return_percentile",
        "mean_forward_annualized_return",
        "excess_forward_annualized_return",
    }
    if data.empty or not required.issubset(data.columns):
        return

    rows = []
    for timestamp, group in data.groupby("timestamp", sort=True):
        pearson = _safe_correlation(
            group,
            "score_zscore",
            "forward_return_zscore",
            "pearson",
        )
        spearman = _safe_correlation(
            group,
            "score_percentile",
            "forward_return_percentile",
            "spearman",
        )
        score_percentile_pearson = _safe_correlation(
            group,
            "score_percentile",
            "excess_forward_annualized_return",
            "pearson",
        )
        benchmark_return = group["mean_forward_annualized_return"].mean()
        rows.append({
            "timestamp": timestamp,
            "pearson": pearson,
            "spearman": spearman,
            "score_percentile_pearson_ic": score_percentile_pearson,
            "benchmark_annualized_return": benchmark_return,
        })

    correlations = pd.DataFrame(rows).dropna(subset=["pearson", "spearman"])
    if correlations.empty:
        return

    pearson_mean = float(correlations["pearson"].mean())
    spearman_mean = float(correlations["spearman"].mean())
    score_percentile_pearson_mean = float(
        correlations["score_percentile_pearson_ic"].mean()
    )
    benchmark_std = correlations["benchmark_annualized_return"].std(ddof=0)
    if pd.notna(benchmark_std) and not np.isclose(benchmark_std, 0):
        correlations["benchmark_zscore"] = (
            correlations["benchmark_annualized_return"]
            - correlations["benchmark_annualized_return"].mean()
        ) / benchmark_std
    else:
        correlations["benchmark_zscore"] = 0.0
    save_csv_for_excel(
        correlations,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_by_timestamp.csv",
        ),
    )
    _save_score_return_hac_diagnostics(
        correlations,
        data,
        timeframe,
        directory,
        output_dir,
        horizon_points=timeframe_forward_return_horizons,
    )

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(
        correlations["timestamp"],
        correlations["pearson"],
        color="#4C78A8",
        linewidth=2,
        marker="o",
        markersize=3,
        label=f"Pearson, średnia {pearson_mean:.3f}",
    )
    ax.plot(
        correlations["timestamp"],
        correlations["spearman"],
        color="#59A14F",
        linewidth=2,
        marker="o",
        markersize=3,
        label=f"Spearman, średnia {spearman_mean:.3f}",
    )
    ax.plot(
        correlations["timestamp"],
        correlations["score_percentile_pearson_ic"],
        color="#F28E2B",
        linewidth=1.8,
        marker="o",
        markersize=2.8,
        label=(
            f"Pearson IC percentyla score, "
            f"średnia {score_percentile_pearson_mean:.3f}"
        ),
    )
    benchmark_ax = ax.twinx()
    benchmark_ax.plot(
        correlations["timestamp"],
        correlations["benchmark_zscore"],
        color="#777777",
        linewidth=1.8,
        linestyle=":",
        marker="s",
        markersize=2.8,
        alpha=0.9,
        label="Z-score zwrotu benchmarku",
    )
    benchmark_ax.axhline(0, color="#777777", linewidth=0.9, linestyle=":", alpha=0.7)
    ax.axhline(0, color="#444444", linewidth=1)
    ax.axhline(
        pearson_mean,
        color="#4C78A8",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
    )
    ax.axhline(
        spearman_mean,
        color="#59A14F",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
    )
    ax.axhline(
        score_percentile_pearson_mean,
        color="#F28E2B",
        linewidth=1.2,
        linestyle="--",
        alpha=0.75,
    )
    ax.set_ylim(-1, 1)
    ax.set_title(
        f"Korelacja score z przyszłą stopą zwrotu według daty scoringu "
        f"({timeframe_label(timeframe)}; średnia Pearson {pearson_mean:.3f}, "
        f"średnia Spearman {spearman_mean:.3f}, "
        f"średnia Pearson IC percentyla score "
        f"{score_percentile_pearson_mean:.3f})"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_ylabel("Korelacja przekrojowa")
    benchmark_ax.set_ylabel("Z-score zwrotu benchmarku")
    benchmark_limit = correlations["benchmark_zscore"].abs().max()
    if pd.notna(benchmark_limit) and benchmark_limit > 0:
        benchmark_limit = max(1.0, float(benchmark_limit) * 1.1)
        benchmark_ax.set_ylim(-benchmark_limit, benchmark_limit)
    ax.grid(True, alpha=0.25)
    handles, labels = ax.get_legend_handles_labels()
    benchmark_handles, benchmark_labels = benchmark_ax.get_legend_handles_labels()
    ax.legend(
        handles + benchmark_handles,
        labels + benchmark_labels,
        loc="best",
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_by_timestamp.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_forward_return_cross_section_correlation_plot(
    timeframe_forward_returns,
    timeframe,
    directory,
    output_dir,
):
    pearson_column = "cross_section_pearson_score_to_forward_percentile"
    spearman_column = "cross_section_spearman_score_to_forward_percentile"
    required = {"timestamp", pearson_column, spearman_column}
    if timeframe_forward_returns.empty or not required.issubset(
        timeframe_forward_returns.columns
    ):
        return

    correlations = (
        timeframe_forward_returns[list(required)]
        .drop_duplicates("timestamp")
        .dropna(subset=[pearson_column, spearman_column])
        .sort_values("timestamp")
    )
    if correlations.empty:
        return

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(
        correlations["timestamp"],
        correlations[pearson_column],
        color="#4C78A8",
        linewidth=2,
        marker="o",
        markersize=3,
        label="Pearson",
    )
    ax.plot(
        correlations["timestamp"],
        correlations[spearman_column],
        color="#59A14F",
        linewidth=2,
        marker="o",
        markersize=3,
        label="Spearman",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.axhline(
        correlations[pearson_column].mean(),
        color="#4C78A8",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
        label="Średnia Pearsona",
    )
    ax.axhline(
        correlations[spearman_column].mean(),
        color="#59A14F",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
        label="Średnia Spearmana",
    )
    ax.set_ylim(-1, 1)
    ax.set_title(
        f"Korelacja percentyla score z percentylem przyszłej stopy "
        f"zwrotu ({timeframe_label(timeframe)})"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_ylabel("Korelacja przekrojowa")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "score_percentile_to_forward_return_percentile_correlation.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_raw_score_forward_return_correlation_plot(
    timeframe_forward_returns,
    timeframe,
    directory,
    output_dir,
):
    required = {"ticker", "score", "mean_forward_annualized_return"}
    if timeframe_forward_returns.empty or not required.issubset(
        timeframe_forward_returns.columns
    ):
        return

    data = timeframe_forward_returns.dropna(
        subset=["ticker", "score", "mean_forward_annualized_return"]
    ).copy()
    if data.empty:
        return

    correlations = pd.DataFrame({
        "pearson": data.groupby("ticker").apply(
            _safe_correlation,
            x_column="score",
            y_column="mean_forward_annualized_return",
            method="pearson",
        ),
        "spearman": data.groupby("ticker").apply(
            _safe_correlation,
            x_column="score",
            y_column="mean_forward_annualized_return",
            method="spearman",
        ),
    }).dropna(how="all")
    if correlations.empty:
        return

    correlations["sort_value"] = correlations[["pearson", "spearman"]].mean(axis=1)
    correlations = correlations.sort_values("sort_value", ascending=False)

    y_positions = np.arange(len(correlations.index))
    fig, (pearson_ax, spearman_ax) = plt.subplots(
        1,
        2,
        figsize=(10, 8),
        sharey=True,
    )
    for ax, column, title in [
        (pearson_ax, "pearson", "Pearson"),
        (spearman_ax, "spearman", "Spearman"),
    ]:
        values = correlations[column]
        colors = np.where(values >= 0, "#59A14F", "#E15759")
        ax.barh(y_positions, values, color=colors, alpha=0.9)
        ax.axvline(0, color="#444444", linewidth=1)
        ax.set_xlim(-1, 1)
        ax.set_title(title)
        ax.set_xlabel("Korelacja")
        ax.grid(True, axis="x", alpha=0.25)
        ax.set_ylim(len(correlations.index) - 0.5, -0.5)

    pearson_ax.set_yticks(y_positions)
    pearson_ax.set_yticklabels(correlations.index)
    pearson_ax.set_ylabel("Ticker")
    spearman_ax.tick_params(axis="y", left=False, labelleft=False)
    fig.suptitle(
        f"Korelacja surowego score ze średnią przyszłą "
        f"roczną stopą zwrotu ({timeframe_label(timeframe)})"
    )
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "raw_score_to_forward_annualized_return_correlation_by_ticker.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def plot(results, output_dir):
    if not results:
        return

    metrics = results.get("metrics")
    score_points = results.get("score_points")
    forward_return_points = results.get("forward_return_points")
    forward_return_horizon_points = results.get("forward_return_horizon_points")
    prices = results.get("prices")
    moving_average_window = int(
        results.get("moving_average_window", DEFAULT_MOVING_AVERAGE_WINDOW)
        or DEFAULT_MOVING_AVERAGE_WINDOW
    )
    if metrics is None or metrics.empty:
        return

    metrics = metrics.copy()
    metrics["timestamp"] = _to_utc_naive(metrics["timestamp"])
    if score_points is None or score_points.empty:
        score_points = metrics
    else:
        score_points = score_points.copy()
        score_points["timestamp"] = _to_utc_naive(score_points["timestamp"])
    if forward_return_points is not None and not forward_return_points.empty:
        forward_return_points = forward_return_points.copy()
        forward_return_points["timestamp"] = _to_utc_naive(
            forward_return_points["timestamp"]
        )
    if (
        forward_return_horizon_points is not None
        and not forward_return_horizon_points.empty
    ):
        forward_return_horizon_points = forward_return_horizon_points.copy()
        forward_return_horizon_points["timestamp"] = _to_utc_naive(
            forward_return_horizon_points["timestamp"]
        )
    if prices is not None and not prices.empty:
        prices = prices.copy()
        prices["timestamp"] = _to_utc_naive(prices["timestamp"])

    for (timeframe, ticker), group in metrics.groupby(
        ["timeframe", "ticker"],
        sort=True,
    ):
        group = group.sort_values("timestamp")
        directory = (
            TICKER_PERCENTILE_HISTORY_DIR
            / _safe_filename(timeframe)
            / TICKER_SCORE_PATHS_SECTION
        )

        if prices is None or prices.empty:
            continue
        ticker_prices = prices[prices["ticker"] == ticker].sort_values("timestamp")
        if ticker_prices.empty:
            continue
        start = group["timestamp"].min()
        end = group["timestamp"].max()
        ticker_prices = ticker_prices[
            ticker_prices["timestamp"].between(start, end)
        ]
        if not ticker_prices.empty:
            _save_combined_plot(
                group,
                ticker_prices,
                ticker,
                timeframe,
                directory,
                output_dir,
                moving_average_window,
            )

    if forward_return_points is not None and not forward_return_points.empty:
        for timeframe, timeframe_forward_returns in forward_return_points.groupby(
            "timeframe",
            sort=True,
        ):
            timeframe_forward_return_horizons = (
                forward_return_horizon_points[
                    forward_return_horizon_points["timeframe"] == timeframe
                ]
                if forward_return_horizon_points is not None
                and not forward_return_horizon_points.empty
                else pd.DataFrame()
            )
            directory = (
                TICKER_PERCENTILE_HISTORY_DIR
                / _safe_filename(timeframe)
            )
            _save_forward_return_heatmap(
                timeframe_forward_returns.sort_values("timestamp"),
                timeframe_forward_return_horizons.sort_values(
                    ["horizon_weeks", "timestamp"]
                )
                if not timeframe_forward_return_horizons.empty
                else timeframe_forward_return_horizons,
                prices,
                timeframe,
                directory,
                output_dir,
            )
