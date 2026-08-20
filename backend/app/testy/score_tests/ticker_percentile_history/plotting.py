import pandas as pd

from app.testy.score_tests.common.output_paths import (
    TICKER_PERCENTILE_HISTORY_DIR,
    TICKER_SCORE_PATHS_SECTION,
)

from .forward_return_plots import _save_forward_return_heatmap
from .plot_config import DEFAULT_MOVING_AVERAGE_WINDOW
from .plot_io import _safe_filename, _to_utc_naive
from .score_path_plots import _save_combined_plot


def plot(results, output_dir):
    if not results:
        return

    metrics = results.get("metrics")
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
        horizon_data = (
            forward_return_points[forward_return_points["timeframe"] == timeframe]
            if forward_return_points is not None
            and not forward_return_points.empty
            and "timeframe" in forward_return_points.columns
            else None
        )
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
                horizon_data,
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
