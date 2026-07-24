import numpy as np
import pandas as pd

from app.testy.market_return_lookup import (
    load_market_lookup_for_analysis,
    lookup_asof_close_many,
)
from app.testy.score_tests.common.data import filter_horizon_week_ranges
from app.testy.score_tests.common.annualization import (
    annualize_return,
)
from app.testy.score_tests.common.metrics import round_or_none


ENTRY_MIN_SCORE_PERCENTILE = 0.70
USE_ENTRY_PERCENTILE_BUCKETS = False
ENTRY_PERCENTILE_BUCKET_SIZE = 2
ENTRY_PERCENTILE_BUCKET_COUNT = 9
PROGRESS_WEEK_STEP = 1
PROGRESS_BUCKET_PERCENTAGE_POINTS = 5
MIN_PROGRESS_BUCKET_PERCENT = 20
MAX_PROGRESS_BUCKET_PERCENT = 80
SWITCH_SCORE_CHANGE_THRESHOLDS = tuple(
    round(value, 2) for value in np.arange(-0.80, 0.4, 0.05)
)

CORRELATION_METRICS = [
    "mean_score_percentile",
]

LIVE_CORRELATION_METRICS = [
    "mean_score_percentile",
    "relative_score_percentile_change",
]


ENTRY_BUCKET_COLUMNS = [
    "entry_percentile_bucket_id",
    "entry_percentile_bucket_slug",
    "entry_percentile_bucket_label",
    "entry_percentile_bucket_rank_start",
    "entry_percentile_bucket_rank_end",
]


def _add_entry_percentile_buckets(ranked):
    result = ranked.copy()
    if not USE_ENTRY_PERCENTILE_BUCKETS:
        result = result[
            result["score_percentile"] >= ENTRY_MIN_SCORE_PERCENTILE
        ].copy()
        if result.empty:
            return result

        start_percent = int(round(ENTRY_MIN_SCORE_PERCENTILE * 100))
        result["entry_percentile_bucket_id"] = 1
        result["entry_percentile_bucket_rank_start"] = 1
        result["entry_percentile_bucket_rank_end"] = result[
            "entry_available_count"
        ]
        result["entry_percentile_bucket_slug"] = (
            f"entry_min_score_percentile_{start_percent:02d}"
        )
        result["entry_percentile_bucket_label"] = (
            f"Entry score percentile >= {start_percent}%"
        )
        return result

    result["entry_percentile_bucket_id"] = (
        (result["entry_rank_position"] - 1) // ENTRY_PERCENTILE_BUCKET_SIZE
    ) + 1
    result = result[
        result["entry_percentile_bucket_id"] <= ENTRY_PERCENTILE_BUCKET_COUNT
    ].copy()
    if result.empty:
        return result

    result["entry_percentile_bucket_rank_start"] = (
        (result["entry_percentile_bucket_id"] - 1)
        * ENTRY_PERCENTILE_BUCKET_SIZE
        + 1
    )
    result["entry_percentile_bucket_rank_end"] = (
        result["entry_percentile_bucket_rank_start"]
        + ENTRY_PERCENTILE_BUCKET_SIZE
        - 1
    )
    result["entry_percentile_bucket_slug"] = [
        f"entry_rank_{int(start):02d}_{int(end):02d}"
        for start, end in zip(
            result["entry_percentile_bucket_rank_start"],
            result["entry_percentile_bucket_rank_end"],
        )
    ]
    result["entry_percentile_bucket_label"] = [
        f"Entry rank {int(start)}-{int(end)}"
        for start, end in zip(
            result["entry_percentile_bucket_rank_start"],
            result["entry_percentile_bucket_rank_end"],
        )
    ]
    return result


def _first_existing_columns(df, columns):
    return [column for column in columns if column in df.columns]


def _first_value_or_none(group, column):
    return group[column].iloc[0] if column in group.columns else None

def _weighted_mean(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return None
    return float(np.average(values[valid], weights=weights[valid]))


def _overlap_days(segment_starts, segment_days, window_start, window_end):
    segment_ends = segment_starts + segment_days
    return np.maximum(
        0.0,
        np.minimum(segment_ends, window_end) - np.maximum(segment_starts, window_start),
    )


def _progress_weeks_for_horizon(horizon_weeks):
    return tuple(range(PROGRESS_WEEK_STEP, int(horizon_weeks), PROGRESS_WEEK_STEP))


def _progress_bucket(progress_percent):
    if (
        progress_percent < MIN_PROGRESS_BUCKET_PERCENT
        or progress_percent >= MAX_PROGRESS_BUCKET_PERCENT
    ):
        return None

    bucket_start = np.floor(
        progress_percent / PROGRESS_BUCKET_PERCENTAGE_POINTS
    ) * PROGRESS_BUCKET_PERCENTAGE_POINTS
    bucket_start = max(
        float(MIN_PROGRESS_BUCKET_PERCENT),
        min(
            float(MAX_PROGRESS_BUCKET_PERCENT - PROGRESS_BUCKET_PERCENTAGE_POINTS),
            float(bucket_start),
        ),
    )
    bucket_end = bucket_start + PROGRESS_BUCKET_PERCENTAGE_POINTS
    return {
        "progress_bucket_start_percent": bucket_start,
        "progress_bucket_end_percent": bucket_end,
        "progress_bucket_mid_percent": (bucket_start + bucket_end) / 2.0,
        "progress_bucket_label": f"{bucket_start:.0f}-{bucket_end:.0f}%",
    }


def _safe_corr(group, metric, method):
    return _safe_corr_pair(group, metric, "annualized_return", method)


def _safe_corr_pair(group, metric, return_metric, method):
    clean = group[[metric, return_metric]].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    if (
        len(clean) < 3
        or clean[metric].nunique() < 2
        or clean[return_metric].nunique() < 2
    ):
        return None
    return round_or_none(clean[metric].corr(clean[return_metric], method=method))


def _prepare_score_history(return_panel):
    columns = [
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "score_zscore",
        "current_price",
    ]
    required = set(columns)
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame(columns=columns)

    return (
        return_panel[columns]
        .dropna(subset=["timeframe", "ticker", "start_timestamp", "score"])
        .drop_duplicates(["timeframe", "ticker", "start_timestamp"])
        .sort_values(["timeframe", "ticker", "start_timestamp"])
        .reset_index(drop=True)
    )


def _prepare_top_entry_observations(
    return_panel,
    horizon_start,
    horizon_end,
    horizon_week_ranges=None,
):
    if return_panel.empty:
        return pd.DataFrame()

    ranked = (
        filter_horizon_week_ranges(
            return_panel,
            horizon_week_ranges=horizon_week_ranges,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )
        .dropna(subset=["score", "future_return"])
        .sort_values(
            [
                "timeframe",
                "horizon_weeks",
                "horizon_days",
                "start_timestamp",
                "score",
                "ticker",
            ],
            ascending=[True, True, True, True, False, True],
        )
        .copy()
    )
    if ranked.empty:
        return pd.DataFrame()

    ranked["entry_rank_position"] = (
        ranked.groupby(
            ["timeframe", "horizon_weeks", "start_timestamp"]
        ).cumcount()
        + 1
    )
    ranked["entry_available_count"] = ranked.groupby(
        ["timeframe", "horizon_weeks", "start_timestamp"]
    )["ticker"].transform("count")
    ranked = _add_entry_percentile_buckets(ranked)
    if ranked.empty:
        return pd.DataFrame()

    ranked["annualized_return"] = [
        annualize_return(total_return, horizon_days)
        for total_return, horizon_days in zip(
            ranked["future_return"],
            ranked["horizon_days"],
        )
    ]
    ranked = ranked.dropna(subset=["annualized_return"])
    ranked["observation_id"] = (
        ranked.groupby(
            [
                "entry_percentile_bucket_id",
                "timeframe",
                "horizon_weeks",
            ]
        ).cumcount()
        + 1
    )
    return ranked.reset_index(drop=True)


def _prepare_benchmark_observations(
    return_panel,
    horizon_start,
    horizon_end,
    horizon_week_ranges=None,
):
    required = {
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "start_timestamp",
        "future_timestamp",
        "ticker",
        "score",
        "future_return",
        "current_price",
        "future_price",
    }
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame()

    benchmark = (
        filter_horizon_week_ranges(
            return_panel,
            horizon_week_ranges=horizon_week_ranges,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )
        .dropna(
            subset=[
                "score",
                "future_return",
                "current_price",
                "future_price",
            ]
        )
        .sort_values(
            [
                "timeframe",
                "horizon_weeks",
                "horizon_days",
                "start_timestamp",
                "score",
                "ticker",
            ],
            ascending=[True, True, True, True, False, True],
        )
        .copy()
    )
    if benchmark.empty:
        return pd.DataFrame()

    benchmark = benchmark[
        (benchmark["current_price"] > 0)
        & (benchmark["future_price"] > 0)
        & (benchmark["future_return"] > -1)
    ].copy()
    return benchmark.reset_index(drop=True)


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


def _summarize_entry_path(entry, path):
    horizon_days = int(entry["horizon_days"])
    horizon_weeks = int(entry["horizon_weeks"])
    segment_days = path["segment_days"].to_numpy(dtype=float)
    covered_days = float(np.nansum(segment_days))

    mean_score_percentile = _weighted_mean(
        path["score_percentile"],
        segment_days,
    )
    score_percentile_drop = (
        float(entry["score_percentile"]) - mean_score_percentile
        if mean_score_percentile is not None
        else None
    )
    relative_score_percentile_drop = (
        score_percentile_drop / float(entry["score_percentile"])
        if score_percentile_drop is not None
        and float(entry["score_percentile"]) > 0
        else None
    )
    score_percentile_change = (
        -score_percentile_drop
        if score_percentile_drop is not None
        else None
    )
    relative_score_percentile_change = (
        -relative_score_percentile_drop
        if relative_score_percentile_drop is not None
        else None
    )

    row = {
        "timeframe": entry["timeframe"],
        **{
            column: entry.get(column)
            for column in ENTRY_BUCKET_COLUMNS
            if column in entry
        },
        "horizon_weeks": horizon_weeks,
        "horizon_days": horizon_days,
        "observation_id": int(entry["observation_id"]),
        "start_timestamp": entry["start_timestamp"],
        "future_timestamp": entry["future_timestamp"],
        "ticker": entry["ticker"],
        "entry_score": float(entry["score"]),
        "entry_score_percentile": float(entry["score_percentile"]),
        "entry_score_zscore": float(entry["score_zscore"]),
        "entry_rank_position": int(entry["entry_rank_position"]),
        "entry_available_count": int(entry["entry_available_count"]),
        "current_price": float(entry["current_price"]),
        "future_price": float(entry["future_price"]),
        "future_return": float(entry["future_return"]),
        "annualized_return": float(entry["annualized_return"]),
        "benchmark_return": entry.get("benchmark_return"),
        "annualized_benchmark_return": entry.get(
            "annualized_benchmark_return"
        ),
        "annualized_alpha": entry.get("annualized_alpha"),
        "benchmark_observation_count": entry.get(
            "benchmark_observation_count"
        ),
        "path_point_count": int(len(path)),
        "path_covered_days": covered_days,
        "path_covered_horizon_share": covered_days / horizon_days,
        "mean_score_percentile": mean_score_percentile,
        "score_percentile_drop": score_percentile_drop,
        "relative_score_percentile_drop": relative_score_percentile_drop,
        "score_percentile_change": score_percentile_change,
        "relative_score_percentile_change": relative_score_percentile_change,
    }

    return row


def _summarize_live_progress(entry, path, market_lookup, remaining_benchmark_lookup):
    rows = []
    horizon_days = int(entry["horizon_days"])
    horizon_weeks = int(entry["horizon_weeks"])
    current_price = float(entry["current_price"])
    future_price = float(entry["future_price"])
    future_return = float(entry["future_return"])
    elapsed_days = path["elapsed_days"].to_numpy(dtype=float)
    segment_days = path["segment_days"].to_numpy(dtype=float)
    score_percentiles = path["score_percentile"].to_numpy(dtype=float)

    for cutoff_weeks in _progress_weeks_for_horizon(horizon_weeks):
        cutoff_timestamp = pd.Timestamp(entry["start_timestamp"]) + pd.to_timedelta(
            cutoff_weeks * 7,
            unit="D",
        )
        cutoff_days = (
            cutoff_timestamp - pd.Timestamp(entry["start_timestamp"])
        ).total_seconds() / 86400.0
        progress_share = cutoff_weeks / horizon_weeks
        progress_percent = progress_share * 100.0
        progress_bucket = _progress_bucket(progress_percent)
        if progress_bucket is None:
            continue

        live_segment_days = _overlap_days(
            elapsed_days,
            segment_days,
            0.0,
            cutoff_days,
        )
        entry_score_percentile = float(entry["score_percentile"])
        mean_score_percentile = _weighted_mean(
            score_percentiles,
            live_segment_days,
        )
        score_percentile_change = (
            mean_score_percentile - entry_score_percentile
            if mean_score_percentile is not None
            else None
        )
        relative_score_percentile_change = (
            score_percentile_change / entry_score_percentile
            if score_percentile_change is not None
            and entry_score_percentile > 0
            else None
        )
        cutoff_price = lookup_asof_close_many(
            market_lookup,
            [entry["ticker"]],
            [cutoff_timestamp],
        )
        price_at_cutoff = (
            float(cutoff_price[0])
            if len(cutoff_price) and np.isfinite(cutoff_price[0]) and cutoff_price[0] > 0
            else None
        )

        price_change_to_cutoff = (
            price_at_cutoff / current_price - 1.0
            if price_at_cutoff is not None and current_price > 0
            else None
        )
        remaining_days = (
            pd.Timestamp(entry["future_timestamp"]) - cutoff_timestamp
        ).total_seconds() / 86400.0
        remaining_return = (
            future_price / price_at_cutoff - 1.0
            if price_at_cutoff is not None
            else None
        )
        remaining_annualized_return = (
            annualize_return(remaining_return, remaining_days)
            if remaining_return is not None and remaining_days > 0
            else None
        )
        benchmark_key = (
            entry["timeframe"],
            horizon_weeks,
            entry["start_timestamp"],
            int(cutoff_weeks),
        )
        remaining_benchmark = remaining_benchmark_lookup.get(
            benchmark_key,
            {},
        )
        remaining_benchmark_return = remaining_benchmark.get(
            "remaining_benchmark_return"
        )
        remaining_annualized_benchmark_return = remaining_benchmark.get(
            "remaining_annualized_benchmark_return"
        )
        switch_to_benchmark_return_gain = (
            remaining_benchmark_return - remaining_return
            if remaining_benchmark_return is not None
            and remaining_return is not None
            else None
        )
        switch_to_benchmark_annualized_gain = (
            remaining_annualized_benchmark_return - remaining_annualized_return
            if remaining_annualized_benchmark_return is not None
            and remaining_annualized_return is not None
            else None
        )
        remaining_annualized_alpha = (
            remaining_annualized_return - remaining_annualized_benchmark_return
            if remaining_annualized_return is not None
            and remaining_annualized_benchmark_return is not None
            else None
        )
        rows.append({
            "timeframe": entry["timeframe"],
            **{
                column: entry.get(column)
                for column in ENTRY_BUCKET_COLUMNS
                if column in entry
            },
            "horizon_weeks": horizon_weeks,
            "horizon_days": horizon_days,
            "observation_id": int(entry["observation_id"]),
            "start_timestamp": entry["start_timestamp"],
            "future_timestamp": entry["future_timestamp"],
            "ticker": entry["ticker"],
            "current_price": current_price,
            "future_price": future_price,
            "future_return": future_return,
            "cutoff_weeks": int(cutoff_weeks),
            "progress_percent": progress_percent,
            "progress_share": progress_share,
            **progress_bucket,
            "cutoff_days": cutoff_days,
            "cutoff_timestamp": cutoff_timestamp,
            "entry_score_percentile": entry_score_percentile,
            "mean_score_percentile": mean_score_percentile,
            "score_percentile_change": score_percentile_change,
            "relative_score_percentile_change": (
                relative_score_percentile_change
            ),
            "price_at_cutoff": price_at_cutoff,
            "price_change_to_cutoff": price_change_to_cutoff,
            "remaining_days": remaining_days,
            "remaining_return": remaining_return,
            "remaining_annualized_return": remaining_annualized_return,
            "remaining_benchmark_return": remaining_benchmark_return,
            "remaining_annualized_benchmark_return": (
                remaining_annualized_benchmark_return
            ),
            "remaining_annualized_alpha": remaining_annualized_alpha,
            "switch_to_benchmark_return_gain": (
                switch_to_benchmark_return_gain
            ),
            "switch_to_benchmark_annualized_gain": (
                switch_to_benchmark_annualized_gain
            ),
            "switch_to_benchmark_would_win": (
                switch_to_benchmark_annualized_gain > 0
                if switch_to_benchmark_annualized_gain is not None
                else None
            ),
            "benchmark_remaining_observation_count": remaining_benchmark.get(
                "benchmark_remaining_observation_count"
            ),
            "annualized_return": float(entry["annualized_return"]),
            "benchmark_return": entry.get("benchmark_return"),
            "annualized_benchmark_return": entry.get(
                "annualized_benchmark_return"
            ),
            "annualized_alpha": entry.get("annualized_alpha"),
            "benchmark_observation_count": entry.get(
                "benchmark_observation_count"
            ),
        })

    return rows


def _build_observations_and_paths(
    entries,
    history_lookup,
    market_lookup,
    remaining_benchmark_lookup,
):
    observation_rows = []
    live_progress_rows = []

    for _, entry in entries.iterrows():
        path = _build_path_for_entry(entry, history_lookup)
        if path.empty:
            continue

        observation_rows.append(_summarize_entry_path(entry, path))
        live_progress_rows.extend(
            _summarize_live_progress(
                entry,
                path,
                market_lookup,
                remaining_benchmark_lookup,
            )
        )

    observations = pd.DataFrame(observation_rows)
    return observations, pd.DataFrame(live_progress_rows)


def _summarize_switch_group(group):
    annualized_gain = group["switch_to_benchmark_annualized_gain"].to_numpy(
        dtype=float
    )
    return_gain = group["switch_to_benchmark_return_gain"].to_numpy(dtype=float)
    downside_gain = np.minimum(0.0, annualized_gain)
    mean_annualized_gain = float(annualized_gain.mean())
    downside_deviation = float(np.sqrt(np.mean(np.square(downside_gain))))

    if downside_deviation == 0:
        downside_information_ratio = (
            0.0
            if mean_annualized_gain == 0
            else np.inf * np.sign(mean_annualized_gain)
        )
    else:
        downside_information_ratio = mean_annualized_gain / downside_deviation

    return {
        "switch_count": int(len(group)),
        "downside_count": int((annualized_gain < 0).sum()),
        "downside_frequency": float((annualized_gain < 0).mean()),
        "benchmark_win_frequency": float((annualized_gain > 0).mean()),
        "mean_switch_to_benchmark_return_gain": float(return_gain.mean()),
        "mean_switch_to_benchmark_annualized_gain": mean_annualized_gain,
        "median_switch_to_benchmark_annualized_gain": float(
            np.median(annualized_gain)
        ),
        "downside_deviation": downside_deviation,
        "downside_information_ratio": downside_information_ratio,
        "mean_remaining_return": float(group["remaining_return"].mean()),
        "mean_remaining_annualized_return": float(
            group["remaining_annualized_return"].mean()
        ),
        "mean_remaining_benchmark_return": float(
            group["remaining_benchmark_return"].mean()
        ),
        "mean_remaining_annualized_benchmark_return": float(
            group["remaining_annualized_benchmark_return"].mean()
        ),
    }


def _mark_best_switch_thresholds(result, group_columns):
    if result.empty:
        return result

    result = result.copy()
    result["is_max_downside_information_ratio"] = False
    result["is_max_mean_switch_gain"] = False

    grouped = result.groupby(list(group_columns), sort=False)
    for _, group in grouped:
        finite_ratio = group[
            np.isfinite(group["downside_information_ratio"].to_numpy(dtype=float))
        ]
        if not finite_ratio.empty:
            max_ratio_index = finite_ratio["downside_information_ratio"].idxmax()
            result.loc[max_ratio_index, "is_max_downside_information_ratio"] = True

        finite_gain = group[
            np.isfinite(
                group["mean_switch_to_benchmark_annualized_gain"].to_numpy(
                    dtype=float
                )
            )
        ]
        if not finite_gain.empty:
            max_gain_index = finite_gain[
                "mean_switch_to_benchmark_annualized_gain"
            ].idxmax()
            result.loc[max_gain_index, "is_max_mean_switch_gain"] = True

    return result


def _build_switch_to_benchmark_threshold_analysis(
    live_progress_observations,
    thresholds=SWITCH_SCORE_CHANGE_THRESHOLDS,
    group_columns=("timeframe", "progress_percent"),
):
    metadata_columns = [
        "entry_percentile_bucket_slug",
        "entry_percentile_bucket_label",
        "entry_percentile_bucket_rank_start",
        "entry_percentile_bucket_rank_end",
        "progress_bucket_end_percent",
        "progress_bucket_mid_percent",
        "progress_bucket_label",
        "progress_percent",
        "progress_share",
        "mean_cutoff_weeks",
    ]
    columns = [
        *group_columns,
        *[
            column
            for column in metadata_columns
            if column not in group_columns
        ],
        "score_change_threshold",
        "score_change_threshold_percent",
        "observation_count",
        "switch_count",
        "switch_share",
        "downside_count",
        "downside_frequency",
        "benchmark_win_frequency",
        "mean_switch_to_benchmark_return_gain",
        "mean_switch_to_benchmark_annualized_gain",
        "median_switch_to_benchmark_annualized_gain",
        "downside_deviation",
        "downside_information_ratio",
        "mean_remaining_return",
        "mean_remaining_annualized_return",
        "mean_remaining_benchmark_return",
        "mean_remaining_annualized_benchmark_return",
        "is_max_downside_information_ratio",
        "is_max_mean_switch_gain",
    ]
    required = [
        "relative_score_percentile_change",
        "switch_to_benchmark_return_gain",
        "switch_to_benchmark_annualized_gain",
        "remaining_return",
        "remaining_annualized_return",
        "remaining_benchmark_return",
        "remaining_annualized_benchmark_return",
    ]
    if (
        live_progress_observations.empty
        or not set(required).issubset(live_progress_observations.columns)
    ):
        return pd.DataFrame(columns=columns)

    data = (
        live_progress_observations.replace([np.inf, -np.inf], np.nan)
        .dropna(subset=required)
        .copy()
    )
    if data.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for group_key, group in data.groupby(list(group_columns), sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        observation_count = int(len(group))
        metadata = {}
        if "progress_bucket_end_percent" in group.columns:
            metadata["progress_bucket_end_percent"] = float(
                group["progress_bucket_end_percent"].iloc[0]
            )
        if "progress_bucket_mid_percent" in group.columns:
            metadata["progress_bucket_mid_percent"] = float(
                group["progress_bucket_mid_percent"].iloc[0]
            )
        if "progress_bucket_label" in group.columns:
            metadata["progress_bucket_label"] = group[
                "progress_bucket_label"
            ].iloc[0]
        if "progress_percent" in group.columns:
            metadata["progress_percent"] = round_or_none(
                group["progress_percent"].mean()
            )
        if "progress_share" in group.columns:
            metadata["progress_share"] = round_or_none(
                group["progress_share"].mean()
            )
        if "cutoff_weeks" in group.columns:
            metadata["mean_cutoff_weeks"] = round_or_none(
                group["cutoff_weeks"].mean()
            )
        for column in ENTRY_BUCKET_COLUMNS:
            if column not in group_columns and column in group.columns:
                metadata[column] = group[column].iloc[0]

        for threshold in thresholds:
            selected = group[
                group["relative_score_percentile_change"] <= threshold
            ]
            if selected.empty:
                continue

            summary = _summarize_switch_group(selected)
            rows.append({
                **group_values,
                **metadata,
                "score_change_threshold": float(threshold),
                "score_change_threshold_percent": round_or_none(
                    float(threshold) * 100
                ),
                "observation_count": observation_count,
                "switch_share": len(selected) / observation_count,
                **summary,
            })

    if not rows:
        return pd.DataFrame(columns=columns)

    result = pd.DataFrame(rows)
    result = _mark_best_switch_thresholds(result, group_columns)
    return (
        result[columns]
        .sort_values([*group_columns, "score_change_threshold"])
        .reset_index(drop=True)
    )


def _build_correlations_by_horizon(
    observations,
    return_metric="annualized_return",
):
    rows = []
    if observations.empty:
        return pd.DataFrame()
    if return_metric not in observations.columns:
        return pd.DataFrame()

    group_columns = [
        *_first_existing_columns(observations, ENTRY_BUCKET_COLUMNS),
        "timeframe",
        "horizon_weeks",
    ]
    for group_key, group in observations.groupby(
        group_columns,
        sort=False,
    ):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        for metric in CORRELATION_METRICS:
            rows.append({
                **group_values,
                "horizon_weeks": int(group_values["horizon_weeks"]),
                "horizon_days": round_or_none(group["horizon_days"].mean()),
                "metric": metric,
                "observation_count": int(
                    group[[metric, return_metric]].dropna().shape[0]
                ),
                "pearson_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "pearson",
                ),
                "spearman_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "spearman",
                ),
                "mean_metric_value": round_or_none(group[metric].mean()),
                "mean_annualized_return": round_or_none(
                    group[return_metric].mean()
                ),
            })

    return pd.DataFrame(rows)


def _build_horizon_average(correlations_by_horizon):
    columns = [
        *ENTRY_BUCKET_COLUMNS,
        "timeframe",
        "horizon_week_start",
        "horizon_week_end",
        "horizon_count",
        "aggregation_method",
        "metric",
        "mean_observation_count",
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
        "mean_metric_value",
        "mean_annualized_return",
    ]
    if correlations_by_horizon.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    group_columns = [
        *_first_existing_columns(correlations_by_horizon, ENTRY_BUCKET_COLUMNS),
        "timeframe",
        "metric",
    ]
    for group_key, group in correlations_by_horizon.groupby(
        group_columns,
        sort=False,
    ):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        rows.append({
            **group_values,
            "horizon_week_start": int(group["horizon_weeks"].min()),
            "horizon_week_end": int(group["horizon_weeks"].max()),
            "horizon_count": int(group["horizon_weeks"].nunique()),
            "aggregation_method": "equal_weight_mean_across_horizons",
            "mean_observation_count": round_or_none(
                group["observation_count"].mean()
            ),
            "mean_pearson_to_annualized_return": round_or_none(
                group["pearson_to_annualized_return"].mean()
            ),
            "mean_spearman_to_annualized_return": round_or_none(
                group["spearman_to_annualized_return"].mean()
            ),
            "mean_metric_value": round_or_none(group["mean_metric_value"].mean()),
            "mean_annualized_return": round_or_none(
                group["mean_annualized_return"].mean()
            ),
        })

    sort_columns = [
        *_first_existing_columns(pd.DataFrame(rows), ["entry_percentile_bucket_id"]),
        "timeframe",
        "metric",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values(
        sort_columns
    ).reset_index(drop=True)


def _build_live_progress_correlations_by_horizon(
    live_progress_observations,
    return_metric="annualized_return",
):
    rows = []
    if live_progress_observations.empty:
        return pd.DataFrame()
    if return_metric not in live_progress_observations.columns:
        return pd.DataFrame()

    group_columns = [
        *_first_existing_columns(
            live_progress_observations,
            ENTRY_BUCKET_COLUMNS,
        ),
        "timeframe",
        "horizon_weeks",
        "progress_bucket_start_percent",
    ]
    grouped = live_progress_observations.groupby(
        group_columns,
        sort=False,
    )
    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        bucket_row = group.iloc[0]
        for metric in LIVE_CORRELATION_METRICS:
            rows.append({
                **group_values,
                "horizon_weeks": int(group_values["horizon_weeks"]),
                "horizon_days": round_or_none(group["horizon_days"].mean()),
                "cutoff_weeks": round_or_none(group["cutoff_weeks"].mean()),
                "progress_bucket_start_percent": float(
                    group_values["progress_bucket_start_percent"]
                ),
                "progress_bucket_end_percent": float(
                    bucket_row["progress_bucket_end_percent"]
                ),
                "progress_bucket_mid_percent": float(
                    bucket_row["progress_bucket_mid_percent"]
                ),
                "progress_bucket_label": bucket_row["progress_bucket_label"],
                "progress_percent": round_or_none(
                    group["progress_percent"].mean()
                ),
                "progress_share": round_or_none(group["progress_share"].mean()),
                "cutoff_days": round_or_none(group["cutoff_days"].mean()),
                "metric": metric,
                "observation_count": int(
                    group[[metric, return_metric]].dropna().shape[0]
                ),
                "pearson_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "pearson",
                ),
                "spearman_to_annualized_return": _safe_corr_pair(
                    group,
                    metric,
                    return_metric,
                    "spearman",
                ),
            })

    return pd.DataFrame(rows)


def _build_live_progress_average(correlations_by_horizon):
    columns = [
        *ENTRY_BUCKET_COLUMNS,
        "timeframe",
        "progress_bucket_start_percent",
        "progress_bucket_end_percent",
        "progress_bucket_mid_percent",
        "progress_bucket_label",
        "mean_cutoff_weeks",
        "progress_percent",
        "progress_share",
        "metric",
        "horizon_week_start",
        "horizon_week_end",
        "horizon_count",
        "mean_cutoff_days",
        "mean_observation_count",
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
    ]
    if correlations_by_horizon.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    group_columns = [
        *_first_existing_columns(correlations_by_horizon, ENTRY_BUCKET_COLUMNS),
        "timeframe",
        "progress_bucket_start_percent",
        "metric",
    ]
    grouped = correlations_by_horizon.groupby(
        group_columns,
        sort=False,
    )
    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        bucket_row = group.iloc[0]
        rows.append({
            **group_values,
            "progress_bucket_start_percent": float(
                group_values["progress_bucket_start_percent"]
            ),
            "progress_bucket_end_percent": float(
                bucket_row["progress_bucket_end_percent"]
            ),
            "progress_bucket_mid_percent": float(
                bucket_row["progress_bucket_mid_percent"]
            ),
            "progress_bucket_label": bucket_row["progress_bucket_label"],
            "mean_cutoff_weeks": round_or_none(group["cutoff_weeks"].mean()),
            "progress_percent": round_or_none(group["progress_percent"].mean()),
            "progress_share": round_or_none(group["progress_share"].mean()),
            "horizon_week_start": int(group["horizon_weeks"].min()),
            "horizon_week_end": int(group["horizon_weeks"].max()),
            "horizon_count": int(group["horizon_weeks"].nunique()),
            "mean_cutoff_days": round_or_none(group["cutoff_days"].mean()),
            "mean_observation_count": round_or_none(
                group["observation_count"].mean()
            ),
            "mean_pearson_to_annualized_return": round_or_none(
                group["pearson_to_annualized_return"].mean()
            ),
            "mean_spearman_to_annualized_return": round_or_none(
                group["spearman_to_annualized_return"].mean()
            ),
        })

    sort_columns = [
        *_first_existing_columns(pd.DataFrame(rows), ["entry_percentile_bucket_id"]),
        "timeframe",
        "metric",
        "progress_bucket_start_percent",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values(
        sort_columns
    ).reset_index(drop=True)


def _round_numeric_columns(df):
    if df.empty:
        return df
    result = df.copy()
    for column in result.select_dtypes(include=[np.number]).columns:
        if column not in {
            "horizon_days",
            "horizon_weeks",
            "cutoff_weeks",
            "entry_percentile_bucket_id",
            "entry_percentile_bucket_rank_start",
            "entry_percentile_bucket_rank_end",
            "progress_bucket_start_percent",
            "progress_bucket_end_percent",
            "progress_bucket_mid_percent",
            "observation_id",
            "entry_rank_position",
            "entry_available_count",
            "rank_position",
            "available_count",
            "path_point_count",
        }:
            result[column] = result[column].round(6)
    return result


def calculate(
    context,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
):
    history = _prepare_score_history(context.return_panel)
    history_lookup = _build_history_lookup(history)
    entries = _prepare_top_entry_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
    )
    benchmark_entries = _prepare_benchmark_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
    )
    full_horizon_benchmark_lookup = _build_full_horizon_benchmark_lookup(
        benchmark_entries
    )
    entries = _add_full_horizon_benchmark_metrics(
        entries,
        full_horizon_benchmark_lookup,
    )
    market_source = (
        context.score_observations
        if context.score_observations is not None
        else context.return_panel
    )
    max_cutoff_timestamp = (
        pd.to_datetime(benchmark_entries["future_timestamp"].max())
        if not benchmark_entries.empty
        else pd.to_datetime(context.return_panel["future_timestamp"].max())
    )
    market_lookup = load_market_lookup_for_analysis(
        market_source,
        max_timestamp=max_cutoff_timestamp,
    )
    remaining_benchmark_lookup = _build_remaining_benchmark_lookup(
        benchmark_entries,
        market_lookup,
    )
    observations, live_progress_observations = (
        _build_observations_and_paths(
            entries,
            history_lookup,
            market_lookup,
            remaining_benchmark_lookup,
        )
    )
    alpha_correlations_by_horizon = _build_correlations_by_horizon(
        observations,
        return_metric="annualized_alpha",
    )
    alpha_horizon_average = _build_horizon_average(
        alpha_correlations_by_horizon
    )
    live_progress_alpha_correlations_by_horizon = (
        _build_live_progress_correlations_by_horizon(
            live_progress_observations,
            return_metric="annualized_alpha",
        )
    )
    live_progress_alpha_average = _build_live_progress_average(
        live_progress_alpha_correlations_by_horizon
    )
    switch_to_benchmark_thresholds = (
        _build_switch_to_benchmark_threshold_analysis(
            live_progress_observations,
            group_columns=(
                "entry_percentile_bucket_id",
                "timeframe",
                "progress_bucket_start_percent",
            ),
        )
    )

    return {
        "observations": _round_numeric_columns(observations),
        "horizon_alpha_average": _round_numeric_columns(
            alpha_horizon_average
        ),
        "live_progress_observations": _round_numeric_columns(
            live_progress_observations
        ),
        "live_progress_alpha_average": _round_numeric_columns(
            live_progress_alpha_average
        ),
        "switch_to_benchmark_thresholds": _round_numeric_columns(
            switch_to_benchmark_thresholds
        ),
    }
