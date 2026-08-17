import pandas as pd

from app.testy.score_tests.common.data import (
    COMMON_HORIZON_ALIGNMENT_COLUMN,
    COMMON_HORIZON_WEEK_END_COLUMN,
    COMMON_HORIZON_WEEK_START_COLUMN,
    align_start_dates_to_common_horizon_window,
    common_horizon_window_metadata,
)
from app.testy.score_tests.common.metrics import round_or_none

from .observations import (
    BENCHMARK_RETURN_BUCKET_COUNT,
    _summarize_downside_information_ratio_group,
)


def _annualized_benchmark_column(df):
    if "annualized_benchmark_return" in df.columns:
        return "annualized_benchmark_return"
    return "benchmark_annualized"


def _assign_benchmark_return_buckets(observations, bucket_count):
    benchmark_column = _annualized_benchmark_column(observations)
    key_columns = ["timeframe", "horizon_weeks", "start_timestamp"]
    bucket_columns = [
        *key_columns,
        "benchmark_return_bucket_id",
        "benchmark_return_bucket",
        "benchmark_bucket_min",
        "benchmark_bucket_max",
        "benchmark_bucket_mean",
        "benchmark_bucket_observation_count",
    ]
    base = (
        observations[key_columns + [benchmark_column]]
        .dropna(subset=[benchmark_column])
        .drop_duplicates(key_columns)
        .copy()
    )
    if base.empty:
        return pd.DataFrame(columns=bucket_columns)

    bucket_frames = []
    for timeframe, timeframe_data in base.groupby("timeframe", sort=False):
        clean = timeframe_data.sort_values(
            [benchmark_column, "horizon_weeks", "start_timestamp"]
        ).copy()
        unique_values = clean[benchmark_column].nunique(dropna=True)
        effective_bucket_count = max(1, min(int(bucket_count), int(unique_values)))

        if effective_bucket_count == 1:
            clean["benchmark_return_bucket_id"] = 1
        else:
            clean["benchmark_return_bucket_id"] = (
                pd.qcut(
                    clean[benchmark_column],
                    q=effective_bucket_count,
                    labels=False,
                    duplicates="drop",
                )
                + 1
            )

        clean["benchmark_return_bucket_id"] = (
            clean["benchmark_return_bucket_id"].astype(int)
        )
        bucket_stats = clean.groupby("benchmark_return_bucket_id")[
            benchmark_column
        ].agg(["min", "max", "mean", "count"])
        clean["benchmark_return_bucket"] = clean["benchmark_return_bucket_id"].map(
            lambda bucket_id: (
                f"Koszyk B{int(bucket_id):02d}: "
                f"{bucket_stats.loc[bucket_id, 'min']:.2%} do "
                f"{bucket_stats.loc[bucket_id, 'max']:.2%}"
            )
        )
        clean["benchmark_bucket_min"] = clean["benchmark_return_bucket_id"].map(
            bucket_stats["min"]
        )
        clean["benchmark_bucket_max"] = clean["benchmark_return_bucket_id"].map(
            bucket_stats["max"]
        )
        clean["benchmark_bucket_mean"] = clean["benchmark_return_bucket_id"].map(
            bucket_stats["mean"]
        )
        clean["benchmark_bucket_observation_count"] = (
            clean["benchmark_return_bucket_id"].map(bucket_stats["count"]).astype(int)
        )
        clean["timeframe"] = timeframe
        bucket_frames.append(clean[bucket_columns])

    return pd.concat(bucket_frames, ignore_index=True)


def build_benchmark_return_bucket_analysis(
    observations,
    bucket_count=BENCHMARK_RETURN_BUCKET_COUNT,
    align_to_common_horizon_window=False,
):
    output_columns = [
        "timeframe",
        "benchmark_return_bucket_id",
        "benchmark_return_bucket",
        "benchmark_bucket_min",
        "benchmark_bucket_max",
        "benchmark_bucket_mean",
        "benchmark_bucket_observation_count",
        "top_share",
        "top_percent",
        "observation_count",
        "horizon_count",
        COMMON_HORIZON_ALIGNMENT_COLUMN,
        COMMON_HORIZON_WEEK_START_COLUMN,
        COMMON_HORIZON_WEEK_END_COLUMN,
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "downside_deviation",
        "downside_information_ratio",
    ]
    if observations.empty:
        return pd.DataFrame(columns=output_columns)

    alignment_metadata = {}
    if align_to_common_horizon_window:
        observations = align_start_dates_to_common_horizon_window(observations)
        if observations.empty:
            return pd.DataFrame(columns=output_columns)
        alignment_metadata = common_horizon_window_metadata(observations)

    benchmark_column = _annualized_benchmark_column(observations)
    strategy_column = (
        "annualized_strategy_return"
        if "annualized_strategy_return" in observations.columns
        else "strategy_annualized"
    )
    bucket_lookup = _assign_benchmark_return_buckets(observations, bucket_count)
    if bucket_lookup.empty:
        return pd.DataFrame(columns=output_columns)

    grouped_observations = observations.merge(
        bucket_lookup,
        on=["timeframe", "horizon_weeks", "start_timestamp"],
        how="inner",
        validate="many_to_one",
    )
    rows = []
    for (timeframe, bucket_id, top_share), group in grouped_observations.groupby(
        ["timeframe", "benchmark_return_bucket_id", "top_share"],
        sort=False,
    ):
        summary = _summarize_downside_information_ratio_group(
            group.rename(columns={
                benchmark_column: "benchmark_annualized",
                strategy_column: "strategy_annualized",
            })
        )
        bucket = group.iloc[0]
        rows.append({
            "timeframe": timeframe,
            "benchmark_return_bucket_id": int(bucket_id),
            "benchmark_return_bucket": bucket["benchmark_return_bucket"],
            "benchmark_bucket_min": bucket["benchmark_bucket_min"],
            "benchmark_bucket_max": bucket["benchmark_bucket_max"],
            "benchmark_bucket_mean": bucket["benchmark_bucket_mean"],
            "benchmark_bucket_observation_count": int(
                bucket["benchmark_bucket_observation_count"]
            ),
            "top_share": float(top_share),
            "top_percent": round_or_none(float(top_share) * 100),
            "horizon_count": int(group["horizon_weeks"].nunique()),
            **alignment_metadata,
            **summary,
        })

    result = (
        pd.DataFrame(rows, columns=output_columns)
        .sort_values(["timeframe", "benchmark_return_bucket_id", "top_share"])
        .reset_index(drop=True)
    )
    for column in result.columns:
        if column not in {
            "timeframe",
            "benchmark_return_bucket",
            "benchmark_return_bucket_id",
            "benchmark_bucket_observation_count",
            "top_percent",
            "observation_count",
            "horizon_count",
            "downside_count",
        } and pd.api.types.is_numeric_dtype(result[column]):
            result[column] = result[column].round(6)
    return result[output_columns]
