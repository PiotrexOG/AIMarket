import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    plot_path,
)
from app.testy.score_tests.common.output_paths import (
    POST_ENTRY_LIVE_PROGRESS_SECTION,
    POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
)

from .plot_config import METRIC_LABELS
from .plot_helpers import (
    _filter_progress_bucket,
    _plot_context_title_label,
    _post_entry_dir,
)


def _plot_score_change_scatter(
    observations,
    output_dir,
    horizon_label,
    metric,
    return_metric="annualized_return",
    return_label="Roczna stopa zwrotu",
    filename_prefix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    )

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[metric, return_metric]
        ).copy()
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.scatter(
            clean[metric],
            clean[return_metric],
            color="#4C78A8",
            alpha=0.10,
            s=14,
            edgecolors="none",
            label="Obserwacje",
        )

        if clean[metric].nunique() >= 2:
            slope, intercept = np.polyfit(
                clean[metric],
                clean[return_metric],
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
                label="Trend liniowy",
            )

        pearson = clean[metric].corr(
            clean[return_metric],
            method="pearson",
        )
        spearman = clean[metric].corr(
            clean[return_metric],
            method="spearman",
        )
        ax.axvline(0, color="#444444", linewidth=1)
        ax.axhline(0, color="#444444", linewidth=1)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{return_label} względem "
            f"{METRIC_LABELS[metric]}, horyzonty {context_label}"
            f"\nPearson {pearson:.2f}, Spearman {spearman:.2f}"
        )
        ax.set_xlabel(METRIC_LABELS[metric])
        ax.set_ylabel(return_label)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=9)
        add_sample_size_note(fig, clean)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_{filename_prefix}{metric}_scatter.png",
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_remaining_return_at_progress_scatter(
    live_progress_observations,
    output_dir,
    horizon_label,
    metric,
    progress_percent,
    metric_max=None,
    filename_suffix="",
    title_suffix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_LIVE_PROGRESS_SECTION,
    )
    progress_data, progress_label, progress_file_label = (
        _filter_progress_bucket(live_progress_observations, progress_percent)
    )
    return_metric = "remaining_annualized_alpha"

    for timeframe, timeframe_data in progress_data.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[metric, return_metric]
        ).copy()
        if metric_max is not None:
            clean = clean[clean[metric] <= metric_max].copy()
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.scatter(
            clean[metric],
            clean[return_metric],
            color="#59A14F",
            alpha=0.10,
            s=14,
            edgecolors="none",
            label="Obserwacje",
        )

        if clean[metric].nunique() >= 2:
            slope, intercept = np.polyfit(
                clean[metric],
                clean[return_metric],
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
                label="Trend liniowy",
            )

        pearson = clean[metric].corr(
            clean[return_metric],
            method="pearson",
        )
        spearman = clean[metric].corr(
            clean[return_metric],
            method="spearman",
        )
        ax.axvline(0, color="#444444", linewidth=1)
        ax.axhline(0, color="#444444", linewidth=1)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            "Roczny nadwyżkowy zwrot "
            f"z trzymania pozycji po {progress_label} horyzontu, "
            f"horyzonty {context_label}"
            f"{title_suffix}"
            f"\nPearson {pearson:.2f}, Spearman {spearman:.2f}"
        )
        ax.set_xlabel(
            f"{METRIC_LABELS[metric]} po {progress_label} horyzontu"
        )
        ax.set_ylabel(
            "Roczny nadwyżkowy zwrot akcji względem benchmarku "
            "od punktu decyzji do końca horyzontu"
        )
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        if metric_max is not None:
            ax.set_xlim(right=metric_max)
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=9)
        add_sample_size_note(fig, clean)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_{metric}_after_{progress_file_label}_"
                    f"remaining_annualized_return_scatter"
                    f"{filename_suffix}.png"
                ),
            ),
            dpi=180,
        )
        plt.close(fig)


def _add_score_drop_band(data):
    result = data.copy()
    finite_change = result["relative_score_percentile_change"].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    if finite_change.empty:
        result["score_drop_band"] = pd.Series(dtype="category")
        return result, []

    step = 0.05
    lower = min(-step, np.floor(finite_change.min() / step) * step)
    upper = max(step, np.ceil(finite_change.max() / step) * step)
    bins = np.arange(lower, upper + step * 1.01, step)
    labels = [
        f"{left:.0%} do {right:.0%}"
        for left, right in zip(bins[:-1], bins[1:])
    ]
    result["score_drop_band"] = pd.cut(
        result["relative_score_percentile_change"],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True,
    )
    return result, labels


def _plot_hold_decision_by_score_drop(
    live_progress_observations,
    output_dir,
    horizon_label,
    progress_percent,
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_LIVE_PROGRESS_SECTION,
    )
    progress_data, progress_label, progress_file_label = (
        _filter_progress_bucket(live_progress_observations, progress_percent)
    )
    return_metric = "remaining_annualized_alpha"

    for timeframe, timeframe_data in progress_data.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "relative_score_percentile_change",
                return_metric,
            ]
        ).copy()
        clean, labels = _add_score_drop_band(clean)
        clean = clean.dropna(subset=["score_drop_band"])
        if clean.empty:
            continue

        summary = (
            clean.groupby("score_drop_band", observed=False)[
                return_metric
            ]
            .agg(["median", "mean", "count"])
            .reindex(labels)
        )
        valid = summary["count"].fillna(0) > 0
        if not valid.any():
            continue

        summary = summary[valid]
        labels = summary.index.astype(str).tolist()
        x = np.arange(len(summary))
        overall_median = clean[return_metric].median()

        fig, return_ax = plt.subplots(figsize=(16, 8))
        colors = [
            "#E15759" if value < 0 else "#59A14F"
            for value in summary["median"].fillna(0)
        ]
        return_ax.bar(
            x,
            summary["median"],
            color=colors,
            alpha=0.85,
            label="Mediana rocznego nadwyżkowego zwrotu względem benchmarku",
        )
        return_ax.scatter(
            x,
            summary["mean"],
            color="#1F1F1F",
            marker="D",
            s=35,
            zorder=3,
            label="Średnia",
        )
        return_ax.axhline(0, color="#444444", linewidth=1)
        return_ax.axhline(
            overall_median,
            color="#4C78A8",
            linestyle="--",
            linewidth=2,
            label=f"Mediana wszystkich obserwacji: {overall_median:.0%}",
        )
        for index, row in summary.iterrows():
            if pd.isna(row["count"]) or row["count"] == 0:
                continue
            position = labels.index(index)
            value = row["median"]
            return_ax.annotate(
                f"{value:.0%}\nn={int(row['count'])}",
                (position, value),
                xytext=(0, 5 if value >= 0 else -5),
                textcoords="offset points",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=9,
            )
        return_ax.set_ylabel(
            "Roczny nadwyżkowy zwrot akcji względem benchmarku "
            "od punktu decyzji do końca horyzontu"
        )
        return_ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        return_ax.set_xticks(x)
        return_ax.set_xticklabels(labels, rotation=45, ha="right")
        return_ax.set_xlabel(
            f"Względna zmiana percentyla score po {progress_label} "
            "horyzontu"
        )
        return_ax.grid(True, axis="y", alpha=0.2)
        return_ax.legend(fontsize=9)
        context_label = _plot_context_title_label(horizon_label)
        return_ax.set_title(
            "Nadwyżkowy zwrot z trzymania pozycji "
            f"według zmiany score po {progress_label} horyzontu, "
            f"horyzonty {context_label}"
        )
        add_sample_size_note(
            fig,
            clean,
            note=(
                f"n={len(clean)} obserwacji łącznie; dokładne n podano "
                "nad każdym słupkiem"
            ),
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_hold_decision_by_score_drop_after_"
                    f"{progress_file_label}.png"
                ),
            ),
            dpi=180,
        )
        plt.close(fig)
