import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    plot_path,
    timeframe_label,
)

from .plot_config import MOVING_AVERAGE_COLUMN
from .plot_io import _save_figure, _save_heatmap_csv


def _save_combined_plot(
    metric_group,
    price_group,
    ticker,
    timeframe,
    directory,
    output_dir,
    moving_average_window,
    horizon_data=None,
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
        f"zamknięcia ({timeframe_label(timeframe, horizon_data)})"
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

    metric_count = int(metric_group["current_score_percentile"].notna().sum())
    price_count = int(price_group["close"].notna().sum())
    add_sample_size_note(
        fig,
        note=(
            f"n={metric_count} dziennych obserwacji percentyla score; "
            f"n={price_count} obserwacji ceny zamknięcia"
        ),
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
    horizon_data=None,
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
        f"({timeframe_label(timeframe, horizon_data)})"
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

    valid_cells = int(np.isfinite(heatmap_data.to_numpy(dtype=float)).sum())
    add_sample_size_note(
        fig,
        note=(
            f"n={valid_cells} niepustych obserwacji ticker\N{MULTIPLICATION SIGN}data; "
            f"{len(heatmap_data.index)} spółek; {len(heatmap_data.columns)} dat"
        ),
    )

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
