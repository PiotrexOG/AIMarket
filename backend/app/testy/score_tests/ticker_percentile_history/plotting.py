import pandas as pd

from app.testy.score_tests.common.output_paths import (
    TICKER_PERCENTILE_HISTORY_DIR,
    TICKER_SCORE_PATHS_SECTION,
)

from .correlation_plots import (
    _save_forward_return_cross_section_correlation_plot,
    _save_raw_score_forward_return_correlation_plot,
    _save_score_return_correlation_by_timestamp_plot,
)
from .forward_return_plots import _save_forward_return_heatmap
from .hac_plots import (
    _format_ci_half_width_clean,
    _save_score_return_autocorrelation_plot,
    _save_score_return_autocorrelation_plots,
    _save_score_return_hac_diagnostics,
    _save_score_return_hac_summary_plot,
)
from .momentum_data import (
    _build_anti_momentum_points,
    _lookup_price_at_or_before,
    _mean_trailing_window_return,
    _momentum_windows_for_row,
    _price_lookup_by_ticker,
    _ticker_score_correlation_table,
)
from .momentum_plots import (
    _build_model_vs_momentum_comparison,
    _plot_model_vs_momentum_panel,
    _save_anti_momentum_correlation_charts,
    _save_model_vs_momentum_comparison_charts,
    _save_ticker_correlation_bar_chart,
)
from .normalization import (
    _format_metric_value,
    _normalized_excess_by_timestamp,
    _rank_percentile_by_group,
    _zscore_by_group,
)
from .plot_config import (
    ANTI_MOMENTUM_SKIP_WEEKS,
    ANTI_MOMENTUM_WINDOWS,
    DEFAULT_MOVING_AVERAGE_WINDOW,
    HAC_DIAGNOSTIC_METRICS,
    MOVING_AVERAGE_COLUMN,
    Z_CRITICAL_95,
)
from .plot_io import (
    _safe_filename,
    _save_figure,
    _save_heatmap_csv,
    _to_utc_naive,
)
from .return_comparison_plots import _save_normalized_excess_comparison_plot
from .score_path_plots import (
    _calculate_full_period_returns,
    _save_all_tickers_moving_average_heatmap,
    _save_combined_plot,
)
from .statistics import (
    _autocorrelation_by_lag,
    _format_ci_half_width,
    _metric_horizon_summary,
    _metric_official_summary,
    _newey_west_lags_from_horizon,
    _newey_west_mean_stats,
    _official_result_mask,
    _safe_correlation,
    _score_return_horizon_correlations,
    _score_return_horizon_hac_summary,
    _score_return_horizon_metadata,
)
from .ticker_heatmap import _save_ticker_date_heatmap


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
