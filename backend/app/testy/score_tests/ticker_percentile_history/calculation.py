import numpy as np

from .config import (
    ANTI_MOMENTUM_PRICE_LOOKBACK_WEEKS,
    ANTI_MOMENTUM_SKIP_WEEKS,
    FORWARD_RETURN_HORIZON_POINT_COLUMNS,
    FORWARD_RETURN_POINT_COLUMNS,
    MOVING_AVERAGE_COLUMN,
    MOVING_AVERAGE_WINDOW,
    SCORE_POINT_COLUMNS,
    SOURCE_COLUMNS,
)
from .forward_returns import (
    _build_forward_return_horizon_points,
    _build_forward_return_points,
)
from .history import (
    _add_rank_percentile,
    _build_metrics,
    _build_prices,
    _build_score_points,
    _build_source,
    _build_ticker_metrics,
    _build_ticker_score_points,
    _daily_forward_fill,
    _max_horizon_lookback_days,
)


def _round_numeric_columns(data):
    if data.empty:
        return data
    result = data.copy()
    for column in result.select_dtypes(include=[np.number]).columns:
        result[column] = result[column].round(6)
    return result


def calculate(
    context,
    moving_average_window=MOVING_AVERAGE_WINDOW,
    horizon_week_ranges=None,
):
    panel = context.score_observations
    if panel is None:
        panel = context.return_panel
    moving_average_window = max(1, int(moving_average_window))

    return {
        "metrics": _round_numeric_columns(
            _build_metrics(panel, moving_average_window)
        ),
        "score_points": _round_numeric_columns(
            _build_score_points(panel, moving_average_window)
        ),
        "forward_return_points": _round_numeric_columns(
            _build_forward_return_points(context.return_panel, horizon_week_ranges)
        ),
        "forward_return_horizon_points": _round_numeric_columns(
            _build_forward_return_horizon_points(
                context.return_panel,
                horizon_week_ranges,
            )
        ),
        "prices": _round_numeric_columns(
            _build_prices(panel, horizon_week_ranges)
        ),
        "moving_average_window": moving_average_window,
    }
