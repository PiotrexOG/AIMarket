import numpy as np
import pandas as pd

from app.db.database import SessionLocal
from app.testy.market_return_lookup import load_market_data_frame
from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.data import filter_horizon_week_ranges


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
SCORE_POINT_COLUMNS = [
    "timestamp",
    "current_score_percentile",
    MOVING_AVERAGE_COLUMN,
    "timeframe",
    "ticker",
]
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


def _build_source(panel):
    if panel.empty or not set(SOURCE_COLUMNS).issubset(panel.columns):
        return pd.DataFrame()

    source = (
        panel[SOURCE_COLUMNS]
        .dropna(
            subset=[
                "timeframe",
                "ticker",
                "start_timestamp",
                "score_percentile",
            ]
        )
        .copy()
    )
    source["start_timestamp"] = pd.to_datetime(source["start_timestamp"])
    source = _add_rank_percentile(
        source,
        value_column="score",
        output_column="score_percentile",
        group_columns=["timeframe", "start_timestamp"],
    )
    return source


def _add_rank_percentile(data, value_column, output_column, group_columns):
    result = data.copy()
    ranks = result.groupby(group_columns)[value_column].rank(
        method="average",
        ascending=True,
    )
    counts = result.groupby(group_columns)[value_column].transform("count")
    result[output_column] = np.where(
        counts > 1,
        (ranks - 1) / (counts - 1),
        0.5,
    )
    return result


def _daily_forward_fill(series, daily_index):
    return (
        series.reindex(series.index.union(daily_index))
        .sort_index()
        .ffill()
        .reindex(daily_index)
        .astype(float)
    )


def _build_ticker_metrics(group, moving_average_window):
    group = group.sort_values("start_timestamp").copy()
    group["start_timestamp"] = group["start_timestamp"].dt.normalize()
    group = group.drop_duplicates("start_timestamp", keep="last").set_index(
        "start_timestamp"
    )
    daily_index = pd.date_range(
        group.index.min().normalize(),
        group.index.max().normalize(),
        freq="D",
    )
    rolling_percentile = group["score_percentile"].rolling(
        window=moving_average_window,
        min_periods=1,
    ).mean()
    daily_percentile = _daily_forward_fill(group["score_percentile"], daily_index)
    daily_rolling_percentile = _daily_forward_fill(
        rolling_percentile,
        daily_index,
    )

    daily_metrics = pd.DataFrame(index=daily_index)
    daily_metrics["current_score_percentile"] = daily_percentile
    daily_metrics[MOVING_AVERAGE_COLUMN] = daily_rolling_percentile
    daily_metrics["timeframe"] = group["timeframe"].iloc[0]
    daily_metrics["ticker"] = group["ticker"].iloc[0]
    daily_metrics.index.name = "timestamp"
    return daily_metrics.reset_index()


def _build_ticker_score_points(group, moving_average_window):
    group = group.sort_values("start_timestamp").copy()
    group["start_timestamp"] = group["start_timestamp"].dt.normalize()
    group = group.drop_duplicates("start_timestamp", keep="last")
    group[MOVING_AVERAGE_COLUMN] = group["score_percentile"].rolling(
        window=moving_average_window,
        min_periods=1,
    ).mean()
    group = group.rename(
        columns={
            "start_timestamp": "timestamp",
            "score_percentile": "current_score_percentile",
        }
    )
    return group[SCORE_POINT_COLUMNS]


def _build_metrics(panel, moving_average_window):
    moving_average_window = max(1, int(moving_average_window))
    source = _build_source(panel)
    if source.empty:
        return pd.DataFrame()

    frames = [
        _build_ticker_metrics(group, moving_average_window)
        for _, group in source.groupby(["timeframe", "ticker"], sort=True)
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _build_score_points(panel, moving_average_window):
    moving_average_window = max(1, int(moving_average_window))
    source = _build_source(panel)
    if source.empty:
        return pd.DataFrame(columns=SCORE_POINT_COLUMNS)

    frames = [
        _build_ticker_score_points(group, moving_average_window)
        for _, group in source.groupby(["timeframe", "ticker"], sort=True)
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=SCORE_POINT_COLUMNS
    )


def _max_horizon_lookback_days(horizon_week_ranges):
    max_lookback_days = (
        ANTI_MOMENTUM_PRICE_LOOKBACK_WEEKS
        + ANTI_MOMENTUM_SKIP_WEEKS
    ) * 7
    if not horizon_week_ranges:
        return max_lookback_days
    horizon_lookback_days = max(
        (end_week + ANTI_MOMENTUM_SKIP_WEEKS) * 7
        for _, end_week in horizon_week_ranges.values()
    )
    return max(max_lookback_days, horizon_lookback_days)


def _build_prices(panel, horizon_week_ranges=None):
    if panel.empty:
        return pd.DataFrame(
            columns=["ticker", "timestamp", "open", "high", "low", "close"]
        )

    lookback_days = _max_horizon_lookback_days(horizon_week_ranges)
    min_timestamp = pd.Timestamp(panel["start_timestamp"].min())
    if lookback_days > 0:
        min_timestamp = min_timestamp - pd.Timedelta(days=lookback_days)

    with SessionLocal() as session:
        prices = load_market_data_frame(
            session,
            tickers=set(panel["ticker"].dropna().unique()),
            min_timestamp=min_timestamp.to_pydatetime(),
            max_timestamp=pd.Timestamp(panel["start_timestamp"].max()).to_pydatetime(),
        )
    if prices.empty:
        return prices

    return prices.rename(columns={"datetime": "timestamp"})[
        ["ticker", "timestamp", "open", "high", "low", "close"]
    ]


def _build_forward_return_points(return_panel, horizon_week_ranges=None):
    required = {
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "future_return",
        "horizon_weeks",
        "horizon_days",
    }
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    panel = filter_horizon_week_ranges(
        return_panel,
        horizon_week_ranges=horizon_week_ranges,
    )
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    expected_horizon_counts = {}
    if horizon_week_ranges:
        expected_horizon_counts = {
            timeframe: end_week - start_week + 1
            for timeframe, (start_week, end_week) in horizon_week_ranges.items()
        }

    panel = add_annualized_return_column(
        panel,
        return_column="future_return",
        horizon_column="horizon_days",
    ).dropna(subset=["annualized_return"])
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    grouped = (
        panel.groupby(["timeframe", "ticker", "start_timestamp"], as_index=False)
        .agg(
            score=("score", "last"),
            score_percentile=("score_percentile", "last"),
            mean_forward_annualized_return=("annualized_return", "mean"),
            horizon_week_start=("horizon_weeks", "min"),
            horizon_week_end=("horizon_weeks", "max"),
            horizon_count=("horizon_weeks", "nunique"),
        )
        .rename(columns={"start_timestamp": "timestamp"})
    )
    if expected_horizon_counts:
        grouped["expected_horizon_count"] = grouped["timeframe"].map(
            expected_horizon_counts
        )
        grouped = grouped[
            grouped["horizon_count"] == grouped["expected_horizon_count"]
        ].copy()
        if grouped.empty:
            return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    grouped = _add_rank_percentile(
        grouped,
        value_column="score",
        output_column="score_percentile",
        group_columns=["timeframe", "timestamp"],
    )
    grouped["forward_return_rank"] = grouped.groupby(
        ["timeframe", "timestamp"]
    )["mean_forward_annualized_return"].rank(method="average", ascending=True)
    grouped["forward_return_count"] = grouped.groupby(
        ["timeframe", "timestamp"]
    )["mean_forward_annualized_return"].transform("count")
    grouped["forward_return_percentile"] = np.where(
        grouped["forward_return_count"] > 1,
        (grouped["forward_return_rank"] - 1)
        / (grouped["forward_return_count"] - 1),
        0.5,
    )
    grouped["cross_section_pearson_score_to_forward_percentile"] = (
        grouped.groupby(["timeframe", "timestamp"], group_keys=False)
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="pearson",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(grouped[["timeframe", "timestamp"]])
        )
        .to_numpy()
    )
    grouped["cross_section_spearman_score_to_forward_percentile"] = (
        grouped.groupby(["timeframe", "timestamp"], group_keys=False)
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="spearman",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(grouped[["timeframe", "timestamp"]])
        )
        .to_numpy()
    )

    return grouped[FORWARD_RETURN_POINT_COLUMNS]


def _build_forward_return_horizon_points(return_panel, horizon_week_ranges=None):
    required = {
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "future_return",
        "horizon_weeks",
        "horizon_days",
    }
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame(columns=FORWARD_RETURN_HORIZON_POINT_COLUMNS)

    panel = filter_horizon_week_ranges(
        return_panel,
        horizon_week_ranges=horizon_week_ranges,
    )
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_HORIZON_POINT_COLUMNS)

    panel = add_annualized_return_column(
        panel,
        return_column="future_return",
        horizon_column="horizon_days",
    ).dropna(subset=["annualized_return"])
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_HORIZON_POINT_COLUMNS)

    grouped = (
        panel.groupby(
            ["timeframe", "horizon_weeks", "ticker", "start_timestamp"],
            as_index=False,
        )
        .agg(
            score=("score", "last"),
            score_percentile=("score_percentile", "last"),
            forward_annualized_return=("annualized_return", "mean"),
            horizon_days=("horizon_days", "mean"),
        )
        .rename(columns={"start_timestamp": "timestamp"})
    )
    grouped = _add_rank_percentile(
        grouped,
        value_column="score",
        output_column="score_percentile",
        group_columns=["timeframe", "horizon_weeks", "timestamp"],
    )
    grouped["forward_return_rank"] = grouped.groupby(
        ["timeframe", "horizon_weeks", "timestamp"]
    )["forward_annualized_return"].rank(method="average", ascending=True)
    grouped["forward_return_count"] = grouped.groupby(
        ["timeframe", "horizon_weeks", "timestamp"]
    )["forward_annualized_return"].transform("count")
    grouped["forward_return_percentile"] = np.where(
        grouped["forward_return_count"] > 1,
        (grouped["forward_return_rank"] - 1)
        / (grouped["forward_return_count"] - 1),
        0.5,
    )
    grouped["cross_section_pearson_score_to_forward_percentile"] = (
        grouped.groupby(
            ["timeframe", "horizon_weeks", "timestamp"],
            group_keys=False,
        )
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="pearson",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(
                grouped[["timeframe", "horizon_weeks", "timestamp"]]
            )
        )
        .to_numpy()
    )
    grouped["cross_section_spearman_score_to_forward_percentile"] = (
        grouped.groupby(
            ["timeframe", "horizon_weeks", "timestamp"],
            group_keys=False,
        )
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="spearman",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(
                grouped[["timeframe", "horizon_weeks", "timestamp"]]
            )
        )
        .to_numpy()
    )

    return grouped[FORWARD_RETURN_HORIZON_POINT_COLUMNS]


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
