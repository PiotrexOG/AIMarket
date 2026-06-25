from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import plot_path


BEST_CORRELATION_METRICS = [
    "mean_score_percentile",
]

LIVE_CORRELATION_METRICS = [
    "mean_score_percentile",
    "relative_score_percentile_change",
]


METRIC_LABELS = {
    "mean_score_percentile": "Mean score percentile",
    "score_percentile_change": (
        "Score percentile change: horizon mean - entry"
    ),
    "relative_score_percentile_change": (
        "Relative score percentile change: (horizon mean - entry) / entry"
    ),
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
        _plot_score_change_progress_correlations(
            live_progress_average,
            output_dir,
            horizon_label,
        )

    if observations is not None and not observations.empty:
        _plot_score_change_scatter(
            observations,
            output_dir,
            horizon_label,
            "relative_score_percentile_change",
        )
        _plot_relative_score_change_heatmap(
            observations,
            output_dir,
            horizon_label,
        )


def _plot_score_change_scatter(
    observations,
    output_dir,
    horizon_label,
    metric,
):
    plot_directory = Path("post_entry_score_path") / horizon_label

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[metric, "annualized_return"]
        ).copy()
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.scatter(
            clean[metric],
            clean["annualized_return"],
            color="#4C78A8",
            alpha=0.10,
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
            trend_x = np.linspace(
                clean[metric].quantile(0.01),
                clean[metric].quantile(0.99),
                100,
            )
            ax.plot(
                trend_x,
                slope * trend_x + intercept,
                color="#E15759",
                linewidth=2.2,
                label="Linear trend",
            )

        pearson = clean[metric].corr(
            clean["annualized_return"],
            method="pearson",
        )
        spearman = clean[metric].corr(
            clean["annualized_return"],
            method="spearman",
        )
        ax.axvline(0, color="#444444", linewidth=1)
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{timeframe}: annualized return versus {METRIC_LABELS[metric]}"
            f"\nPearson {pearson:.2f}, Spearman {spearman:.2f}"
        )
        ax.set_xlabel(METRIC_LABELS[metric])
        ax.set_ylabel("Annualized return")
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_{metric}_scatter.png",
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_score_drop_scatter(
    observations,
    regression_average,
    output_dir,
    horizon_label,
):
    plot_directory = Path("post_entry_score_path") / horizon_label

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "entry_score_percentile",
                "score_percentile_drop",
                "annualized_return",
            ]
        ).copy()
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(13, 8))
        points = ax.scatter(
            clean["score_percentile_drop"],
            clean["annualized_return"],
            c=clean["entry_score_percentile"],
            cmap="viridis",
            vmin=0.60,
            vmax=1.0,
            alpha=0.14,
            s=15,
            edgecolors="none",
        )
        colorbar = fig.colorbar(points, ax=ax)
        colorbar.set_label("Entry score percentile")
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        bins = [0.60, 0.70, 0.80, 0.90, 1.000001]
        labels = ["60–70%", "70–80%", "80–90%", "90–100%"]
        clean["entry_percentile_band"] = pd.cut(
            clean["entry_score_percentile"],
            bins=bins,
            labels=labels,
            right=False,
            include_lowest=True,
        )
        colors = ["#59A14F", "#F28E2B", "#E15759", "#4C78A8"]
        for label, color in zip(labels, colors):
            band = clean[clean["entry_percentile_band"] == label]
            if len(band) < 3 or band["score_percentile_drop"].nunique() < 2:
                continue
            slope, intercept = np.polyfit(
                band["score_percentile_drop"],
                band["annualized_return"],
                1,
            )
            trend_x = np.linspace(
                band["score_percentile_drop"].quantile(0.02),
                band["score_percentile_drop"].quantile(0.98),
                100,
            )
            ax.plot(
                trend_x,
                slope * trend_x + intercept,
                color=color,
                linewidth=2.2,
                label=f"Entry {label}",
            )

        regression_text = ""
        if regression_average is not None and not regression_average.empty:
            row = regression_average[
                regression_average["timeframe"] == timeframe
            ]
            if not row.empty:
                row = row.iloc[0]
                coefficient = row.get(
                    "mean_score_percentile_drop_coefficient"
                )
                negative_share = row.get(
                    "score_drop_negative_coefficient_share"
                )
                if pd.notna(coefficient) and pd.notna(negative_share):
                    regression_text = (
                        f"\nmean drop coefficient {coefficient:.2f}; "
                        f"negative in {negative_share:.0%} of horizons"
                    )

        ax.axvline(0, color="#444444", linewidth=1)
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{timeframe}: return versus post-entry score percentile drop"
            f"{regression_text}"
        )
        ax.set_xlabel(
            "Score percentile drop: entry percentile − horizon mean"
        )
        ax.set_ylabel("Annualized return")
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_score_percentile_drop_scatter.png",
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_relative_score_change_heatmap(
    observations,
    output_dir,
    horizon_label,
):
    plot_directory = Path("post_entry_score_path") / horizon_label
    entry_bins = [value / 100 for value in range(60, 101, 5)]
    entry_bins[-1] = 1.000001
    entry_labels = [
        f"{value}-{value + 5}%"
        for value in range(60, 100, 5)
    ]
    change_bins = [
        -np.inf,
        -0.70,
        -0.60,
        -0.50,
        -0.40,
        -0.30,
        -0.20,
        -0.10,
        0.0,
        0.10,
        0.20,
        0.30,
        np.inf,
    ]
    change_labels = [
        "decline >70%",
        "decline 60-70%",
        "decline 50-60%",
        "decline 40-50%",
        "decline 30-40%",
        "decline 20-30%",
        "decline 10-20%",
        "decline 0-10%",
        "improvement 0-10%",
        "improvement 10-20%",
        "improvement 20-30%",
        "improvement >30%",
    ]

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "entry_score_percentile",
                "relative_score_percentile_change",
                "annualized_return",
            ]
        ).copy()
        clean["entry_band"] = pd.cut(
            clean["entry_score_percentile"],
            bins=entry_bins,
            labels=entry_labels,
            right=False,
            include_lowest=True,
        )
        clean["change_band"] = pd.cut(
            clean["relative_score_percentile_change"],
            bins=change_bins,
            labels=change_labels,
            right=False,
        )
        clean = clean.dropna(subset=["entry_band", "change_band"])
        if clean.empty:
            continue

        mean_returns = clean.pivot_table(
            index="change_band",
            columns="entry_band",
            values="annualized_return",
            aggfunc="mean",
            observed=False,
        ).reindex(index=change_labels, columns=entry_labels)
        counts = clean.pivot_table(
            index="change_band",
            columns="entry_band",
            values="annualized_return",
            aggfunc="count",
            observed=False,
        ).reindex(index=change_labels, columns=entry_labels)

        values = mean_returns.to_numpy(dtype=float)
        finite_values = values[np.isfinite(values)]
        if finite_values.size == 0:
            continue
        color_limit = max(
            abs(float(np.nanpercentile(finite_values, 5))),
            abs(float(np.nanpercentile(finite_values, 95))),
        )
        if color_limit == 0:
            color_limit = 1.0

        fig, ax = plt.subplots(figsize=(15, 10))
        image = ax.imshow(
            values,
            cmap="RdYlGn",
            vmin=-color_limit,
            vmax=color_limit,
            aspect="auto",
        )
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label("Mean annualized return")
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        for row_index in range(len(change_labels)):
            for column_index in range(len(entry_labels)):
                value = values[row_index, column_index]
                count = counts.iloc[row_index, column_index]
                if not np.isfinite(value) or pd.isna(count) or count == 0:
                    continue
                ax.text(
                    column_index,
                    row_index,
                    f"{value:.0%}\nn={int(count)}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="#111111",
                )

        ax.set_xticks(range(len(entry_labels)))
        ax.set_xticklabels(entry_labels)
        ax.set_yticks(range(len(change_labels)))
        ax.set_yticklabels(change_labels)
        ax.set_xlabel("Entry score percentile")
        ax.set_ylabel(
            "Relative score percentile change: (horizon mean - entry) / entry"
        )
        ax.set_title(
            f"{timeframe}: mean return by entry percentile and relative "
            f"score change, "
            f"horizons {horizon_label}"
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_entry_percentile_by_relative_score_change_heatmap.png",
            ),
            dpi=180,
        )
        plt.close(fig)


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


def _plot_score_change_progress_correlations(
    data,
    output_dir,
    horizon_label,
):
    plot_directory = Path("post_entry_score_path") / horizon_label
    metrics = ["relative_score_percentile_change"]

    for (timeframe, metric), clean in data[
        data["metric"].isin(metrics)
    ].groupby(["timeframe", "metric"], sort=False):
        clean = clean.sort_values("progress_percent")
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
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{timeframe}: {METRIC_LABELS[metric]} correlation by elapsed "
            f"horizon, horizons {horizon_label}"
        )
        ax.set_xlabel("Observed share of investment horizon")
        ax.set_ylabel("Mean correlation to final annualized return")
        ax.set_xticks(range(5, 101, 5))
        ax.set_xticklabels(
            [f"{value}%" for value in range(5, 101, 5)],
            rotation=45,
        )
        ax.set_ylim(-1, 1)
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_live_progress_{metric}_correlations.png",
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
