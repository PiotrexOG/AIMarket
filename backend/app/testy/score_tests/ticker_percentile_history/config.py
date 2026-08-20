
SOURCE_COLUMNS = [
    "timeframe",
    "ticker",
    "start_timestamp",
    "score",
    "score_percentile",
]


MOVING_AVERAGE_WINDOW = 4
MOVING_AVERAGE_COLUMN = "moving_average_score_percentile"
ANTI_MOMENTUM_PRICE_LOOKBACK_WEEKS = 52
ANTI_MOMENTUM_SKIP_WEEKS = 4
FORWARD_RETURN_POINT_COLUMNS = [
    "timestamp",
    "score",
    "score_percentile",
    "mean_forward_annualized_return",
    "forward_return_percentile",
    "cross_section_pearson_score_to_forward_percentile",
    "cross_section_spearman_score_to_forward_percentile",
    "horizon_week_start",
    "horizon_week_end",
    "horizon_count",
    "timeframe",
    "ticker",
]
FORWARD_RETURN_HORIZON_POINT_COLUMNS = [
    "timestamp",
    "score",
    "score_percentile",
    "forward_annualized_return",
    "forward_return_percentile",
    "cross_section_pearson_score_to_forward_percentile",
    "cross_section_spearman_score_to_forward_percentile",
    "horizon_weeks",
    "horizon_days",
    "timeframe",
    "ticker",
]
