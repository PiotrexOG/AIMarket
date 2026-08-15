import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.plotting import (
    horizon_x_column,
    horizon_x_label,
    limit_horizon_range,
    mean_label,
    plot_path,
    set_integer_x_axis,
    timeframe_label,
)
from app.testy.score_tests.common.output_paths import (
    GLOBAL_TOP_PERCENT_SELECTION_DIR,
)


def build_top_percent_output(analysis):
    columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "bucket",
        "top_percent",
        "min_score",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    required = set(columns) - {"annualized_return"}
    if analysis.empty or not {*required, "test"}.issubset(analysis.columns):
        return pd.DataFrame(columns=columns)
    selection = analysis[
        (analysis["test"] == "B1_top_percent") & (analysis["bucket"] != "All")
    ]
    return (
        add_annualized_return_column(selection)[columns]
        .sort_values(["timeframe", "horizon_weeks", "top_percent"])
        .reset_index(drop=True)
    )


def plot(analysis, output_dir):
    data = analysis[
        (analysis["test"] == "B1_top_percent") & (analysis["bucket"] != "All")
    ].dropna(subset=["avg_return"])
    data = add_annualized_return_column(data).dropna(subset=["annualized_return"])
    for timeframe, timeframe_data in data.groupby("timeframe"):
        timeframe_data = limit_horizon_range(timeframe, timeframe_data)
        if timeframe_data.empty:
            continue
        fig, ax = plt.subplots(figsize=(12, 7))
        x_column = horizon_x_column(timeframe_data)
        for bucket, group in timeframe_data.groupby("bucket", sort=False):
            group = group.sort_values(x_column)
            ax.plot(
                group[x_column],
                group["annualized_return"],
                marker="o",
                markevery=max(1, len(group) // 30),
                linewidth=1.8,
                markersize=3,
                label=mean_label(
                    bucket,
                    group["annualized_return"],
                    lambda value: f"{value:.1%}",
                ),
            )
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{timeframe_label(timeframe)}: globalny dobór najlepszych X% "
            "i roczna stopa zwrotu"
        )
        ax.set_xlabel(horizon_x_label(timeframe_data))
        set_integer_x_axis(ax)
        ax.set_ylabel("Roczna stopa zwrotu")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.25)
        ax.legend(title="Średnia z pokazanych horyzontów")
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                GLOBAL_TOP_PERCENT_SELECTION_DIR,
                f"{timeframe}_top_percent_annualized_return.png",
            ),
            dpi=160,
        )
        plt.close(fig)
