import matplotlib.pyplot as plt
import pandas as pd

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    common_horizon_alignment_title_suffix,
    horizon_x_column,
    horizon_x_label,
    limit_horizon_range,
    mean_label,
    plot_path,
    set_integer_x_axis,
    timeframe_label,
)
from app.testy.score_tests.common.output_paths import (
    GLOBAL_INFORMATION_COEFFICIENT_DIR,
)


def build_correlation_output(analysis):
    columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "metric",
        "observation_count",
        "pearson",
    ]
    if analysis.empty:
        return pd.DataFrame(columns=columns)
    return (
        analysis[analysis["test"] == "B2_global_pearson"][columns]
        .sort_values(["timeframe", "horizon_weeks", "metric"])
        .reset_index(drop=True)
    )


def plot(analysis, output_dir):
    data = analysis[analysis["test"] == "B2_global_pearson"].dropna(
        subset=["pearson"]
    )
    for timeframe, timeframe_data in data.groupby("timeframe"):
        timeframe_data = limit_horizon_range(timeframe, timeframe_data)
        if timeframe_data.empty:
            continue
        fig, ax = plt.subplots(figsize=(12, 7))
        x_column = horizon_x_column(timeframe_data)
        for metric, group in timeframe_data.groupby("metric", sort=False):
            group = group.sort_values(x_column)
            ax.plot(
                group[x_column],
                group["pearson"],
                marker="o",
                markevery=max(1, len(group) // 30),
                linewidth=1.8,
                markersize=3,
                label=mean_label(
                        metric,
                        group["pearson"],
                        lambda value: f"{value:.3f}",
                    ),
            )
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{timeframe_label(timeframe, timeframe_data)}: globalne miary IC "
            "dla przyszłych stóp zwrotu"
            f"{common_horizon_alignment_title_suffix(timeframe_data)}"
        )
        ax.set_xlabel(horizon_x_label(timeframe_data))
        set_integer_x_axis(ax)
        ax.set_ylabel("Korelacja")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Średnia z pokazanych horyzontów")
        add_sample_size_note(
            fig,
            timeframe_data,
            "observation_count",
            per="punkt (miara i horyzont)",
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                GLOBAL_INFORMATION_COEFFICIENT_DIR,
                f"{timeframe}_global_information_coefficient.png",
            ),
            dpi=160,
        )
        plt.close(fig)
