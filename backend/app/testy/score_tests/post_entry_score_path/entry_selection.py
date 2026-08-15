import pandas as pd

from app.testy.score_tests.common.annualization import annualize_return
from app.testy.score_tests.common.data import filter_horizon_week_ranges

from .config import (
    ENTRY_MIN_SCORE_PERCENTILE,
    ENTRY_PERCENTILE_BUCKET_COUNT,
    ENTRY_PERCENTILE_BUCKET_SIZE,
    USE_ENTRY_PERCENTILE_BUCKETS,
)


def _entry_percentile_variant_slug(entry_min_score_percentile):
    if entry_min_score_percentile <= 0:
        return "all_scores"
    start_percent = int(round(entry_min_score_percentile * 100))
    return f"entry_min_score_percentile_{start_percent:02d}"


def _entry_percentile_variant_label(entry_min_score_percentile):
    if entry_min_score_percentile <= 0:
        return "Wszystkie percentyle score"
    start_percent = int(round(entry_min_score_percentile * 100))
    return f"Percentyl score przy wejściu >= {start_percent}%"


def _add_entry_percentile_buckets(
    ranked,
    entry_min_score_percentile=ENTRY_MIN_SCORE_PERCENTILE,
    use_entry_percentile_buckets=USE_ENTRY_PERCENTILE_BUCKETS,
):
    result = ranked.copy()
    entry_min_score_percentile = max(
        0.0,
        min(1.0, float(entry_min_score_percentile)),
    )
    if not use_entry_percentile_buckets:
        if entry_min_score_percentile > 0:
            result = result[
                result["score_percentile"] >= entry_min_score_percentile
            ].copy()
        if result.empty:
            return result

        result["entry_percentile_bucket_id"] = 1
        result["entry_min_score_percentile"] = entry_min_score_percentile
        result["entry_percentile_bucket_rank_start"] = 1
        result["entry_percentile_bucket_rank_end"] = result[
            "entry_available_count"
        ]
        result["entry_percentile_bucket_slug"] = (
            _entry_percentile_variant_slug(entry_min_score_percentile)
        )
        result["entry_percentile_bucket_label"] = (
            _entry_percentile_variant_label(entry_min_score_percentile)
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
    entry_min_score_percentile=ENTRY_MIN_SCORE_PERCENTILE,
    use_entry_percentile_buckets=USE_ENTRY_PERCENTILE_BUCKETS,
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
    ranked = _add_entry_percentile_buckets(
        ranked,
        entry_min_score_percentile=entry_min_score_percentile,
        use_entry_percentile_buckets=use_entry_percentile_buckets,
    )
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
