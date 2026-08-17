import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import annualize_return

from .plot_config import ANTI_MOMENTUM_WINDOWS
from .sample_metadata import (
    BASE_OBSERVATION_COUNT_COLUMN,
    base_observation_count,
    horizon_observation_weights,
)
from .statistics import _safe_correlation


def _price_lookup_by_ticker(prices):
    lookups = {}
    if prices is None or prices.empty:
        return lookups

    clean_prices = (
        prices[["ticker", "timestamp", "close"]]
        .dropna(subset=["ticker", "timestamp", "close"])
        .copy()
    )
    if clean_prices.empty:
        return lookups

    clean_prices["timestamp"] = pd.to_datetime(clean_prices["timestamp"])
    clean_prices = clean_prices.sort_values(["ticker", "timestamp"])
    for ticker, group in clean_prices.groupby("ticker", sort=True):
        series = group.drop_duplicates("timestamp", keep="last").set_index(
            "timestamp"
        )["close"]
        lookups[ticker] = series.sort_index()
    return lookups


def _lookup_price_at_or_before(price_series, timestamp, tolerance_days=3):
    if price_series is None or price_series.empty:
        return np.nan
    timestamp = pd.Timestamp(timestamp)
    value = price_series.asof(timestamp)
    if pd.isna(value):
        return np.nan
    matched_index = price_series.index[price_series.index <= timestamp]
    if matched_index.empty:
        return np.nan
    matched_timestamp = matched_index[-1]
    if timestamp - matched_timestamp > pd.Timedelta(days=tolerance_days):
        return np.nan
    return float(value)


def _mean_trailing_window_return(
    row,
    price_lookup,
    start_week,
    end_week,
    skip_weeks=0,
):
    ticker_prices = price_lookup.get(row["ticker"])
    if ticker_prices is None:
        return np.nan

    timestamp = pd.Timestamp(row["timestamp"])
    end_timestamp = timestamp - pd.Timedelta(weeks=skip_weeks)
    end_price = _lookup_price_at_or_before(ticker_prices, end_timestamp)
    if pd.isna(end_price) or end_price <= 0:
        return np.nan

    trailing_returns = []
    for horizon_week in range(start_week, end_week + 1):
        past_timestamp = end_timestamp - pd.Timedelta(weeks=horizon_week)
        past_price = _lookup_price_at_or_before(ticker_prices, past_timestamp)
        if pd.isna(past_price) or past_price <= 0:
            continue
        total_return = end_price / past_price - 1
        horizon_days = max(1, (end_timestamp - past_timestamp).days)
        annualized = annualize_return(total_return, horizon_days)
        if annualized is not None:
            trailing_returns.append(annualized)

    return float(np.mean(trailing_returns)) if trailing_returns else np.nan


def _momentum_windows_for_row(row):
    windows = []
    for label, start_week, end_week, skip_weeks in ANTI_MOMENTUM_WINDOWS:
        if start_week is None or end_week is None:
            if (
                pd.isna(row.get("horizon_week_start"))
                or pd.isna(row.get("horizon_week_end"))
            ):
                continue
            start_week = int(row["horizon_week_start"])
            end_week = int(row["horizon_week_end"])
        windows.append((label, int(start_week), int(end_week), int(skip_weeks)))
    return windows


def _build_anti_momentum_points(data, prices):
    if prices is None or prices.empty:
        return pd.DataFrame()

    required = {
        "ticker",
        "timestamp",
        "score",
        "score_percentile",
        "mean_forward_annualized_return",
        "forward_return_percentile",
        "horizon_week_start",
        "horizon_week_end",
    }
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame()

    price_lookup = _price_lookup_by_ticker(prices)
    if not price_lookup:
        return pd.DataFrame()

    point_columns = [
        "ticker",
        "timestamp",
        "score",
        "score_percentile",
        "mean_forward_annualized_return",
        "forward_return_percentile",
        "horizon_week_start",
        "horizon_week_end",
    ]
    if "horizon_count" in data.columns:
        point_columns.append("horizon_count")
    points = data[point_columns].dropna(
        subset=["ticker", "timestamp", "score"]
    ).copy()
    if points.empty:
        return pd.DataFrame()
    if "horizon_count" not in points.columns:
        points["horizon_count"] = horizon_observation_weights(points)

    for label, _, _, _ in ANTI_MOMENTUM_WINDOWS:
        column = f"trailing_{label}_annualized_return"
        points[column] = [
            _mean_trailing_window_return(
                row,
                price_lookup,
                start_week,
                end_week,
                skip_weeks,
            )
            for _, row in points.iterrows()
            for (
                window_label,
                start_week,
                end_week,
                skip_weeks,
            ) in _momentum_windows_for_row(row)
            if window_label == label
        ]
    return points


def _ticker_score_correlation_table(points, ticker_order, value_column):
    rows = []
    for ticker, group in points.groupby("ticker", sort=True):
        correlation = _safe_correlation(
            group,
            "score",
            value_column,
            "pearson",
        )
        clean = group.dropna(subset=["score", value_column])
        rows.append({
            "ticker": ticker,
            "correlation": correlation,
            "observations": len(clean),
            BASE_OBSERVATION_COUNT_COLUMN: base_observation_count(
                clean,
                required_columns=("score", value_column),
            ),
            "mean_score": clean["score"].mean() if not clean.empty else np.nan,
            f"mean_{value_column}": (
                clean[value_column].mean() if not clean.empty else np.nan
            ),
        })

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    ordered_tickers = [
        ticker
        for ticker in ticker_order
        if ticker in set(result["ticker"])
    ]
    ordered_tickers.extend(
        ticker
        for ticker in sorted(result["ticker"])
        if ticker not in set(ordered_tickers)
    )
    return result.set_index("ticker").reindex(ordered_tickers).reset_index()
