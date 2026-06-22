import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.plotting import limit_horizon_range, plot_path


def plot(analysis, output_dir):
    if analysis.empty:
        return
    _plot_top_n(analysis, output_dir)
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
        for bucket, group in timeframe_data.groupby("bucket", sort=False):
            group = group.sort_values("horizon_days")
            ax.plot(
                group["horizon_days"],
                group["annualized_return"],
                marker="o",
                markevery=max(1, len(group) // 30),
                linewidth=1.8,
                markersize=3,
                label=bucket,
            )
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: weekly annualized return by Top N")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Annualized return")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.25)
        ax.legend(title="Weekly selection")
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "a1_a2_weekly",
                f"{timeframe}_a1_top_n_annualized_return.png",
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
        for metric, group in timeframe_data.groupby("metric", sort=False):
            group = group.sort_values("horizon_days")
            ax.plot(
                group["horizon_days"],
                group["pearson"],
                marker="o",
                markevery=max(1, len(group) // 30),
                linewidth=1.8,
                markersize=3,
                label=metric,
            )
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: mean weekly Pearson correlation")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Mean weekly Pearson correlation")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Metric")
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "a1_a2_weekly",
                f"{timeframe}_a2_weekly_pearson.png",
            ),
            dpi=160,
        )
        plt.close(fig)
