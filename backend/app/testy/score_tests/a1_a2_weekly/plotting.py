import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

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
    WEEKLY_INFORMATION_COEFFICIENT_DIR,
    WEEKLY_TOP_N_SELECTION_DIR,
)


def plot(analysis, output_dir):
    if analysis.empty:
        return
    _plot_top_n(analysis, output_dir)
    _plot_correlations(analysis, output_dir)


def plot_weekly_information_coefficient(analysis, output_dir):
    if analysis.empty:
        return
    _plot_correlations(analysis, output_dir)


def _plot_top_n(analysis, output_dir):
    data = analysis[
        (analysis["test"] == "A1_top_n") & (analysis["bucket"] != "All 18")
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
            f"{timeframe_label(timeframe)}: tygodniowy dobór najlepszych N spółek "
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
                WEEKLY_TOP_N_SELECTION_DIR,
                f"{timeframe}_top_n_annualized_return.png",
            ),
            dpi=160,
        )
        plt.close(fig)


def _plot_correlations(analysis, output_dir):
    data = analysis[analysis["test"] == "A2_weekly_pearson"].dropna(
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
            f"{timeframe_label(timeframe)}: tygodniowe miary IC "
            "dla przyszłych stóp zwrotu"
        )
        ax.set_xlabel(horizon_x_label(timeframe_data))
        set_integer_x_axis(ax)
        ax.set_ylabel("Średni tygodniowy IC")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Średnia z pokazanych horyzontów")
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                WEEKLY_INFORMATION_COEFFICIENT_DIR,
                f"{timeframe}_weekly_information_coefficient.png",
            ),
            dpi=160,
        )
        plt.close(fig)
