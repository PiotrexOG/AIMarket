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


def build_market_lookup(market_df):
    lookup = {}

    for ticker, group in market_df.groupby("ticker", sort=False):
        group = group.sort_values("datetime")
        ohlc4 = group["ohlc4"].to_numpy(dtype=float)
        valid_ohlc4 = np.isfinite(ohlc4)

        lookup[ticker] = {
            "datetimes": group["datetime"].to_numpy(dtype="datetime64[ns]"),
            "max_datetime": group["datetime"].max().to_datetime64(),
            "close": group["close"].to_numpy(dtype=float),
            "ohlc4": ohlc4,
            "ohlc4_cumsum": np.concatenate((
                [0.0],
                np.cumsum(np.where(valid_ohlc4, ohlc4, 0.0)),
            )),
            "ohlc4_count_cumsum": np.concatenate((
                [0],
                np.cumsum(valid_ohlc4.astype(int)),
            )),
        }

    return lookup


def load_market_lookup_for_analysis(
    df,
    max_timestamp,
):


    min_timestamp = to_python_datetime(df["start_timestamp"].min())
    max_timestamp = to_python_datetime(max_timestamp)

    with SessionLocal() as session:
        market_df = load_market_data_frame(
            session,
            tickers=set(df["ticker"].dropna().unique()),
            min_timestamp=min_timestamp,
            max_timestamp=max_timestamp,
        )

    if market_df.empty:
        return {}

    return build_market_lookup(market_df)


def lookup_window_average_ohlc4_many(
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

        target_positions = np.flatnonzero(mask)
        valid_anchor_indices = anchor_indices[valid]
        start_indices = np.maximum(0, valid_anchor_indices - window_positions)
        end_indices = np.minimum(
            len(ticker_data["ohlc4"]) - 1,
            valid_anchor_indices + window_positions,
        )
        cumsum = ticker_data["ohlc4_cumsum"]
        count_cumsum = ticker_data["ohlc4_count_cumsum"]
        window_sums = cumsum[end_indices + 1] - cumsum[start_indices]
        window_counts = count_cumsum[end_indices + 1] - count_cumsum[start_indices]
        result[target_positions[valid]] = np.divide(
            window_sums,
            window_counts,
            out=np.full(len(window_sums), np.nan, dtype=float),
            where=window_counts > 0,
        )

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
    horizon_df["future_price"] = lookup_window_average_ohlc4_many(
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
