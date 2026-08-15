import pandas as pd

from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.data import filter_horizon_week_ranges
from app.testy.score_tests.common.metrics import (
    average_score_range_summary,
    return_summary,
)
from app.testy.score_tests.common.plotting import (
    limit_horizon_range,
    plot_bucket_average,
    plot_bucket_lines,
    timeframe_label,
)
from app.testy.score_tests.common.output_paths import (
    WEEKLY_RANK_BUCKET_RETURNS_DIR,
)


def calculate(
    context,
    bucket_size=1,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
):
    if context.return_panel.empty:
        return pd.DataFrame()

    ranked = context.weekly_ranked.copy()
    ranked = filter_horizon_week_ranges(
        ranked,
        horizon_week_ranges=horizon_week_ranges,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        align_to_common_horizon_window=True,
    )
    ranked["rank_position"] = (
        ranked.groupby(["timeframe", "horizon_weeks", "start_timestamp"])
        .cumcount()
        + 1
    )
    ranked["bucket_start_rank"] = (
        ((ranked["rank_position"] - 1) // bucket_size) * bucket_size + 1
    )
    ranked["bucket_end_rank"] = ranked["bucket_start_rank"] + bucket_size - 1
    ranked["bucket"] = (
        "Rank "
        + ranked["bucket_start_rank"].astype(str)
    )

    rows = []
    group_columns = [
        "timeframe",
        "horizon_weeks",
        "bucket_start_rank",
        "bucket_end_rank",
        "bucket",
    ]
    for key, bucket_group in ranked.groupby(group_columns, sort=False):
        timeframe, horizon_weeks, bucket_start, bucket_end, bucket = key
        horizon_days = bucket_group["horizon_days"].mean()
        weekly = bucket_group.groupby("start_timestamp", as_index=False).agg(
            future_return=("future_return", "mean"),
            selected_count=("ticker", "count"),
            min_score=("score", "min"),
            max_score=("score", "max"),
        )
        rows.append({
            "timeframe": timeframe,
            "horizon_weeks": int(horizon_weeks),
            "horizon_days": horizon_days,
            "bucket": bucket,
            "bucket_start_rank": int(bucket_start),
            "bucket_end_rank": int(bucket_end),
            **average_score_range_summary(weekly),
            **return_summary(weekly),
        })
    return pd.DataFrame(rows)


def build_output(analysis):
    columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "bucket",
        "bucket_start_rank",
        "bucket_end_rank",
        "avg_score_min",
        "avg_score_max",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    if analysis.empty:
        return pd.DataFrame(columns=columns)
    return (
        add_annualized_return_column(analysis)[columns]
        .sort_values(["timeframe", "horizon_weeks", "bucket_start_rank"])
        .reset_index(drop=True)
    )


def plot(analysis, output_dir):
    if analysis.empty:
        return
    data = add_annualized_return_column(
        analysis.dropna(subset=["avg_return"])
    ).dropna(subset=["annualized_return"])

    for timeframe, timeframe_data in data.groupby("timeframe"):
        timeframe_data = limit_horizon_range(timeframe, timeframe_data)
        if timeframe_data.empty:
            continue
        bucket_order = (
            timeframe_data[["bucket", "bucket_start_rank"]]
            .drop_duplicates()
            .sort_values("bucket_start_rank")["bucket"]
            .tolist()
        )
        plot_bucket_lines(
            timeframe_data,
            output_dir,
            WEEKLY_RANK_BUCKET_RETURNS_DIR,
            f"{timeframe}_rank_bucket_annualized_return_lines.png",
            (
                f"{timeframe_label(timeframe)}: roczna stopa zwrotu "
                "według tygodniowych pozycji w rankingu"
            ),
            bucket_order,
            show_mean_in_legend=True,
        )
        plot_bucket_average(
            timeframe_data,
            output_dir,
            WEEKLY_RANK_BUCKET_RETURNS_DIR,
            f"{timeframe}_rank_bucket_annualized_return_average.png",
            (
                f"{timeframe_label(timeframe)}: Średnia roczna stopa "
                "zwrotu według tygodniowych pozycji w rankingu"
            ),
            bucket_order,
            score_range_columns=("avg_score_min", "avg_score_max"),
        )
