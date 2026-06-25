import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from app.testy.score_tests.common.plotting import plot_path


def _safe_filename(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._") or "unknown"


def _to_utc_naive(values):
    return pd.to_datetime(values, utc=True).dt.tz_localize(None)


def _save_combined_plot(
    metric_group,
    price_group,
    ticker,
    timeframe,
    directory,
    output_dir,
):
    percentile_color = "#4C78A8"
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
    price_line = price_ax.plot(
        price_group["timestamp"],
        price_group["close"],
        color=price_color,
        linewidth=2,
        alpha=0.85,
        label="Close price",
    )[0]

    percentile_ax.set_title(
        f"{ticker}: raw score percentile and closing price ({timeframe})"
    )
    percentile_ax.set_xlabel("Date")
    percentile_ax.set_ylabel("Score percentile", color=percentile_color)
    percentile_ax.set_ylim(0, 1)
    percentile_ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    percentile_ax.tick_params(axis="y", colors=percentile_color)
    percentile_ax.grid(True, alpha=0.25)

    price_ax.set_ylabel("Close price", color=price_color)
    price_ax.tick_params(axis="y", colors=price_color)
    percentile_ax.legend(
        handles=[percentile_line, price_line],
        loc="best",
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{ticker}_score_percentile_with_price.png"),
        dpi=180,
    )
    plt.close(fig)


def plot(results, output_dir):
    if not results:
        return

    metrics = results.get("metrics")
    prices = results.get("prices")
    if metrics is None or metrics.empty:
        return

    metrics = metrics.copy()
    metrics["timestamp"] = _to_utc_naive(metrics["timestamp"])
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
            )
