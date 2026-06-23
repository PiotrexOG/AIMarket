from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import plot_path


SCATTER_METRICS = [
    "worst_rank_share_from_top",
    "horizon_share_below_top_70",
    "longest_horizon_share_below_top_70",
    "max_rank_share_drop_from_entry",
]

BEST_CORRELATION_METRICS = [
    "worst_score_percentile",
    "mean_score_percentile",
    "horizon_share_score_below_entry",
    "horizon_share_below_top_50",
]


METRIC_LABELS = {
    "mean_rank_share_from_top": "Mean rank share from top",
    "worst_rank_share_from_top": "Worst rank share from top",
    "mean_score_percentile": "Mean score percentile",
    "worst_score_percentile": "Worst score percentile",
    "max_rank_share_drop_from_entry": "Max rank share drop from entry",
    "horizon_share_score_below_entry": "Horizon share score below entry",
    "horizon_share_below_top_50": "Horizon share below top 50%",
    "horizon_share_below_top_70": "Horizon share below top 70%",
    "horizon_share_below_top_90": "Horizon share below top 90%",
    "longest_horizon_share_below_top_50": "Longest share below top 50%",
    "longest_horizon_share_below_top_70": "Longest share below top 70%",
    "longest_horizon_share_below_top_90": "Longest share below top 90%",
}


def plot(results, output_dir, horizon_label):
    if not results:
        return

    correlations = results.get("horizon_average")
    observations = results.get("observations")

    if correlations is not None and not correlations.empty:
        _plot_average_correlations(correlations, output_dir, horizon_label)

    if observations is not None and not observations.empty:
        _plot_scatter_metrics(observations, output_dir, horizon_label)
        _plot_best_correlation_overview(
            observations,
            correlations,
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


def _plot_scatter_metrics(observations, output_dir, horizon_label):
    plot_directory = Path("post_entry_score_path") / horizon_label

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        for metric in SCATTER_METRICS:
            clean = timeframe_data.dropna(subset=[metric, "annualized_return"])
            if clean.empty:
                continue

            fig, ax = plt.subplots(figsize=(11, 7))
            scatter = ax.scatter(
                clean[metric],
                clean["annualized_return"],
                c=clean["horizon_days"],
                cmap="viridis",
                alpha=0.65,
                s=28,
            )
            ax.axhline(0, color="#444444", linewidth=1)
            ax.set_title(
                f"{timeframe}: annualized return vs {METRIC_LABELS.get(metric, metric)}"
            )
            ax.set_xlabel(METRIC_LABELS.get(metric, metric))
            ax.set_ylabel("Annualized return")
            ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            ax.grid(True, alpha=0.25)
            colorbar = fig.colorbar(scatter, ax=ax)
            colorbar.set_label("Horizon days")
            fig.tight_layout()
            fig.savefig(
                plot_path(
                    output_dir,
                    plot_directory,
                    f"{timeframe}_{metric}_scatter.png",
                ),
                dpi=160,
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

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        for ax, metric in zip(axes.flat, BEST_CORRELATION_METRICS):
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

                bucket_count = min(10, clean[metric].nunique())
                clean["metric_bucket"] = pd.qcut(
                    clean[metric],
                    q=bucket_count,
                    duplicates="drop",
                )
                bucket_means = clean.groupby(
                    "metric_bucket",
                    observed=True,
                ).agg(
                    metric_mean=(metric, "mean"),
                    return_mean=("annualized_return", "mean"),
                )
                ax.plot(
                    bucket_means["metric_mean"],
                    bucket_means["return_mean"],
                    color="#F28E2B",
                    marker="o",
                    linewidth=2,
                    markersize=5,
                    label="Quantile means",
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
