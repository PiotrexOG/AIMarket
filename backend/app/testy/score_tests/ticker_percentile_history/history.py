import numpy as np
import pandas as pd

from app.db.database import SessionLocal
from app.testy.market_return_lookup import load_market_data_frame

from .config import (
    ANTI_MOMENTUM_PRICE_LOOKBACK_WEEKS,
    ANTI_MOMENTUM_SKIP_WEEKS,
    MOVING_AVERAGE_COLUMN,
    SOURCE_COLUMNS,
)


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
