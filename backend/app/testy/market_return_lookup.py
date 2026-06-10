from datetime import timedelta

import numpy as np
import pandas as pd

from app.db.models.market_data import MarketData
from app.db.database import SessionLocal

def to_python_datetime(value):
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()

    return pd.Timestamp(value).to_pydatetime()


def load_market_data_frame(session, tickers, min_timestamp, max_timestamp):


    rows = (
        session.query(
            MarketData.ticker,
            MarketData.datetime,
            MarketData.open,
            MarketData.high,
            MarketData.low,
            MarketData.close,
        )
        .filter(
            MarketData.ticker.in_(sorted(tickers)),
            MarketData.datetime >= min_timestamp,
            MarketData.datetime <= max_timestamp,
        )
        .order_by(MarketData.ticker, MarketData.datetime)
        .all()
    )

    market_df = pd.DataFrame(
        rows,
        columns=["ticker", "datetime", "open", "high", "low", "close"],
    )

    if market_df.empty:
        return market_df

    market_df["datetime"] = pd.to_datetime(market_df["datetime"])
    market_df["ohlc4"] = market_df[["open", "high", "low", "close"]].mean(axis=1)
    return market_df


def build_market_lookup(market_df, smoothing_windows):
    lookup = {}
    smoothing_windows = sorted(set(smoothing_windows))

    for ticker, group in market_df.groupby("ticker", sort=False):
        group = group.sort_values("datetime")
        ohlc4 = group["ohlc4"].to_numpy(dtype=float)
        window_medians = {}

        for window_positions in smoothing_windows:
            if window_positions <= 0:
                window_medians[window_positions] = ohlc4
                continue

            window_medians[window_positions] = (
                pd.Series(ohlc4)
                .rolling(
                    window=window_positions * 2 + 1,
                    center=True,
                    min_periods=1,
                )
                .median()
                .to_numpy(dtype=float)
            )

        lookup[ticker] = {
            "datetimes": group["datetime"].to_numpy(dtype="datetime64[ns]"),
            "max_datetime": group["datetime"].max().to_datetime64(),
            "close": group["close"].to_numpy(dtype=float),
            "ohlc4": ohlc4,
            "window_medians": window_medians,
        }

    return lookup


def load_market_lookup_for_analysis(
    df,
    horizon_day_range_map,
    smoothing_window_map,
    buffer_days,
):


    max_horizon_days = max(
        max(horizon_days_values)
        for horizon_days_values in horizon_day_range_map.values()
    )
    min_timestamp = to_python_datetime(df["start_timestamp"].min()) - timedelta(
        days=buffer_days,
    )
    max_timestamp = to_python_datetime(df["start_timestamp"].max()) + timedelta(
        days=max_horizon_days + buffer_days,
    )

    with SessionLocal() as session:
        market_df = load_market_data_frame(
            session,
            tickers=set(df["ticker"].dropna().unique()),
            min_timestamp=min_timestamp,
            max_timestamp=max_timestamp,
        )

    if market_df.empty:
        return {}

    return build_market_lookup(
        market_df,
        smoothing_windows=smoothing_window_map.values(),
    )


def lookup_smoothed_ohlc4_many(
    market_lookup,
    tickers,
    timestamps,
    window_positions,
):
    result = np.full(len(tickers), np.nan, dtype=float)
    tickers_array = np.asarray(tickers)
    timestamps_array = pd.to_datetime(timestamps).to_numpy(dtype="datetime64[ns]")

    for ticker in pd.unique(tickers_array):
        ticker_data = market_lookup.get(ticker)

        if ticker_data is None:
            continue

        mask = tickers_array == ticker
        target_timestamps = timestamps_array[mask]
        inside_available_data = target_timestamps <= ticker_data["max_datetime"]
        anchor_indices = np.searchsorted(
            ticker_data["datetimes"],
            target_timestamps,
            side="right",
        ) - 1
        valid = (anchor_indices >= 0) & inside_available_data

        if not valid.any():
            continue

        window_values = ticker_data["window_medians"].get(window_positions)

        if window_values is None:
            continue

        target_positions = np.flatnonzero(mask)
        result[target_positions[valid]] = window_values[anchor_indices[valid]]

    return result


def lookup_asof_close_many(market_lookup, tickers, timestamps):
    result = np.full(len(tickers), np.nan, dtype=float)
    tickers_array = np.asarray(tickers)
    timestamps_array = pd.to_datetime(timestamps).to_numpy(dtype="datetime64[ns]")

    for ticker in pd.unique(tickers_array):
        ticker_data = market_lookup.get(ticker)

        if ticker_data is None:
            continue

        mask = tickers_array == ticker
        target_timestamps = timestamps_array[mask]
        anchor_indices = np.searchsorted(
            ticker_data["datetimes"],
            target_timestamps,
            side="right",
        ) - 1
        valid = anchor_indices >= 0

        if not valid.any():
            continue

        target_positions = np.flatnonzero(mask)
        result[target_positions[valid]] = ticker_data["close"][anchor_indices[valid]]

    return result


def add_current_prices(df, market_lookup):
    priced_df = df.copy()
    priced_df["current_price"] = lookup_asof_close_many(
        market_lookup,
        priced_df["ticker"],
        priced_df["start_timestamp"],
    )
    return priced_df


def build_horizon_return_frame(
    group,
    market_lookup,
    score_column,
    horizon_days,
    window_positions,
):
    horizon_df = group[
        ["ticker", "start_timestamp", score_column, "current_price"]
    ].copy()
    horizon_df["future_timestamp"] = (
        horizon_df["start_timestamp"] + pd.to_timedelta(horizon_days, unit="D")
    )
    horizon_df["future_price"] = lookup_smoothed_ohlc4_many(
        market_lookup,
        horizon_df["ticker"],
        horizon_df["future_timestamp"],
        window_positions,
    )
    horizon_df = horizon_df.dropna(subset=["current_price", "future_price"])
    horizon_df = horizon_df[horizon_df["current_price"] > 0].copy()
    horizon_df["future_return"] = (
        horizon_df["future_price"] - horizon_df["current_price"]
    ) / horizon_df["current_price"]
    return horizon_df
