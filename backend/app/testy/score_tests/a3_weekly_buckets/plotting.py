from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.plotting import (
    limit_horizon_range,
    plot_bucket_average,
    plot_bucket_lines,
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
            "a_tests",
            f"{timeframe}_rank_bucket_annualized_return_lines.png",
            f"{timeframe}: weekly rank bucket annualized return",
            bucket_order,
            show_mean_in_legend=True,
        )
        plot_bucket_average(
            timeframe_data,
            output_dir,
            "a_tests",
            f"{timeframe}_rank_bucket_annualized_return_average.png",
            f"{timeframe}: weekly rank bucket mean annualized return",
            bucket_order,
            score_range_columns=("avg_score_min", "avg_score_max"),
        )
