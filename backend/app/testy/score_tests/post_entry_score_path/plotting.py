from pathlib import Path

from .correlation_plots import (
    _plot_best_correlation_overview,
    _plot_live_progress_correlations,
    _plot_score_change_progress_correlations,
)
from .heatmap_plots import (
    _plot_relative_score_change_heatmap,
)
from .plot_config import (
    PLOT_MODE_FULL,
    PLOT_MODE_ONLY_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE,
    PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE,
    SCORE_CHANGE_SCATTER_PROGRESS_PERCENT,
)
from .plot_helpers import (
    _filter_all_scores_only_plot_data,
    _filter_results_for_entry_bucket,
    _plot_mode_for_entry_bucket_slug,
)
from .score_path_plots import (
    _plot_hold_decision_by_score_drop,
    _plot_remaining_return_at_progress_scatter,
    _plot_score_change_scatter,
)
from .switch_plots import (
    _plot_switch_to_benchmark_threshold_heatmaps,
    _plot_switch_to_benchmark_threshold_lines,
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
        observations = _filter_all_scores_only_plot_data(observations)
        alpha_correlations = _filter_all_scores_only_plot_data(
            alpha_correlations
        )
        live_progress_alpha_average = _filter_all_scores_only_plot_data(
            live_progress_alpha_average
        )
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
            _plot_relative_score_change_heatmap(
                observations,
                output_dir,
                horizon_label,
                return_metric="annualized_alpha",
                return_label=(
                    "roczny nadwyżkowy zwrot względem benchmarku"
                ),
                filename_prefix="alpha_",
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

    if (
        plot_mode != PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE
        and observations is not None
        and not observations.empty
    ):
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
        if plot_mode != PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE:
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
