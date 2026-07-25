import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import plot_path
from app.testy.score_tests.common.io import save_csv_for_excel


MOVING_AVERAGE_COLUMN = "moving_average_score_percentile"
DEFAULT_MOVING_AVERAGE_WINDOW = 4


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
        label="Raw score percentile",
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
                    f"{moving_average_window}-point moving average "
                    "score percentile"
                ),
            )[0]
    price_line = price_ax.plot(
        price_group["timestamp"],
        price_group["close"],
        color=price_color,
        linewidth=2,
        alpha=0.85,
        label="Close price",
    )[0]

    percentile_ax.set_title(
        f"{ticker}: raw score percentile, moving average and closing price ({timeframe})"
    )
    percentile_ax.set_xlabel("Date")
    percentile_ax.set_ylabel("Score percentile", color=percentile_color)
    percentile_ax.set_ylim(0, 1)
    percentile_ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    percentile_ax.tick_params(axis="y", colors=percentile_color)
    percentile_ax.grid(True, alpha=0.25)

    price_ax.set_ylabel("Close price", color=price_color)
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
    heatmap_ax.set_ylabel("Ticker, sorted by full-period return")
    heatmap_ax.set_xlabel("Score date")
    heatmap_ax.set_title(
        f"{moving_average_window}-point moving average score percentile ({timeframe})"
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
    return_ax.set_title("Full return")
    return_ax.set_xlabel("Return")
    return_ax.set_ylim(len(heatmap_data.index) - 0.5, -0.5)
    return_ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    return_ax.tick_params(axis="y", left=False, labelleft=False)
    return_ax.grid(True, axis="x", alpha=0.25)

    colorbar = fig.colorbar(image, cax=colorbar_ax)
    colorbar.set_label("Score percentile MA")
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
    ax.set_ylabel("Ticker, sorted by mean forward annualized return")
    ax.set_xlabel("Score date")
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
        metric_label = column_metric_label or "Metric"
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
        label="Benchmark return z-score",
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
        label="Long-short normalized excess",
    )
    ax.plot(
        comparison["timestamp"],
        comparison["long_only_normalized_excess"],
        color="#F28E2B",
        linewidth=2.3,
        marker="o",
        markersize=3.5,
        label="Long-only normalized excess",
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
            label=f"Long-short mean {long_short_mean:.1%}",
        )
    if pd.notna(long_only_mean):
        ax.axhline(
            long_only_mean,
            color="#F28E2B",
            linewidth=1.5,
            linestyle="--",
            alpha=0.8,
            label=f"Long-only mean {long_only_mean:.1%}",
        )
    benchmark_ax.axhline(0, color="#777777", linewidth=0.9, linestyle=":", alpha=0.7)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_title(
        f"Normalized excess attribution by score date ({timeframe})"
    )
    ax.set_xlabel("Score date")
    ax.set_ylabel("Normalized excess return")
    benchmark_ax.set_ylabel("Benchmark return z-score")
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
        else "configured horizon"
    )

    heatmaps = [
        {
            "column": "score_zscore",
            "filename": "pearson_01_score_zscore_heatmap.png",
            "title": f"Pearson view: score z-score ({timeframe})",
            "colorbar": "Score z-score",
            "cmap": "RdYlGn",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["score_zscore"].mean(),
            "row_metric_label": "ScoreZ",
        },
        {
            "column": "forward_return_zscore",
            "filename": "pearson_02_forward_return_zscore_heatmap.png",
            "title": (
                f"Pearson view: forward return z-score "
                f"({timeframe}, {horizon_label})"
            ),
            "colorbar": "Forward return z-score",
            "cmap": "RdYlGn",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["forward_return_zscore"].mean(),
            "row_metric_label": "RetZ",
        },
        {
            "column": "zscore_error",
            "filename": "pearson_03_score_minus_return_zscore_heatmap.png",
            "title": (
                f"Pearson view: score z-score minus return z-score "
                f"({timeframe}, {horizon_label})"
            ),
            "colorbar": "Score z-score - forward return z-score",
            "cmap": "RdYlGn_r",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["zscore_error"].mean(),
            "row_metric_label": "DiffZ",
        },
        {
            "column": "score_percentile",
            "filename": "spearman_01_score_percentile_heatmap.png",
            "title": f"Spearman view: score percentile ({timeframe})",
            "colorbar": "Score percentile",
            "cmap": "RdYlGn",
            "vmin": 0,
            "vmax": 1,
            "percent_format": True,
            "row_metric": data.groupby("ticker")["score_percentile"].mean(),
            "row_metric_label": "ScorePct",
            "row_metric_format": "percent",
        },
        {
            "column": "forward_return_percentile",
            "filename": "spearman_02_forward_return_percentile_heatmap.png",
            "title": (
                f"Spearman view: forward return percentile "
                f"({timeframe}, {horizon_label})"
            ),
            "colorbar": "Forward return percentile",
            "cmap": "RdYlGn",
            "vmin": 0,
            "vmax": 1,
            "percent_format": True,
            "row_metric": data.groupby("ticker")["forward_return_percentile"].mean(),
            "row_metric_label": "RetPct",
            "row_metric_format": "percent",
        },
        {
            "column": "percentile_error",
            "filename": "spearman_03_score_minus_return_percentile_heatmap.png",
            "title": (
                f"Spearman view: score percentile minus return percentile "
                f"({timeframe}, {horizon_label})"
            ),
            "colorbar": "Score percentile - forward return percentile",
            "cmap": "RdYlGn_r",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["percentile_error"].mean(),
            "row_metric_label": "DiffPct",
            "row_metric_format": "signed_percent",
        },
        {
            "column": "excess_forward_annualized_return",
            "filename": "excess_forward_annualized_return_heatmap.png",
            "title": (
                f"Forward annualized return above timestamp benchmark "
                f"({timeframe}, {horizon_label})"
            ),
            "colorbar": "Excess forward annualized return",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")[
                "excess_forward_annualized_return"
            ].mean(),
            "row_metric_label": "AvgExRet",
            "row_metric_format": "signed_percent",
        },
        {
            "column": "return_attribution",
            "filename": "return_contribution_attribution_heatmap.png",
            "title": (
                f"Long-short return attribution: "
                f"(score percentile - 0.5) x excess forward return "
                f"({timeframe}, {horizon_label})"
            ),
            "colorbar": "Return contribution",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["return_attribution"].mean(),
            "row_metric_label": "AvgContr",
            "row_metric_format": "signed_percent",
            "column_metric": long_short_normalized_excess,
            "column_metric_label": "Long-short normalized excess",
            "column_metric_format": "signed_percent",
        },
        {
            "column": "long_only_return_attribution",
            "filename": "long_only_return_contribution_attribution_heatmap.png",
            "title": (
                f"Long-only return attribution: "
                f"max(score percentile - 0.5, 0) x excess forward return "
                f"({timeframe}, {horizon_label})"
            ),
            "colorbar": "Long-only return contribution",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")[
                "long_only_return_attribution"
            ].mean(),
            "row_metric_label": "AvgContr",
            "row_metric_format": "signed_percent",
            "column_metric": long_only_normalized_excess,
            "column_metric_label": "Long-only normalized excess",
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
            directory,
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
        directory,
        output_dir,
        long_short_normalized_excess,
        long_only_normalized_excess,
    )
    _save_score_return_correlation_by_timestamp_plot(
        data,
        timeframe,
        directory,
        output_dir,
    )


def _save_score_return_correlation_by_timestamp_plot(
    data,
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

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(
        correlations["timestamp"],
        correlations["pearson"],
        color="#4C78A8",
        linewidth=2,
        marker="o",
        markersize=3,
        label=f"Pearson, mean {pearson_mean:.3f}",
    )
    ax.plot(
        correlations["timestamp"],
        correlations["spearman"],
        color="#59A14F",
        linewidth=2,
        marker="o",
        markersize=3,
        label=f"Spearman, mean {spearman_mean:.3f}",
    )
    ax.plot(
        correlations["timestamp"],
        correlations["score_percentile_pearson_ic"],
        color="#F28E2B",
        linewidth=1.8,
        marker="o",
        markersize=2.8,
        label=(
            f"Score percentile Pearson IC, "
            f"mean {score_percentile_pearson_mean:.3f}"
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
        label="Benchmark return z-score",
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
        f"Score vs forward return correlation by score date "
        f"({timeframe}; Pearson mean {pearson_mean:.3f}, "
        f"Spearman mean {spearman_mean:.3f}, "
        f"Score pct Pearson IC mean {score_percentile_pearson_mean:.3f})"
    )
    ax.set_xlabel("Score date")
    ax.set_ylabel("Cross-sectional correlation")
    benchmark_ax.set_ylabel("Benchmark return z-score")
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
        label="Pearson mean",
    )
    ax.axhline(
        correlations[spearman_column].mean(),
        color="#59A14F",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
        label="Spearman mean",
    )
    ax.set_ylim(-1, 1)
    ax.set_title(
        f"Model score percentile vs forward return percentile correlation ({timeframe})"
    )
    ax.set_xlabel("Score date")
    ax.set_ylabel("Cross-sectional correlation")
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
        ax.set_xlabel("Correlation")
        ax.grid(True, axis="x", alpha=0.25)
        ax.set_ylim(len(correlations.index) - 0.5, -0.5)

    pearson_ax.set_yticks(y_positions)
    pearson_ax.set_yticklabels(correlations.index)
    pearson_ax.set_ylabel("Ticker")
    spearman_ax.tick_params(axis="y", left=False, labelleft=False)
    fig.suptitle(
        f"Raw score vs mean forward annualized return correlation ({timeframe})"
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
    if prices is not None and not prices.empty:
        prices = prices.copy()
        prices["timestamp"] = _to_utc_naive(prices["timestamp"])

    for (timeframe, ticker), group in metrics.groupby(
        ["timeframe", "ticker"],
        sort=True,
    ):
        group = group.sort_values("timestamp")
        directory = (
            Path("ticker_percentile_history")
            / _safe_filename(timeframe)
            / "ticker_plots"
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
            directory = (
                Path("ticker_percentile_history")
                / _safe_filename(timeframe)
                / "heatmaps"
            )
            _save_forward_return_heatmap(
                timeframe_forward_returns.sort_values("timestamp"),
                timeframe,
                directory,
                output_dir,
            )
