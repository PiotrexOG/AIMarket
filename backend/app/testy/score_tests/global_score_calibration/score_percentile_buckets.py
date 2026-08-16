import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.data import (
    add_common_horizon_window_metadata,
    filter_horizon_week_ranges,
)
from app.testy.score_tests.common.metrics import return_summary, round_or_none
from app.testy.score_tests.common.plotting import (
    limit_horizon_range,
    plot_bucket_average,
    plot_bucket_lines,
    timeframe_label,
)
from app.testy.score_tests.common.output_paths import (
    GLOBAL_SCORE_PERCENTILE_BUCKETS_DIR,
)


BOUNDARIES = np.linspace(0, 100, 19)
DEFAULT_BUCKETS = [
    (BOUNDARIES[index], BOUNDARIES[index + 1])
    for index in range(len(BOUNDARIES) - 1)
]


def calculate(
    context,
    score_buckets=DEFAULT_BUCKETS,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
):
    if context.return_panel.empty:
        return pd.DataFrame()
    rows = []
    ranked_panel = filter_horizon_week_ranges(
        context.global_ranked,
        horizon_week_ranges=horizon_week_ranges,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        align_to_common_horizon_window=True,
    )
    for (timeframe, horizon_weeks), ranked in ranked_panel.groupby(
        ["timeframe", "horizon_weeks"],
        sort=False,
    ):
        horizon_days = ranked["horizon_days"].mean()
        ranked = ranked.dropna(subset=["score"])
        scores = ranked["score"]
        for bucket_start, bucket_end in score_buckets:
            if scores.empty:
                selected = pd.DataFrame()
                min_score = max_score = None
            else:
                min_score = float(scores.quantile(1 - bucket_end / 100))
                max_score = float(scores.quantile(1 - bucket_start / 100))
                selected = ranked[
                    ranked["score"].between(min_score, max_score)
                ]
                if bucket_start > 0:
                    selected = selected[selected["score"] < max_score]
            rows.append({
                "timeframe": timeframe,
                "horizon_weeks": int(horizon_weeks),
                "horizon_days": horizon_days,
                "bucket": f"Top {bucket_start:.1f}-{bucket_end:.1f}%",
                "bucket_start_percent": round(float(bucket_start), 1),
                "bucket_end_percent": round(float(bucket_end), 1),
                "min_score": round_or_none(min_score),
                "max_score": round_or_none(max_score),
                **return_summary(selected),
            })
    return add_common_horizon_window_metadata(pd.DataFrame(rows), source=ranked_panel)


def build_output(analysis):
    columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "bucket",
        "bucket_start_percent",
        "bucket_end_percent",
        "min_score",
        "max_score",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    if analysis.empty:
        return pd.DataFrame(columns=columns)
    return (
        add_annualized_return_column(analysis)[columns]
        .sort_values(["timeframe", "horizon_weeks", "bucket_start_percent"])
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
            timeframe_data[
                ["bucket", "bucket_start_percent", "bucket_end_percent"]
            ]
            .drop_duplicates()
            .sort_values(["bucket_start_percent", "bucket_end_percent"])["bucket"]
            .tolist()
        )
        plot_bucket_lines(
            timeframe_data,
            output_dir,
            GLOBAL_SCORE_PERCENTILE_BUCKETS_DIR,
            f"{timeframe}_score_bucket_annualized_return_lines.png",
            (
                f"{timeframe_label(timeframe, timeframe_data)}: roczna stopa zwrotu "
                "według globalnych koszyków score"
            ),
            bucket_order,
            show_mean_in_legend=True,
        )
        plot_bucket_average(
            timeframe_data,
            output_dir,
            GLOBAL_SCORE_PERCENTILE_BUCKETS_DIR,
            f"{timeframe}_score_bucket_annualized_return_average.png",
            (
                f"{timeframe_label(timeframe, timeframe_data)}: Średnia roczna stopa "
                "zwrotu według globalnych koszyków score"
            ),
            bucket_order,
        )
