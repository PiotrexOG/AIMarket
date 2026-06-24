from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

from app.testy.score_tests.common.plotting import plot_path


BEST_CORRELATION_METRICS = [
    "mean_score_percentile",
    "worst_score_percentile",
]

LIVE_CORRELATION_METRICS = [
    "current_score_percentile",
    "worst_score_percentile",
    "mean_score_percentile",
    "rolling_mean_score_percentile_40",
    "ewma_score_percentile_halflife_40",
]


METRIC_LABELS = {
    "current_score_percentile": "Current",
    "mean_score_percentile": "Mean score percentile",
    "worst_score_percentile": "Worst score percentile",
    "rolling_mean_score_percentile_40": "Rolling mean 40%",
    "ewma_score_percentile_halflife_40": "EWMA half-life 40%",
}


def plot(results, output_dir, horizon_label):
    if not results:
        return

    correlations = results.get("horizon_average")
    observations = results.get("observations")
    live_progress_average = results.get("live_progress_average")

    if correlations is not None and not correlations.empty:
        _plot_average_correlations(correlations, output_dir, horizon_label)

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


def _plot_average_correlations(correlations, output_dir, horizon_label):
    plot_directory = Path("post_entry_score_path") / horizon_label

    for timeframe, data in correlations.groupby("timeframe"):
        clean = data.dropna(subset=["mean_pearson_to_annualized_return"]).copy()
        if clean.empty:
            continue
        clean["label"] = clean["metric"].map(METRIC_LABELS).fillna(clean["metric"])
        clean = clean.sort_values("mean_pearson_to_annualized_return")

        fig_height = max(6, len(clean) * 0.45)
        fig, ax = plt.subplots(figsize=(12, fig_height))
        colors = np.where(
            clean["mean_pearson_to_annualized_return"] >= 0,
            "#4C78A8",
            "#E15759",
        )
        ax.barh(clean["label"], clean["mean_pearson_to_annualized_return"], color=colors)
        ax.axvline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{timeframe}: post-entry score path correlation, horizons {horizon_label}"
        )
        ax.set_xlabel("Mean Pearson correlation to annualized return")
        ax.grid(True, axis="x", alpha=0.25)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_mean_path_metric_correlations.png",
            ),
            dpi=160,
        )
        plt.close(fig)


def _plot_live_progress_correlations(data, output_dir, horizon_label):
    plot_directory = Path("post_entry_score_path") / horizon_label

    for timeframe, timeframe_data in data.groupby("timeframe"):
        correlation_columns = [
            ("mean_pearson_to_annualized_return", "Pearson"),
            ("mean_spearman_to_annualized_return", "Spearman"),
        ]
        colors = plt.cm.tab10(np.linspace(0, 1, len(LIVE_CORRELATION_METRICS)))

        for correlation_column, correlation_label in correlation_columns:
            fig, ax = plt.subplots(figsize=(13, 7))
            for color, metric in zip(colors, LIVE_CORRELATION_METRICS):
                clean = timeframe_data[
                    timeframe_data["metric"] == metric
                ].sort_values("progress_percent")
                if clean.empty:
                    continue
                ax.plot(
                    clean["progress_percent"],
                    clean[correlation_column],
                    color=color,
                    marker="o",
                    markevery=2,
                    markersize=3,
                    linewidth=1.8,
                    label=METRIC_LABELS.get(metric, metric),
                )

            ax.set_title(
                f"{timeframe}: {correlation_label} correlation by elapsed horizon, "
                f"horizons {horizon_label}"
            )
            ax.set_xlabel("Observed share of investment horizon")
            ax.set_ylabel("Mean correlation to final annualized return")
            ax.set_xticks(range(5, 101, 5))
            ax.set_xticklabels(
                [f"{value}%" for value in range(5, 101, 5)],
                rotation=45,
            )
            ax.grid(True, alpha=0.25)
            ax.legend(fontsize=8, ncol=2)

            fig.tight_layout()
            fig.savefig(
                plot_path(
                    output_dir,
                    plot_directory,
                    (
                        f"{timeframe}_live_progress_"
                        f"{correlation_label.lower()}_correlation.png"
                    ),
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

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        for ax, metric in zip(axes, BEST_CORRELATION_METRICS):
            clean = timeframe_data.dropna(subset=[metric, "annualized_return"]).copy()
            if clean.empty:
                ax.set_visible(False)
                continue

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
                f"{METRIC_LABELS.get(metric, metric)}{correlation_text}",
                fontsize=11,
            )
            ax.set_xlabel(METRIC_LABELS.get(metric, metric))
            ax.set_ylabel("Annualized return")
            ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            ax.grid(True, alpha=0.2)
            ax.legend(fontsize=8)

        fig.suptitle(
            f"{timeframe}: strongest post-entry score path relationships, "
            f"horizons {horizon_label}",
            fontsize=15,
        )
        fig.tight_layout(rect=(0, 0, 1, 0.96))
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_best_correlation_overview.png",
            ),
            dpi=180,
        )
        plt.close(fig)
