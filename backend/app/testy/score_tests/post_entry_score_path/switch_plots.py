import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    annotate_sample_sizes,
    plot_path,
)
from app.testy.score_tests.common.output_paths import (
    POST_ENTRY_LIVE_PROGRESS_SECTION,
    POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION,
)

from .plot_config import SWITCH_TO_BENCHMARK_METRIC_LABELS
from .plot_helpers import (
    _filter_progress_bucket,
    _plot_context_title_label,
    _post_entry_dir,
    _progress_x_column,
)
from .score_path_plots import _add_score_drop_band


def _plot_switch_to_benchmark_threshold_lines(
    threshold_analysis,
    output_dir,
    horizon_label,
    progress_percent,
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION,
    )
    progress_data, progress_label, progress_file_label = (
        _filter_progress_bucket(threshold_analysis, progress_percent)
    )
    progress_data = progress_data.replace([np.inf, -np.inf], np.nan)

    required_columns = [
        "score_change_threshold",
        "mean_switch_to_benchmark_annualized_gain",
        "downside_deviation",
        "downside_information_ratio",
        "switch_share",
    ]
    for timeframe, timeframe_data in progress_data.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "score_change_threshold",
                "mean_switch_to_benchmark_annualized_gain",
                "downside_deviation",
            ]
        ).sort_values("score_change_threshold")
        if clean.empty or not set(required_columns).issubset(clean.columns):
            continue

        fig, gain_ax = plt.subplots(figsize=(14, 8))
        gain_ax.plot(
            clean["score_change_threshold"],
            clean["mean_switch_to_benchmark_annualized_gain"],
            color="#4C78A8",
            marker="o",
            linewidth=2,
            label="Średni roczny zysk z przełączenia",
        )
        gain_ax.plot(
            clean["score_change_threshold"],
            clean["downside_deviation"],
            color="#E15759",
            marker="s",
            linewidth=2,
            label="Downside deviation",
        )
        if "switch_count" in clean.columns:
            annotate_sample_sizes(
                gain_ax,
                clean["score_change_threshold"],
                clean["mean_switch_to_benchmark_annualized_gain"],
                clean["switch_count"],
            )
        gain_ax.axhline(0, color="#444444", linewidth=1)
        gain_ax.axvline(0, color="#444444", linewidth=1)
        gain_ax.set_xlabel(
            "Względna zmiana percentyla score"
        )
        gain_ax.set_ylabel(
            "Roczna różnica stopy zwrotu względem trzymania akcji"
        )
        gain_ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        gain_ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        gain_ax.grid(True, alpha=0.25)

        ratio_ax = gain_ax.twinx()
        ratio_clean = clean.dropna(subset=["downside_information_ratio"])
        if not ratio_clean.empty:
            ratio_ax.plot(
                ratio_clean["score_change_threshold"],
                ratio_clean["downside_information_ratio"],
                color="#59A14F",
                marker="D",
                linewidth=2,
                label="Wskaźnik DIR",
            )
            best = ratio_clean.loc[
                ratio_clean["downside_information_ratio"].idxmax()
            ]
            ratio_ax.scatter(
                [best["score_change_threshold"]],
                [best["downside_information_ratio"]],
                color="#1F1F1F",
                s=70,
                zorder=5,
                label=(
                    "Najlepszy DIR: "
                    f"{best['score_change_threshold']:.0%}, "
                    f"{best['downside_information_ratio']:.2f}"
                ),
            )
        ratio_ax.set_ylabel("Wskaźnik DIR")

        lines, labels = gain_ax.get_legend_handles_labels()
        ratio_lines, ratio_labels = ratio_ax.get_legend_handles_labels()
        gain_ax.legend(
            lines + ratio_lines,
            labels + ratio_labels,
            fontsize=9,
            loc="best",
        )
        context_label = _plot_context_title_label(horizon_label)
        gain_ax.set_title(
            "Przełączenie na benchmark gdy "
            "względna zmiana percentyla score \N{LESS-THAN OR EQUAL TO} próg "
            f"po {progress_label} horyzontu, horyzonty {context_label}"
        )
        add_sample_size_note(
            fig,
            clean,
            "switch_count",
            per="punkt progu (obserwacje spełniające warunek przełączenia)",
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_switch_to_benchmark_thresholds_after_"
                    f"{progress_file_label}.png"
                ),
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_switch_to_benchmark_threshold_heatmaps(
    threshold_analysis,
    output_dir,
    horizon_label,
    threshold_axis_label=(
        "Względna zmiana percentyla score"
    ),
    filename_suffix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION,
    )
    metrics = [
        "mean_switch_to_benchmark_annualized_gain",
        "downside_deviation",
        "downside_information_ratio",
    ]

    for timeframe, timeframe_data in threshold_analysis.groupby("timeframe"):
        for metric in metrics:
            progress_column = _progress_x_column(timeframe_data)
            progress_label_column = (
                "progress_bucket_label"
                if "progress_bucket_label" in timeframe_data.columns
                else None
            )
            clean = timeframe_data.replace([np.inf, -np.inf], np.nan).dropna(
                subset=[progress_column, "score_change_threshold", metric]
            )
            if clean.empty:
                continue

            progress_order = sorted(clean[progress_column].unique())
            if progress_label_column:
                progress_labels = (
                    clean[[progress_column, progress_label_column]]
                    .drop_duplicates()
                    .sort_values(progress_column)[progress_label_column]
                    .astype(str)
                    .tolist()
                )
            else:
                progress_labels = [f"{progress}%" for progress in progress_order]
            threshold_order = sorted(clean["score_change_threshold"].unique())
            threshold_labels = [
                f"{threshold:.0%}" for threshold in threshold_order
            ]
            matrix = (
                clean.pivot_table(
                    index=progress_column,
                    columns="score_change_threshold",
                    values=metric,
                    aggfunc="mean",
                    observed=False,
                )
                .reindex(index=progress_order, columns=threshold_order)
            )
            counts = (
                clean.pivot_table(
                    index=progress_column,
                    columns="score_change_threshold",
                    values="switch_count",
                    aggfunc="max",
                    observed=False,
                )
                .reindex(index=progress_order, columns=threshold_order)
                if "switch_count" in clean.columns
                else None
            )
            values = matrix.to_numpy(dtype=float)
            finite_values = values[np.isfinite(values)]
            if finite_values.size == 0:
                continue

            if metric == "downside_deviation":
                lower = 0.0
                upper = float(np.nanpercentile(finite_values, 95))
                if upper == 0:
                    upper = float(np.nanmax(finite_values)) or 1.0
                cmap = "RdYlGn_r"
            else:
                color_limit = max(
                    abs(float(np.nanpercentile(finite_values, 5))),
                    abs(float(np.nanpercentile(finite_values, 95))),
                )
                if color_limit == 0:
                    color_limit = 1.0
                lower = -color_limit
                upper = color_limit
                cmap = "RdYlGn"

            fig, ax = plt.subplots(figsize=(16, 9))
            image = ax.imshow(
                values,
                cmap=cmap,
                vmin=lower,
                vmax=upper,
                aspect="auto",
            )
            if counts is not None:
                for row_index in range(len(progress_order)):
                    for column_index in range(len(threshold_order)):
                        value = values[row_index, column_index]
                        count = counts.iloc[row_index, column_index]
                        if not np.isfinite(value) or pd.isna(count) or count <= 0:
                            continue
                        value_text = (
                            f"{value:.2f}"
                            if metric == "downside_information_ratio"
                            else f"{value:.1%}"
                        )
                        ax.text(
                            column_index,
                            row_index,
                            f"{value_text}\nn={int(count)}",
                            ha="center",
                            va="center",
                            fontsize=6,
                            color="#111111",
                        )
            colorbar = fig.colorbar(image, ax=ax)
            colorbar.set_label(SWITCH_TO_BENCHMARK_METRIC_LABELS[metric])
            if metric != "downside_information_ratio":
                colorbar.ax.yaxis.set_major_formatter(
                    mtick.PercentFormatter(1.0)
                )

            ax.set_xticks(range(len(threshold_order)))
            ax.set_xticklabels(
                threshold_labels,
                rotation=45,
                ha="right",
            )
            ax.set_yticks(range(len(progress_order)))
            ax.set_yticklabels(progress_labels)
            ax.set_xlabel(threshold_axis_label)
            ax.set_ylabel("Zaobserwowana część horyzontu inwestycji")
            context_label = _plot_context_title_label(horizon_label)
            ax.set_title(
                f"{SWITCH_TO_BENCHMARK_METRIC_LABELS[metric]}, "
                f"horyzonty {context_label}"
            )
            add_sample_size_note(
                fig,
                clean,
                "switch_count",
                per=(
                    "komórkę (punkt postępu i próg; obserwacje spełniające "
                    "warunek przełączenia)"
                ),
            )
            fig.tight_layout()
            fig.savefig(
                plot_path(
                    output_dir,
                    plot_directory,
                    (
                        f"{timeframe}_switch_to_benchmark{filename_suffix}_"
                        f"{metric}_heatmap.png"
                    ),
                ),
                dpi=180,
            )
            plt.close(fig)


def _plot_hold_decision_heatmap(
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
    price_bins = [-np.inf, -0.30, -0.15, 0.0, 0.15, np.inf]
    price_labels = [
        "spadek ceny >30%",
        "spadek ceny 15-30%",
        "spadek ceny 0-15%",
        "wzrost ceny 0-15%",
        "wzrost ceny >15%",
    ]

    for timeframe, timeframe_data in progress_data.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "relative_score_percentile_change",
                "price_change_to_cutoff",
                "remaining_annualized_return",
            ]
        ).copy()
        clean, score_labels = _add_score_drop_band(clean)
        clean["price_change_band"] = pd.cut(
            clean["price_change_to_cutoff"],
            bins=price_bins,
            labels=price_labels,
            right=False,
            include_lowest=True,
        )
        clean = clean.dropna(
            subset=["score_drop_band", "price_change_band"]
        )
        if clean.empty:
            continue

        median_returns = clean.pivot_table(
            index="score_drop_band",
            columns="price_change_band",
            values="remaining_annualized_return",
            aggfunc="median",
            observed=False,
        ).reindex(index=score_labels, columns=price_labels)
        counts = clean.pivot_table(
            index="score_drop_band",
            columns="price_change_band",
            values="remaining_annualized_return",
            aggfunc="count",
            observed=False,
        ).reindex(index=score_labels, columns=price_labels)
        positive_share = (
            clean.assign(
                positive=clean["remaining_annualized_return"] > 0
            )
            .pivot_table(
                index="score_drop_band",
                columns="price_change_band",
                values="positive",
                aggfunc="mean",
                observed=False,
            )
            .reindex(index=score_labels, columns=price_labels)
        )

        values = median_returns.to_numpy(dtype=float)
        finite_values = values[np.isfinite(values)]
        if finite_values.size == 0:
            continue
        color_limit = max(
            abs(float(np.nanpercentile(finite_values, 10))),
            abs(float(np.nanpercentile(finite_values, 90))),
        )
        if color_limit == 0:
            color_limit = 1.0

        fig, ax = plt.subplots(figsize=(14, 9))
        image = ax.imshow(
            values,
            cmap="RdYlGn",
            vmin=-color_limit,
            vmax=color_limit,
            aspect="auto",
        )
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label("Mediana pozostałej rocznej stopy zwrotu")
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        for row_index in range(len(score_labels)):
            for column_index in range(len(price_labels)):
                value = values[row_index, column_index]
                count = counts.iloc[row_index, column_index]
                probability = positive_share.iloc[
                    row_index, column_index
                ]
                if not np.isfinite(value) or pd.isna(count) or count == 0:
                    continue
                ax.text(
                    column_index,
                    row_index,
                    (
                        f"mediana {value:.0%}\n"
                        f"udział >0 {probability:.0%}\n"
                        f"n={int(count)}"
                    ),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="#111111",
                )

        ax.set_xticks(range(len(price_labels)))
        ax.set_xticklabels(price_labels, rotation=20, ha="right")
        ax.set_yticks(range(len(score_labels)))
        ax.set_yticklabels(score_labels)
        ax.set_xlabel(
            f"Zmiana ceny od wejścia do punktu decyzji {progress_label}"
        )
        ax.set_ylabel(
            f"Względna zmiana percentyla score do punktu decyzji {progress_label}"
        )
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            "Pozostała stopa zwrotu według "
            f"pogorszenia score i zmiany ceny, horyzonty {context_label}"
        )
        add_sample_size_note(
            fig,
            clean,
            note=(
                f"n={len(clean)} obserwacji łącznie; dokładne n podano "
                "w każdej niepustej komórce"
            ),
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_hold_decision_score_drop_by_price_change_"
                    f"after_{progress_file_label}_heatmap.png"
                ),
            ),
            dpi=180,
        )
        plt.close(fig)
