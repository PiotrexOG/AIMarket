import numpy as np
import pandas as pd

from app.db.database import SessionLocal
from app.testy.market_return_lookup import load_market_data_frame


SOURCE_COLUMNS = [
    "timeframe",
    "ticker",
    "start_timestamp",
    "score",
    "score_percentile",
]

def _build_ticker_metrics(group):
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
    daily_percentile = (
        group["score_percentile"]
        .reindex(group.index.union(daily_index))
        .sort_index()
        .ffill()
        .reindex(daily_index)
        .astype(float)
    )

    daily_metrics = pd.DataFrame(index=daily_index)
    daily_metrics["current_score_percentile"] = daily_percentile
    daily_metrics["timeframe"] = group["timeframe"].iloc[0]
    daily_metrics["ticker"] = group["ticker"].iloc[0]
    daily_metrics.index.name = "timestamp"
    return daily_metrics.reset_index()


def _build_metrics(panel):
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
    frames = [
        _build_ticker_metrics(group)
        for _, group in source.groupby(["timeframe", "ticker"], sort=True)
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _build_prices(panel):
    if panel.empty:
        return pd.DataFrame(
            columns=["ticker", "timestamp", "open", "high", "low", "close"]
        )

    with SessionLocal() as session:
        prices = load_market_data_frame(
            session,
            tickers=set(panel["ticker"].dropna().unique()),
            min_timestamp=pd.Timestamp(panel["start_timestamp"].min()).to_pydatetime(),
            max_timestamp=pd.Timestamp(panel["start_timestamp"].max()).to_pydatetime(),
        )
    if prices.empty:
        return prices

    return prices.rename(columns={"datetime": "timestamp"})[
        ["ticker", "timestamp", "open", "high", "low", "close"]
    ]


def _round_numeric_columns(data):
    if data.empty:
        return data
    result = data.copy()
    for column in result.select_dtypes(include=[np.number]).columns:
        result[column] = result[column].round(6)
    return result


def calculate(context):
    panel = context.score_observations
    if panel is None:
        panel = context.return_panel

    return {
        "metrics": _round_numeric_columns(_build_metrics(panel)),
        "prices": _round_numeric_columns(_build_prices(panel)),
    }
