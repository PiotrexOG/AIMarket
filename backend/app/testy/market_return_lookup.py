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
    return market_df


def build_market_lookup(market_df):
    lookup = {}

    for ticker, group in market_df.groupby("ticker", sort=False):
        group = group.sort_values("datetime")

        lookup[ticker] = {
            "datetimes": group["datetime"].to_numpy(dtype="datetime64[ns]"),
            "max_datetime": group["datetime"].max().to_datetime64(),
            "close": group["close"].to_numpy(dtype=float),
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

