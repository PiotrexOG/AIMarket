import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from score_correlation_plotting import (
    plot_average_metric_values,
    plot_horizon_pearson,
    plot_horizon_quantile_pearson,
    plot_metric_summary,
    plot_return_distribution,
    plot_scatter_by_timeframe,
    plot_score_buckets,
    plot_ticker_score_timeline,
    plot_timeframe_ticker_score_timeline,
)
from top_bucket_performance import (
    ABSOLUTE_SCORE_THRESHOLDS,
    DEBUG_BENCHMARK_HORIZON_DAYS,
    add_benchmark_columns,
    build_benchmark_debug_dict,
    build_policy_stability_summary,
    build_score_distribution_summaries,
)
from top_bucket_performance_plotting import (
    plot_absolute_threshold_performance,
    plot_score_distributions,
    plot_top_bucket_performance,
)


ROOT_FOLDER = Path(__file__).resolve().parents[2]

if str(ROOT_FOLDER) not in sys.path:
    sys.path.append(str(ROOT_FOLDER))

CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"

INPUT_FILE = CROSS_SECTION_DIR / "score_vs_returns.json"
OUTPUT_DIR = CROSS_SECTION_DIR / "correlation_plots"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"

# Same smoothing windows as in cross_section_pipeline.py. The horizon analysis
# changes only the end-date distance, not the left/right price smoothing window.
TIMEFRAME_PRICE_WINDOW_MAP = {
    "short_term_14d": 6,
    "medium_term_50d": 21,
    "long_term_200d": 84,
}

HORIZON_DAY_RANGE_MAP = {
    "short_term_14d": range(1, 420),
    "medium_term_50d": range(1, 420),
    "long_term_200d": range(1, 420),
}

TOP_SCORE_SHARES = [0.10, 0.20, 0.30, 0.40, 0.50]

MARKET_DATA_BUFFER_DAYS = 420


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_dataframe(data):
    rows = []

    for timeframe, timeframe_data in data.get("by_timeframe", {}).items():
        for observation in timeframe_data.get("observations", []):
            row = {
                "timeframe": timeframe,
                "ticker": observation["ticker"],
                "start_timestamp": observation["start_timestamp"],
                "future_return": observation["future_return"],
            }

            relative_scores = observation.get("relative_scores")

            if relative_scores:
                row.update(relative_scores)
            elif "score" in observation:
                row[EQUAL_WEIGHT_SCORE_COLUMN] = observation["score"]

            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["start_timestamp"] = pd.to_datetime(df["start_timestamp"])
    df["future_return"] = pd.to_numeric(df["future_return"], errors="coerce")

    score_columns = get_score_columns(df, include_equal_weight=False)

    for column in score_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if score_columns and EQUAL_WEIGHT_SCORE_COLUMN not in df.columns:
        df[EQUAL_WEIGHT_SCORE_COLUMN] = df[score_columns].mean(axis=1)

    if EQUAL_WEIGHT_SCORE_COLUMN in df.columns:
        df[EQUAL_WEIGHT_SCORE_COLUMN] = pd.to_numeric(
            df[EQUAL_WEIGHT_SCORE_COLUMN],
            errors="coerce",
        )

    return df.dropna(subset=["future_return"])


def get_score_columns(df, include_equal_weight=True):
    columns = [
        column
        for column in df.columns
        if column.startswith("relative_")
    ]

    if include_equal_weight and EQUAL_WEIGHT_SCORE_COLUMN in df.columns:
        return [EQUAL_WEIGHT_SCORE_COLUMN] + sorted(columns)

    return sorted(columns)


def calculate_correlations(group, score_column, return_column="future_return"):
    if score_column not in group.columns or return_column not in group.columns:
        return {
            "count": 0,
            "pearson": None,
            "pearson_p": None,
            "spearman": None,
            "spearman_p": None,
        }

    clean = group[[score_column, return_column]].dropna()

    if (
        len(clean) < 3
        or clean[score_column].nunique() < 2
        or clean[return_column].nunique() < 2
    ):
        return {
            "count": len(clean),
            "pearson": None,
            "pearson_p": None,
            "spearman": None,
            "spearman_p": None,
        }

    pearson_corr, pearson_p = pearsonr(clean[score_column], clean[return_column])
    spearman_corr, spearman_p = spearmanr(clean[score_column], clean[return_column])

    return {
        "count": len(clean),
        "pearson": round(float(pearson_corr), 6),
        "pearson_p": round(float(pearson_p), 6),
        "spearman": round(float(spearman_corr), 6),
        "spearman_p": round(float(spearman_p), 6),
    }


def save_summary(df, score_columns):
    rows = []

    for score_column in score_columns:
        for timeframe, group in df.groupby("timeframe"):
            row = {
                "timeframe": timeframe,
                "ticker": "ALL",
                "score_column": score_column,
                "baseline_return": round(float(group["future_return"].mean()), 6),
            }
            row.update(calculate_correlations(group, score_column))
            rows.append(row)

        for (timeframe, ticker), group in df.groupby(["timeframe", "ticker"]):
            row = {
                "timeframe": timeframe,
                "ticker": ticker,
                "score_column": score_column,
                "baseline_return": round(float(group["future_return"].mean()), 6),
            }
            row.update(calculate_correlations(group, score_column))
            rows.append(row)

    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT_DIR / "correlation_summary.csv", index=False)

    return summary


def to_python_datetime(value):
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()

    return pd.Timestamp(value).to_pydatetime()


def calculate_return_stats(group):
    if "future_return" not in group.columns or group.empty:
        return {
            "avg_return": None,
            "median_return": None,
            "win_rate": None,
        }

    returns = group["future_return"].dropna()

    if returns.empty:
        return {
            "avg_return": None,
            "median_return": None,
            "win_rate": None,
        }

    return {
        "avg_return": round(float(returns.mean()), 6),
        "median_return": round(float(returns.median()), 6),
        "win_rate": round(float((returns > 0).mean()), 6),
    }


def calculate_sample_stats(group):
    if group.empty:
        return {
            "unique_start_dates": 0,
            "unique_tickers": 0,
        }

    return {
        "unique_start_dates": int(group["start_timestamp"].nunique()),
        "unique_tickers": int(group["ticker"].nunique()),
    }


def load_market_data_frame(session, tickers, min_timestamp, max_timestamp):
    from app.db.models.market_data import MarketData

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
    window_positions_values = sorted(set(TIMEFRAME_PRICE_WINDOW_MAP.values()))

    for ticker, group in market_df.groupby("ticker", sort=False):
        group = group.sort_values("datetime")
        ohlc4 = group["ohlc4"].to_numpy(dtype=float)
        window_medians = {}

        for window_positions in window_positions_values:
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
            "ohlc4": group["ohlc4"].to_numpy(dtype=float),
            "window_medians": window_medians,
        }

    return lookup


def lookup_window_median_ohlc4_many(
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


def build_horizon_return_frame(group, market_lookup, horizon_days, window_positions):
    horizon_df = group[
        ["ticker", "start_timestamp", EQUAL_WEIGHT_SCORE_COLUMN, "current_price"]
    ].copy()
    horizon_df["future_timestamp"] = (
        horizon_df["start_timestamp"] + pd.to_timedelta(horizon_days, unit="D")
    )
    horizon_df["future_price"] = lookup_window_median_ohlc4_many(
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


def calculate_horizon_summaries(df):
    if EQUAL_WEIGHT_SCORE_COLUMN not in df.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    from app.db.database import SessionLocal

    horizon_rows = []
    quantile_rows = []
    absolute_threshold_rows = []
    max_horizon_days = max(
        max(horizon_days_values)
        for horizon_days_values in HORIZON_DAY_RANGE_MAP.values()
    )
    min_timestamp = to_python_datetime(df["start_timestamp"].min()) - timedelta(
        days=MARKET_DATA_BUFFER_DAYS,
    )
    max_timestamp = to_python_datetime(df["start_timestamp"].max()) + timedelta(
        days=max_horizon_days + MARKET_DATA_BUFFER_DAYS,
    )

    with SessionLocal() as session:
        market_df = load_market_data_frame(
            session,
            tickers=set(df["ticker"].dropna().unique()),
            min_timestamp=min_timestamp,
            max_timestamp=max_timestamp,
        )

    if market_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    market_lookup = build_market_lookup(market_df)
    priced_df = add_current_prices(df, market_lookup)

    for timeframe, group in priced_df.groupby("timeframe"):
        horizon_days_values = HORIZON_DAY_RANGE_MAP.get(timeframe)

        if not horizon_days_values:
            continue

        window_positions = TIMEFRAME_PRICE_WINDOW_MAP.get(timeframe, 0)

        for horizon_days in horizon_days_values:
            horizon_df = build_horizon_return_frame(
                group,
                market_lookup=market_lookup,
                horizon_days=horizon_days,
                window_positions=window_positions,
            )
            stats = calculate_correlations(
                horizon_df,
                EQUAL_WEIGHT_SCORE_COLUMN,
                return_column="future_return",
            )
            horizon_rows.append({
                "timeframe": timeframe,
                "horizon_days": horizon_days,
                "window_positions": window_positions,
                **stats,
                **calculate_return_stats(horizon_df),
                **calculate_sample_stats(horizon_df),
            })

            for top_share in TOP_SCORE_SHARES:
                if (
                    EQUAL_WEIGHT_SCORE_COLUMN not in horizon_df.columns
                    or horizon_df.empty
                ):
                    selected = pd.DataFrame()
                    min_score = None
                else:
                    min_score = horizon_df[EQUAL_WEIGHT_SCORE_COLUMN].quantile(
                        1 - top_share
                    )
                    selected = horizon_df[
                        horizon_df[EQUAL_WEIGHT_SCORE_COLUMN] >= min_score
                    ]

                selected_stats = calculate_correlations(
                    selected,
                    EQUAL_WEIGHT_SCORE_COLUMN,
                    return_column="future_return",
                )
                quantile_rows.append({
                    "timeframe": timeframe,
                    "horizon_days": horizon_days,
                    "window_positions": window_positions,
                    "top_share": top_share,
                    "top_percent": int(top_share * 100),
                    "min_score": None if min_score is None else round(float(min_score), 6),
                    **selected_stats,
                    **calculate_return_stats(selected),
                })

            for score_threshold in ABSOLUTE_SCORE_THRESHOLDS:
                selected = horizon_df[
                    horizon_df[EQUAL_WEIGHT_SCORE_COLUMN] >= score_threshold
                ]
                selected_stats = calculate_correlations(
                    selected,
                    EQUAL_WEIGHT_SCORE_COLUMN,
                    return_column="future_return",
                )
                absolute_threshold_rows.append({
                    "timeframe": timeframe,
                    "horizon_days": horizon_days,
                    "window_positions": window_positions,
                    "score_threshold": score_threshold,
                    **selected_stats,
                    **calculate_return_stats(selected),
                    **calculate_sample_stats(selected),
                })

    return (
        pd.DataFrame(horizon_rows),
        pd.DataFrame(quantile_rows),
        pd.DataFrame(absolute_threshold_rows),
    )


def save_horizon_summaries(df):
    horizon_summary, quantile_summary, absolute_threshold_summary = (
        calculate_horizon_summaries(df)
    )
    quantile_summary = add_benchmark_columns(horizon_summary, quantile_summary)
    absolute_threshold_summary = add_benchmark_columns(
        horizon_summary,
        absolute_threshold_summary,
    )

    if not horizon_summary.empty:
        horizon_summary.to_csv(
            OUTPUT_DIR / "horizon_pearson_summary.csv",
            index=False,
        )

    if not quantile_summary.empty:
        quantile_summary.to_csv(
            OUTPUT_DIR / "horizon_quantile_pearson_summary.csv",
            index=False,
        )

    if not absolute_threshold_summary.empty:
        absolute_threshold_summary.to_csv(
            OUTPUT_DIR / "horizon_absolute_score_performance_summary.csv",
            index=False,
        )

    return horizon_summary, quantile_summary, absolute_threshold_summary


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = load_json(INPUT_FILE)
    df = build_dataframe(data)

    if df.empty:
        print("[EMPTY] No observations found.")
        return

    score_columns = get_score_columns(df)

    if not score_columns:
        print("[EMPTY] No score columns found.")
        return

    metric_columns = get_score_columns(df, include_equal_weight=False)
    summary = save_summary(df, score_columns)
    score_distribution, score_threshold_mapping = build_score_distribution_summaries(
        df,
        EQUAL_WEIGHT_SCORE_COLUMN,
        TOP_SCORE_SHARES,
    )
    score_distribution.to_csv(OUTPUT_DIR / "score_distribution_summary.csv", index=False)
    score_threshold_mapping.to_csv(
        OUTPUT_DIR / "score_quantile_threshold_mapping.csv",
        index=False,
    )
    horizon_summary, quantile_summary, absolute_threshold_summary = (
        save_horizon_summaries(df)
    )
    quantile_stability = build_policy_stability_summary(
        quantile_summary,
        "top_percent",
        "top_percent",
    )
    absolute_stability = build_policy_stability_summary(
        absolute_threshold_summary,
        "score_threshold",
        "minimum_score",
    )
    pd.concat([quantile_stability, absolute_stability], ignore_index=True).to_csv(
        OUTPUT_DIR / "selection_policy_stability_summary.csv",
        index=False,
    )
    benchmark_debug = build_benchmark_debug_dict(
        horizon_summary,
        DEBUG_BENCHMARK_HORIZON_DAYS,
    )

    plot_scatter_by_timeframe(df, summary, OUTPUT_DIR, EQUAL_WEIGHT_SCORE_COLUMN)
    plot_return_distribution(df, OUTPUT_DIR)
    plot_score_buckets(df, score_columns, OUTPUT_DIR)
    plot_metric_summary(summary, OUTPUT_DIR)
    plot_average_metric_values(df, OUTPUT_DIR, metric_columns)
    plot_ticker_score_timeline(df, OUTPUT_DIR, EQUAL_WEIGHT_SCORE_COLUMN)
    plot_timeframe_ticker_score_timeline(df, OUTPUT_DIR, EQUAL_WEIGHT_SCORE_COLUMN)
    plot_horizon_pearson(horizon_summary, OUTPUT_DIR)
    plot_horizon_quantile_pearson(quantile_summary, OUTPUT_DIR)
    plot_score_distributions(
        df,
        EQUAL_WEIGHT_SCORE_COLUMN,
        score_threshold_mapping,
        OUTPUT_DIR,
    )
    plot_top_bucket_performance(quantile_summary, OUTPUT_DIR)
    plot_absolute_threshold_performance(absolute_threshold_summary, OUTPUT_DIR)

    print(f"[DEBUG] Benchmark for {DEBUG_BENCHMARK_HORIZON_DAYS} days:")
    print(json.dumps(benchmark_debug, indent=2))
    print("[OK] Saved plots and summary:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
