import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    annotate_sample_sizes,
    plot_path,
)
from app.testy.score_tests.common.output_paths import (
    POST_ENTRY_LIVE_PROGRESS_SECTION,
    POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
)

from .plot_config import METRIC_LABELS
from .plot_helpers import (
    _plot_context_title_label,
    _post_entry_dir,
    _progress_x_column,
    _set_progress_x_ticks,
)


def _annotate_progress_sample_sizes(ax, data, progress_column):
    correlation_columns = [
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
    ]
    required = {progress_column, "mean_observation_count", *correlation_columns}
    if not required.issubset(data.columns):
        return

    annotation_y = data[correlation_columns].max(axis=1, skipna=True)
    annotate_sample_sizes(
        ax,
        data[progress_column],
        annotation_y,
        data["mean_observation_count"],
        label_prefix="śr. n",
    )


def _plot_live_progress_correlations(
    data,
    output_dir,
    horizon_label,
    return_label="końcowa średnia roczna stopa zwrotu",
    filename_prefix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_LIVE_PROGRESS_SECTION,
    )

    for timeframe, timeframe_data in data.groupby("timeframe"):
        clean = timeframe_data[
            timeframe_data["metric"] == "mean_score_percentile"
        ].sort_values(_progress_x_column(timeframe_data))
        if clean.empty:
            continue

        progress_column = _progress_x_column(clean)
        fig, ax = plt.subplots(figsize=(13, 7))
        ax.plot(
            clean[progress_column],
            clean["mean_pearson_to_annualized_return"],
            color="#4C78A8",
            marker="o",
            linewidth=2,
            label="Pearson",
        )
        ax.plot(
            clean[progress_column],
            clean["mean_spearman_to_annualized_return"],
            color="#F28E2B",
            marker="s",
            linewidth=2,
            label="Spearman",
        )
        _annotate_progress_sample_sizes(ax, clean, progress_column)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            "Korelacja średniego percentyla "
            f"score z upływem horyzontu, horyzonty {context_label}"
        )
        ax.set_xlabel("Zaobserwowana część horyzontu inwestycji")
        ax.set_ylabel(f"Średnia korelacja z metryką: {return_label}")
        _set_progress_x_ticks(ax, clean)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.25)
        ax.legend()
        add_sample_size_note(
            fig,
            clean,
            "mean_observation_count",
            per="punkt postępu (średnia liczba obserwacji na horyzont)",
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_{filename_prefix}"
                    f"live_progress_mean_score_percentile_correlations.png"
                ),
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_score_change_progress_correlations(
    data,
    output_dir,
    horizon_label,
    return_label="końcowa średnia roczna stopa zwrotu",
    filename_prefix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_LIVE_PROGRESS_SECTION,
    )
    metrics = ["relative_score_percentile_change"]

    for (timeframe, metric), clean in data[
        data["metric"].isin(metrics)
    ].groupby(["timeframe", "metric"], sort=False):
        clean = clean.sort_values(_progress_x_column(clean))
        if clean.empty:
            continue

        progress_column = _progress_x_column(clean)
        fig, ax = plt.subplots(figsize=(13, 7))
        ax.plot(
            clean[progress_column],
            clean["mean_pearson_to_annualized_return"],
            color="#4C78A8",
            marker="o",
            linewidth=2,
            label="Pearson",
        )
        ax.plot(
            clean[progress_column],
            clean["mean_spearman_to_annualized_return"],
            color="#F28E2B",
            marker="s",
            linewidth=2,
            label="Spearman",
        )
        _annotate_progress_sample_sizes(ax, clean, progress_column)
        ax.axhline(0, color="#444444", linewidth=1)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            "Korelacja metryki "
            f"'{METRIC_LABELS[metric]}' z upływem horyzontu, "
            f"horyzonty {context_label}"
        )
        ax.set_xlabel("Zaobserwowana część horyzontu inwestycji")
        ax.set_ylabel(f"Średnia korelacja z metryką: {return_label}")
        _set_progress_x_ticks(ax, clean)
        ax.set_ylim(-1, 1)
        ax.grid(True, alpha=0.25)
        ax.legend()
        add_sample_size_note(
            fig,
            clean,
            "mean_observation_count",
            per="punkt postępu (średnia liczba obserwacji na horyzont)",
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_{filename_prefix}"
                    f"live_progress_{metric}_correlations.png"
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
    return_metric="annualized_return",
    return_label="Średnia roczna stopa zwrotu",
    filename_prefix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    )

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
        clean = timeframe_data.dropna(subset=[metric, return_metric]).copy()
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.scatter(
            clean[metric],
            clean[return_metric],
            color="#4C78A8",
            alpha=0.12,
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
            trend_x = np.linspace(clean[metric].min(), clean[metric].max(), 100)
            ax.plot(
                trend_x,
                slope * trend_x + intercept,
                color="#E15759",
                linewidth=2,
                label="Trend liniowy",
            )

        stats = correlation_lookup.get(metric, {})
        pearson = stats.get("mean_pearson_to_annualized_return")
        spearman = stats.get("mean_spearman_to_annualized_return")
        correlation_text = ""
        if pearson is not None and spearman is not None:
            correlation_text = (
                f"\nśrednia korelacja horyzontów: "
                f"Pearson {pearson:.2f}, Spearman {spearman:.2f}"
            )

        ax.axhline(0, color="#444444", linewidth=1)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{METRIC_LABELS[metric]} "
            f"względem metryki '{return_label}', "
            f"horyzonty {context_label}{correlation_text}",
            fontsize=12,
        )
        ax.set_xlabel(METRIC_LABELS[metric])
        ax.set_ylabel(return_label)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=8)
        add_sample_size_note(fig, clean)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_{filename_prefix}best_correlation_overview.png",
            ),
            dpi=180,
        )
        plt.close(fig)
