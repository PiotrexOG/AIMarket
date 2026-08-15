import numpy as np
import pandas as pd

from app.testy.market_return_lookup import lookup_asof_close_many
from app.testy.score_tests.common.annualization import annualize_return

from .config import PROGRESS_WEEK_STEP


def _build_history_lookup(history):
    return {
        key: group.reset_index(drop=True)
        for key, group in history.groupby(
            ["timeframe", "ticker"],
            sort=False,
        )
    }


def _build_path_for_entry(entry, history_lookup):
    start_timestamp = pd.Timestamp(entry["start_timestamp"])
    end_timestamp = pd.Timestamp(entry["future_timestamp"])
    ticker_history = history_lookup.get(
        (entry["timeframe"], entry["ticker"])
    )
    if ticker_history is None:
        return pd.DataFrame()
    path = ticker_history[
        (ticker_history["start_timestamp"] >= start_timestamp)
        & (ticker_history["start_timestamp"] <= end_timestamp)
    ].copy()
    if path.empty:
        return path

    path = path.sort_values("start_timestamp").reset_index(drop=True)
    next_timestamps = path["start_timestamp"].shift(-1)
    path["next_score_timestamp"] = next_timestamps.fillna(end_timestamp)
    path["next_score_timestamp"] = pd.to_datetime(
        np.minimum(
            path["next_score_timestamp"].to_numpy(dtype="datetime64[ns]"),
            np.datetime64(end_timestamp),
        )
    )
    path["elapsed_days"] = (
        pd.to_datetime(path["start_timestamp"]) - start_timestamp
    ).dt.days.clip(lower=0)
    path["segment_days"] = (
        path["next_score_timestamp"] - pd.to_datetime(path["start_timestamp"])
    ).dt.days.clip(lower=0)
    path["segment_horizon_share"] = (
        path["segment_days"] / float(entry["horizon_days"])
    )
    return path


def _build_remaining_benchmark_lookup(benchmark_entries, market_lookup):
    key_columns = [
        "timeframe",
        "horizon_weeks",
        "start_timestamp",
        "cutoff_weeks",
    ]
    output_columns = [
        *key_columns,
        "remaining_benchmark_return",
        "remaining_annualized_benchmark_return",
        "benchmark_remaining_observation_count",
    ]
    if benchmark_entries.empty or not market_lookup:
        return {}

    base_entries = benchmark_entries[
        [
            "timeframe",
            "horizon_weeks",
            "horizon_days",
            "start_timestamp",
            "future_timestamp",
            "ticker",
            "future_price",
        ]
    ].copy()
    base_entries["start_timestamp"] = pd.to_datetime(
        base_entries["start_timestamp"]
    )

    frames = []
    max_horizon_weeks = int(base_entries["horizon_weeks"].max())
    for cutoff_weeks in range(PROGRESS_WEEK_STEP, max_horizon_weeks, PROGRESS_WEEK_STEP):
        entries = base_entries.copy()
        entries = entries[entries["horizon_weeks"] > cutoff_weeks].copy()
        entries["cutoff_weeks"] = int(cutoff_weeks)
        if entries.empty:
            continue

        entries["cutoff_timestamp"] = (
            entries["start_timestamp"]
            + pd.to_timedelta(cutoff_weeks * 7, unit="D")
        )
        entries["price_at_cutoff"] = lookup_asof_close_many(
            market_lookup,
            entries["ticker"],
            entries["cutoff_timestamp"],
        )
        entries["remaining_days"] = (
            pd.to_datetime(entries["future_timestamp"])
            - pd.to_datetime(entries["cutoff_timestamp"])
        ).dt.total_seconds() / 86400.0
        matched = entries[
            (entries["remaining_days"] > 0)
            & (entries["price_at_cutoff"] > 0)
            & (entries["future_price"] > 0)
        ].copy()
        if matched.empty:
            continue

        matched["progress_percent"] = (
            matched["cutoff_weeks"] / matched["horizon_weeks"] * 100.0
        )
        matched["progress_share"] = matched["cutoff_weeks"] / matched[
            "horizon_weeks"
        ]
        matched["cutoff_days"] = (
            pd.to_datetime(matched["cutoff_timestamp"])
            - pd.to_datetime(matched["start_timestamp"])
        ).dt.total_seconds() / 86400.0

        matched = matched[
            matched["cutoff_timestamp"].notna()
            & (matched["cutoff_timestamp"] >= matched["start_timestamp"])
        ].copy()
        if matched.empty:
            continue

        matched["benchmark_constituent_remaining_return"] = (
            matched["future_price"] / matched["price_at_cutoff"] - 1.0
        )
        matched = matched[
            np.isfinite(matched["benchmark_constituent_remaining_return"])
            & (matched["benchmark_constituent_remaining_return"] > -1)
        ]
        if matched.empty:
            continue

        frames.append(matched)

    if not frames:
        return {}

    constituents = pd.concat(frames, ignore_index=True)
    grouped = (
        constituents.groupby(key_columns, sort=False)
        .agg(
            remaining_benchmark_return=(
                "benchmark_constituent_remaining_return",
                "mean",
            ),
            remaining_days=("remaining_days", "mean"),
            benchmark_remaining_observation_count=(
                "benchmark_constituent_remaining_return",
                "count",
            ),
        )
        .reset_index()
    )
    grouped["remaining_annualized_benchmark_return"] = [
        annualize_return(total_return, remaining_days)
        for total_return, remaining_days in zip(
            grouped["remaining_benchmark_return"],
            grouped["remaining_days"],
        )
    ]

    return (
        grouped[output_columns]
        .set_index(key_columns)
        .to_dict(orient="index")
    )


def _build_full_horizon_benchmark_lookup(benchmark_entries):
    key_columns = [
        "timeframe",
        "horizon_weeks",
        "start_timestamp",
    ]
    if benchmark_entries.empty:
        return {}

    grouped = (
        benchmark_entries.groupby(key_columns, sort=False)
        .agg(
            benchmark_return=("future_return", "mean"),
            horizon_days=("horizon_days", "mean"),
            benchmark_observation_count=("future_return", "count"),
        )
        .reset_index()
    )
    grouped["annualized_benchmark_return"] = [
        annualize_return(total_return, horizon_days)
        for total_return, horizon_days in zip(
            grouped["benchmark_return"],
            grouped["horizon_days"],
        )
    ]

    return (
        grouped[
            [
                *key_columns,
                "benchmark_return",
                "annualized_benchmark_return",
                "benchmark_observation_count",
            ]
        ]
        .set_index(key_columns)
        .to_dict(orient="index")
    )


def _add_full_horizon_benchmark_metrics(entries, benchmark_lookup):
    if entries.empty:
        return entries

    result = entries.copy()
    benchmark_returns = []
    annualized_benchmark_returns = []
    benchmark_observation_counts = []

    for _, entry in result.iterrows():
        benchmark = benchmark_lookup.get(
            (
                entry["timeframe"],
                int(entry["horizon_weeks"]),
                entry["start_timestamp"],
            ),
            {},
        )
        benchmark_returns.append(benchmark.get("benchmark_return"))
        annualized_benchmark_returns.append(
            benchmark.get("annualized_benchmark_return")
        )
        benchmark_observation_counts.append(
            benchmark.get("benchmark_observation_count")
        )

    result["benchmark_return"] = benchmark_returns
    result["annualized_benchmark_return"] = annualized_benchmark_returns
    result["benchmark_observation_count"] = benchmark_observation_counts
    result["annualized_alpha"] = (
        result["annualized_return"] - result["annualized_benchmark_return"]
    )
    return result
