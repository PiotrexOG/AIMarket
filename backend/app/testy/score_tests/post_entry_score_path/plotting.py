from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import plot_path, timeframe_label
from app.testy.score_tests.common.output_paths import (
    POST_ENTRY_LIVE_PROGRESS_SECTION,
    POST_ENTRY_SCORE_PATH_DIR,
    POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION,
    horizon_dir,
)
from app.testy.score_tests.post_entry_score_path.calculation import (
    ENTRY_MIN_SCORE_PERCENTILE,
    USE_ENTRY_PERCENTILE_BUCKETS,
)


SCORE_CHANGE_SCATTER_PROGRESS_PERCENT = 25
PROGRESS_BUCKET_PERCENTAGE_POINTS = 5
MIN_PROGRESS_BUCKET_PERCENT = 10
MAX_PROGRESS_BUCKET_PERCENT = 80

ALL_SCORES_SLUG = "all_scores"
ENTRY_MIN_SCORE_PERCENTILE_70_SLUG = "entry_min_score_percentile_70"
ALL_SCORES_ONLY_TIMEFRAME = "long_term_200d"
PLOT_MODE_FULL = "full"
PLOT_MODE_ONLY_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE = (
    "only_live_progress_mean_score_percentile"
)
PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE = (
    "without_live_progress_mean_score_percentile"
)


METRIC_LABELS = {
    "mean_score_percentile": "Średni percentyl score",
    "score_percentile_change": (
        "Zmiana percentyla score: średnia w horyzoncie - wejście"
    ),
    "relative_score_percentile_change": (
        "Względna zmiana percentyla score"
    ),
}

SWITCH_TO_BENCHMARK_METRIC_LABELS = {
    "mean_switch_to_benchmark_annualized_gain": (
        "Średni roczny zysk z przełączenia na benchmark gdy względna zmiana percentyla score <= próg"
    ),
    "downside_deviation": "Downside deviation zysku z przełączenia na benchmark gdy względna zmiana percentyla score <= próg",
    "downside_information_ratio": "Wskaźnik DIR z przełączenia na benchmark gdy względna zmiana percentyla score <= próg"
}


def _entry_percentile_bins_and_labels(data=None):
    if USE_ENTRY_PERCENTILE_BUCKETS and data is not None and not data.empty:
        start_percent = int(
            np.floor(data["entry_score_percentile"].min() * 10) * 10
        )
    elif (
        data is not None
        and not data.empty
        and "entry_min_score_percentile" in data.columns
    ):
        start_percent = int(
            round(float(data["entry_min_score_percentile"].iloc[0]) * 100)
        )
    else:
        start_percent = int(round(ENTRY_MIN_SCORE_PERCENTILE * 100))
    step_percent = 10
    start_percent = max(0, min(90, start_percent))
    boundaries = list(range(start_percent, 101, step_percent))
    if boundaries[-1] != 100:
        boundaries.append(100)

    bins = [value / 100 for value in boundaries]
    bins[-1] = 1.000001
    labels = [
        f"{left}-{right}%"
        for left, right in zip(boundaries[:-1], boundaries[1:])
    ]
    return bins, labels


def _entry_min_score_percentile(data):
    if (
        data is not None
        and not data.empty
        and "entry_min_score_percentile" in data.columns
    ):
        return float(data["entry_min_score_percentile"].iloc[0])
    return ENTRY_MIN_SCORE_PERCENTILE


def _filter_results_for_entry_bucket(results, bucket_id):
    filtered = {}
    for key, value in results.items():
        if (
            isinstance(value, pd.DataFrame)
            and "entry_percentile_bucket_id" in value.columns
        ):
            filtered[key] = value[
                value["entry_percentile_bucket_id"] == bucket_id
            ].copy()
        else:
            filtered[key] = value
    return filtered


def _plot_mode_for_entry_bucket_slug(slug):
    if slug == ALL_SCORES_SLUG:
        return PLOT_MODE_ONLY_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE
    if slug == ENTRY_MIN_SCORE_PERCENTILE_70_SLUG:
        return PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE
    return PLOT_MODE_FULL


def _filter_all_scores_only_plot_data(data):
    if data is None or data.empty or "timeframe" not in data.columns:
        return data
    return data[data["timeframe"] == ALL_SCORES_ONLY_TIMEFRAME]


def _horizon_range_title_label(horizon_label):
    horizon_part = Path(horizon_label).parts[0]
    if horizon_part.endswith("w"):
        horizon_part = horizon_part[:-1]
        return f"{horizon_part} tygodni"
    return str(horizon_part).replace("_", " ")


def _score_scope_title_label(horizon_label):
    parts = Path(horizon_label).parts
    if len(parts) < 2:
        return None

    score_scope = parts[1]
    if score_scope == ALL_SCORES_SLUG:
        return "wszystkie"
    prefix = "entry_min_score_percentile_"
    if score_scope.startswith(prefix):
        return f"top {int(score_scope.removeprefix(prefix))} percentyl"
    return score_scope.replace("_", " ")


def _plot_context_title_label(horizon_label):
    context = _horizon_range_title_label(horizon_label)
    score_scope = _score_scope_title_label(horizon_label)
    if score_scope is not None and score_scope is not "wszystkie":
        context = f"{context}, {score_scope} scores"
    return context


def _post_entry_dir(horizon_label, *sections):
    return horizon_dir(POST_ENTRY_SCORE_PATH_DIR, horizon_label, *sections)


def _target_progress_bucket_start(progress_percent):
    bucket_start = np.floor(
        progress_percent / PROGRESS_BUCKET_PERCENTAGE_POINTS
    ) * PROGRESS_BUCKET_PERCENTAGE_POINTS
    return max(
        float(MIN_PROGRESS_BUCKET_PERCENT),
        min(
            float(MAX_PROGRESS_BUCKET_PERCENT - PROGRESS_BUCKET_PERCENTAGE_POINTS),
            float(bucket_start),
        ),
    )


def _filter_progress_bucket(data, progress_percent):
    if "progress_bucket_start_percent" not in data.columns:
        return (
            data[data["progress_percent"] == progress_percent],
            f"{progress_percent}%",
            f"{progress_percent}pct",
        )

    bucket_start = _target_progress_bucket_start(progress_percent)
    bucket_end = bucket_start + PROGRESS_BUCKET_PERCENTAGE_POINTS
    return (
        data[data["progress_bucket_start_percent"] == bucket_start],
        f"{bucket_start:.0f}-{bucket_end:.0f}%",
        f"{bucket_start:.0f}_{bucket_end:.0f}pct",
    )


def _progress_x_column(data):
    if "progress_bucket_mid_percent" in data.columns:
        return "progress_bucket_mid_percent"
    return "progress_percent"


def _set_progress_x_ticks(ax, data):
    if {
        "progress_bucket_start_percent",
        "progress_bucket_mid_percent",
        "progress_bucket_label",
    }.issubset(data.columns):
        labels = (
            data[
                [
                    "progress_bucket_start_percent",
                    "progress_bucket_mid_percent",
                    "progress_bucket_label",
                ]
            ]
            .drop_duplicates()
            .sort_values("progress_bucket_start_percent")
        )
        ax.set_xticks(labels["progress_bucket_mid_percent"])
        ax.set_xticklabels(labels["progress_bucket_label"], rotation=45)
        return

    ax.set_xticks(range(5, 101, 5))
    ax.set_xticklabels(
        [f"{value}%" for value in range(5, 101, 5)],
        rotation=45,
    )


def plot(
    results,
    output_dir,
    horizon_label,
    split_entry_buckets=True,
    plot_mode=PLOT_MODE_FULL,
):
    if not results:
        return

    alpha_correlations = results.get("horizon_alpha_average")
    observations = results.get("observations")
    live_progress_observations = results.get("live_progress_observations")
    live_progress_alpha_average = results.get("live_progress_alpha_average")
    switch_to_benchmark_thresholds = results.get(
        "switch_to_benchmark_thresholds"
    )

    if (
        split_entry_buckets
        and observations is not None
        and not observations.empty
        and {
            "entry_percentile_bucket_id",
            "entry_percentile_bucket_slug",
        }.issubset(observations.columns)
    ):
        buckets = (
            observations[
                [
                    "entry_percentile_bucket_id",
                    "entry_percentile_bucket_slug",
                ]
            ]
            .drop_duplicates()
            .sort_values("entry_percentile_bucket_id")
        )
        for _, bucket in buckets.iterrows():
            bucket_slug = bucket["entry_percentile_bucket_slug"]
            bucket_results = _filter_results_for_entry_bucket(
                results,
                bucket["entry_percentile_bucket_id"],
            )
            plot(
                bucket_results,
                output_dir,
                Path(horizon_label) / bucket_slug,
                split_entry_buckets=False,
                plot_mode=_plot_mode_for_entry_bucket_slug(bucket_slug),
            )
        return

    if plot_mode == PLOT_MODE_ONLY_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE:
        live_progress_alpha_average = _filter_all_scores_only_plot_data(
            live_progress_alpha_average
        )
        if (
            live_progress_alpha_average is not None
            and not live_progress_alpha_average.empty
        ):
            _plot_live_progress_correlations(
                live_progress_alpha_average,
                output_dir,
                horizon_label,
                return_label=(
                    "końcowy roczny nadwyżkowy zwrot względem benchmarku"
                ),
                filename_prefix="alpha_",
            )
        return

    if observations is not None and not observations.empty:
        _plot_best_correlation_overview(
            observations,
            alpha_correlations,
            output_dir,
            horizon_label,
            return_metric="annualized_alpha",
            return_label="Roczny nadwyżkowy zwrot względem benchmarku",
            filename_prefix="alpha_",
        )

    if (
        live_progress_alpha_average is not None
        and not live_progress_alpha_average.empty
    ):
        if plot_mode != PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE:
            _plot_live_progress_correlations(
                live_progress_alpha_average,
                output_dir,
                horizon_label,
                return_label=(
                    "końcowy roczny nadwyżkowy zwrot względem benchmarku"
                ),
                filename_prefix="alpha_",
            )
        _plot_score_change_progress_correlations(
            live_progress_alpha_average,
            output_dir,
            horizon_label,
            return_label=(
                "końcowy roczny nadwyżkowy zwrot względem benchmarku"
            ),
            filename_prefix="alpha_",
        )

    if observations is not None and not observations.empty:
        _plot_score_change_scatter(
            observations,
            output_dir,
            horizon_label,
            "relative_score_percentile_change",
            return_metric="annualized_alpha",
            return_label="Roczny nadwyżkowy zwrot względem benchmarku",
            filename_prefix="alpha_",
        )
        _plot_relative_score_change_heatmap(
            observations,
            output_dir,
            horizon_label,
            return_metric="annualized_alpha",
            return_label="roczny nadwyżkowy zwrot względem benchmarku",
            filename_prefix="alpha_",
        )

    if (
        live_progress_observations is not None
        and not live_progress_observations.empty
    ):
        _plot_remaining_return_at_progress_scatter(
            live_progress_observations,
            output_dir,
            horizon_label,
            "relative_score_percentile_change",
            SCORE_CHANGE_SCATTER_PROGRESS_PERCENT,
        )
        _plot_remaining_return_at_progress_scatter(
            live_progress_observations,
            output_dir,
            horizon_label,
            "relative_score_percentile_change",
            SCORE_CHANGE_SCATTER_PROGRESS_PERCENT,
            metric_max=0.0,
            filename_suffix="_to_0pct",
            title_suffix=", zmiana percentyla score <= 0%",
        )
        _plot_hold_decision_by_score_drop(
            live_progress_observations,
            output_dir,
            horizon_label,
            SCORE_CHANGE_SCATTER_PROGRESS_PERCENT,
        )

    if (
        switch_to_benchmark_thresholds is not None
        and not switch_to_benchmark_thresholds.empty
    ):
        _plot_switch_to_benchmark_threshold_lines(
            switch_to_benchmark_thresholds,
            output_dir,
            horizon_label,
            SCORE_CHANGE_SCATTER_PROGRESS_PERCENT,
        )
        _plot_switch_to_benchmark_threshold_heatmaps(
            switch_to_benchmark_thresholds,
            output_dir,
            horizon_label,
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
            f"{timeframe_label(timeframe)}: {return_label} względem "
            f"{METRIC_LABELS[metric]}, horyzonty {context_label}"
            f"\nPearson {pearson:.2f}, Spearman {spearman:.2f}"
        )
        ax.set_xlabel(METRIC_LABELS[metric])
        ax.set_ylabel(return_label)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=9)
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
            f"{timeframe_label(timeframe)}: roczny nadwyżkowy zwrot "
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
            f"{timeframe_label(timeframe)}: nadwyżkowy zwrot z trzymania pozycji "
            f"według zmiany score po {progress_label} horyzontu, "
            f"horyzonty {context_label}"
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
            f"{timeframe_label(timeframe)}: przełączenie na benchmark gdy względna zmiana percentyla score <= próg"
            f"po {progress_label} horyzontu, horyzonty {context_label}"
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
                f"{timeframe_label(timeframe)}: "
                f"{SWITCH_TO_BENCHMARK_METRIC_LABELS[metric]}, "
                f"horyzonty {context_label}"
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
            f"{timeframe_label(timeframe)}: pozostała stopa zwrotu według "
            f"pogorszenia score i zmiany ceny, horyzonty {context_label}"
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


def _plot_score_drop_scatter(
    observations,
    regression_average,
    output_dir,
    horizon_label,
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    )

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
            vmin=_entry_min_score_percentile(clean),
            vmax=1.0,
            alpha=0.14,
            s=15,
            edgecolors="none",
        )
        colorbar = fig.colorbar(points, ax=ax)
        colorbar.set_label("Percentyl score przy wejściu")
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        bins, labels = _entry_percentile_bins_and_labels(clean)
        clean["entry_percentile_band"] = pd.cut(
            clean["entry_score_percentile"],
            bins=bins,
            labels=labels,
            right=False,
            include_lowest=True,
        )
        colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))
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
                label=f"Wejście {label}",
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
                        f"\nśredni współczynnik spadku {coefficient:.2f}; "
                        f"ujemny w {negative_share:.0%} horyzontów"
                    )

        ax.axvline(0, color="#444444", linewidth=1)
        ax.axhline(0, color="#444444", linewidth=1)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{timeframe_label(timeframe)}: stopa zwrotu względem spadku "
            "percentyla score po wejściu, "
            f"horyzonty {context_label}"
            f"{regression_text}"
        )
        ax.set_xlabel(
            "Spadek percentyla score: percentyl wejścia - średnia w horyzoncie"
        )
        ax.set_ylabel("Roczna stopa zwrotu")
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
    return_metric="annualized_return",
    return_label="roczna stopa zwrotu",
    filename_prefix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    )
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
        "spadek >70%",
        "spadek 60-70%",
        "spadek 50-60%",
        "spadek 40-50%",
        "spadek 30-40%",
        "spadek 20-30%",
        "spadek 10-20%",
        "spadek 0-10%",
        "poprawa 0-10%",
        "poprawa 10-20%",
        "poprawa 20-30%",
        "poprawa >30%",
    ]

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "entry_score_percentile",
                "relative_score_percentile_change",
                return_metric,
            ]
        ).copy()
        entry_bins, entry_labels = _entry_percentile_bins_and_labels(clean)
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
            values=return_metric,
            aggfunc="mean",
            observed=False,
        ).reindex(index=change_labels, columns=entry_labels)
        counts = clean.pivot_table(
            index="change_band",
            columns="entry_band",
            values=return_metric,
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
        colorbar.set_label(f"Średnia: {return_label}")
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
        ax.set_xlabel("Percentyl score przy wejściu")
        ax.set_ylabel(
            "Względna zmiana percentyla score"
        )
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{timeframe_label(timeframe)}: średnia wartość metryki "
            f"'{return_label}' według percentyla wejścia i względnej zmiany "
            f"score, horyzonty {context_label}"
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_{filename_prefix}"
                    f"entry_percentile_by_relative_score_change_heatmap.png"
                ),
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_live_progress_correlations(
    data,
    output_dir,
    horizon_label,
    return_label="końcowa roczna stopa zwrotu",
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
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{timeframe_label(timeframe)}: korelacja średniego percentyla "
            f"score z upływem horyzontu, horyzonty {context_label}"
        )
        ax.set_xlabel("Zaobserwowana część horyzontu inwestycji")
        ax.set_ylabel(f"Średnia korelacja z metryką: {return_label}")
        _set_progress_x_ticks(ax, clean)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.25)
        ax.legend()
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
    return_label="końcowa roczna stopa zwrotu",
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
        ax.axhline(0, color="#444444", linewidth=1)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{timeframe_label(timeframe)}: korelacja metryki "
            f"'{METRIC_LABELS[metric]}' z upływem horyzontu, "
            f"horyzonty {context_label}"
        )
        ax.set_xlabel("Zaobserwowana część horyzontu inwestycji")
        ax.set_ylabel(f"Średnia korelacja z metryką: {return_label}")
        _set_progress_x_ticks(ax, clean)
        ax.set_ylim(-1, 1)
        ax.grid(True, alpha=0.25)
        ax.legend()
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
    return_label="Roczna stopa zwrotu",
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
            f"{timeframe_label(timeframe)}: {METRIC_LABELS[metric]} "
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
