from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

from app.testy.score_tests.common.plotting import plot_path


BEST_CORRELATION_METRICS = [
    "mean_score_percentile",
]

LIVE_CORRELATION_METRICS = [
    "mean_score_percentile",
]


METRIC_LABELS = {
    "mean_score_percentile": "Mean score percentile",
}


def plot(results, output_dir, horizon_label):
    if not results:
        return

    correlations = results.get("horizon_average")
    observations = results.get("observations")
    live_progress_average = results.get("live_progress_average")

    if observations is not None and not observations.empty:
        _plot_best_correlation_overview(
            observations,
            correlations,
            output_dir,
            horizon_label,
        )

    if live_progress_average is not None and not live_progress_average.empty:
        _plot_live_progress_correlations(
            live_progress_average,
            output_dir,
            horizon_label,
        )


def _plot_live_progress_correlations(data, output_dir, horizon_label):
    plot_directory = Path("post_entry_score_path") / horizon_label

    for timeframe, timeframe_data in data.groupby("timeframe"):
        clean = timeframe_data[
            timeframe_data["metric"] == "mean_score_percentile"
        ].sort_values("progress_percent")
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(13, 7))
        ax.plot(
            clean["progress_percent"],
            clean["mean_pearson_to_annualized_return"],
            color="#4C78A8",
            marker="o",
            linewidth=2,
            label="Pearson",
        )
        ax.plot(
            clean["progress_percent"],
            clean["mean_spearman_to_annualized_return"],
            color="#F28E2B",
            marker="s",
            linewidth=2,
            label="Spearman",
        )
        ax.set_title(
            f"{timeframe}: mean score percentile correlation by elapsed horizon, "
            f"horizons {horizon_label}"
        )
        ax.set_xlabel("Observed share of investment horizon")
        ax.set_ylabel("Mean correlation to final annualized return")
        ax.set_xticks(range(5, 101, 5))
        ax.set_xticklabels(
            [f"{value}%" for value in range(5, 101, 5)],
            rotation=45,
        )
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_live_progress_mean_score_percentile_correlations.png",
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_best_correlation_overview(
    observations,
    correlations,
    output_dir,
    horizon_label,
):
    plot_directory = Path("post_entry_score_path") / horizon_label

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        correlation_lookup = {}
        if correlations is not None and not correlations.empty:
            timeframe_correlations = correlations[
                correlations["timeframe"] == timeframe
            ]
            correlation_lookup = timeframe_correlations.set_index("metric").to_dict(
                orient="index"
            )

        metric = "mean_score_percentile"
        clean = timeframe_data.dropna(subset=[metric, "annualized_return"]).copy()
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.scatter(
            clean[metric],
            clean["annualized_return"],
            color="#4C78A8",
            alpha=0.12,
            s=14,
            edgecolors="none",
            label="Observations",
        )

        if clean[metric].nunique() >= 2:
            slope, intercept = np.polyfit(
                clean[metric],
                clean["annualized_return"],
                1,
            )
            trend_x = np.linspace(clean[metric].min(), clean[metric].max(), 100)
            ax.plot(
                trend_x,
                slope * trend_x + intercept,
                color="#E15759",
                linewidth=2,
                label="Linear trend",
            )

        stats = correlation_lookup.get(metric, {})
        pearson = stats.get("mean_pearson_to_annualized_return")
        spearman = stats.get("mean_spearman_to_annualized_return")
        correlation_text = ""
        if pearson is not None and spearman is not None:
            correlation_text = (
                f"\nmean horizon correlation: "
                f"Pearson {pearson:.2f}, Spearman {spearman:.2f}"
            )

        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{METRIC_LABELS[metric]}{correlation_text}",
            fontsize=12,
        )
        ax.set_xlabel(METRIC_LABELS[metric])
        ax.set_ylabel("Annualized return")
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_best_correlation_overview.png",
            ),
            dpi=180,
        )
        plt.close(fig)
