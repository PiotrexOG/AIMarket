import numpy as np
import pandas as pd

from app.testy.market_return_lookup import load_market_lookup_for_analysis

from .config import (
    CORRELATION_METRICS,
    ENTRY_BUCKET_COLUMNS,
    ENTRY_MIN_SCORE_PERCENTILE,
    ENTRY_PERCENTILE_BUCKET_COUNT,
    ENTRY_PERCENTILE_BUCKET_SIZE,
    LIVE_CORRELATION_METRICS,
    MAX_PROGRESS_BUCKET_PERCENT,
    MIN_PROGRESS_BUCKET_PERCENT,
    PROGRESS_BUCKET_PERCENTAGE_POINTS,
    PROGRESS_WEEK_STEP,
    SWITCH_SCORE_CHANGE_THRESHOLDS,
    USE_ENTRY_PERCENTILE_BUCKETS,
)
from .correlations import (
    _build_correlations_by_horizon,
    _build_horizon_average,
    _build_live_progress_average,
    _build_live_progress_correlations_by_horizon,
)
from .entry_selection import (
    _add_entry_percentile_buckets,
    _entry_percentile_variant_label,
    _entry_percentile_variant_slug,
    _prepare_benchmark_observations,
    _prepare_score_history,
    _prepare_top_entry_observations,
)
from .path_building import (
    _add_full_horizon_benchmark_metrics,
    _build_full_horizon_benchmark_lookup,
    _build_history_lookup,
    _build_path_for_entry,
    _build_remaining_benchmark_lookup,
)
from .path_summaries import (
    _build_observations_and_paths,
    _summarize_entry_path,
    _summarize_live_progress,
)
from .switch_analysis import (
    _build_switch_to_benchmark_threshold_analysis,
    _mark_best_switch_thresholds,
    _summarize_switch_group,
)
from .utilities import (
    _first_existing_columns,
    _first_value_or_none,
    _overlap_days,
    _progress_bucket,
    _progress_weeks_for_horizon,
    _safe_corr,
    _safe_corr_pair,
    _weighted_mean,
)


def _round_numeric_columns(df):
    if df.empty:
        return df
    result = df.copy()
    for column in result.select_dtypes(include=[np.number]).columns:
        if column not in {
            "horizon_days",
            "horizon_weeks",
            "cutoff_weeks",
            "entry_percentile_bucket_id",
            "entry_percentile_bucket_rank_start",
            "entry_percentile_bucket_rank_end",
            "progress_bucket_start_percent",
            "progress_bucket_end_percent",
            "progress_bucket_mid_percent",
            "observation_id",
            "entry_rank_position",
            "entry_available_count",
            "rank_position",
            "available_count",
            "path_point_count",
        }:
            result[column] = result[column].round(6)
    return result


def calculate(
    context,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
    entry_min_score_percentile=ENTRY_MIN_SCORE_PERCENTILE,
    use_entry_percentile_buckets=USE_ENTRY_PERCENTILE_BUCKETS,
):
    history = _prepare_score_history(context.return_panel)
    history_lookup = _build_history_lookup(history)
    entries = _prepare_top_entry_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
        entry_min_score_percentile=entry_min_score_percentile,
        use_entry_percentile_buckets=use_entry_percentile_buckets,
    )
    benchmark_entries = _prepare_benchmark_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
    )
    full_horizon_benchmark_lookup = _build_full_horizon_benchmark_lookup(
        benchmark_entries
    )
    entries = _add_full_horizon_benchmark_metrics(
        entries,
        full_horizon_benchmark_lookup,
    )
    market_source = (
        context.score_observations
        if context.score_observations is not None
        else context.return_panel
    )
    max_cutoff_timestamp = (
        pd.to_datetime(benchmark_entries["future_timestamp"].max())
        if not benchmark_entries.empty
        else pd.to_datetime(context.return_panel["future_timestamp"].max())
    )
    market_lookup = load_market_lookup_for_analysis(
        market_source,
        max_timestamp=max_cutoff_timestamp,
    )
    remaining_benchmark_lookup = _build_remaining_benchmark_lookup(
        benchmark_entries,
        market_lookup,
    )
    observations, live_progress_observations = (
        _build_observations_and_paths(
            entries,
            history_lookup,
            market_lookup,
            remaining_benchmark_lookup,
        )
    )
    alpha_correlations_by_horizon = _build_correlations_by_horizon(
        observations,
        return_metric="annualized_alpha",
    )
    alpha_horizon_average = _build_horizon_average(
        alpha_correlations_by_horizon
    )
    live_progress_alpha_correlations_by_horizon = (
        _build_live_progress_correlations_by_horizon(
            live_progress_observations,
            return_metric="annualized_alpha",
        )
    )
    live_progress_alpha_average = _build_live_progress_average(
        live_progress_alpha_correlations_by_horizon
    )
    switch_to_benchmark_thresholds = (
        _build_switch_to_benchmark_threshold_analysis(
            live_progress_observations,
            group_columns=(
                "entry_percentile_bucket_id",
                "timeframe",
                "progress_bucket_start_percent",
            ),
        )
    )

    return {
        "observations": _round_numeric_columns(observations),
        "horizon_alpha_average": _round_numeric_columns(
            alpha_horizon_average
        ),
        "live_progress_observations": _round_numeric_columns(
            live_progress_observations
        ),
        "live_progress_alpha_average": _round_numeric_columns(
            live_progress_alpha_average
        ),
        "switch_to_benchmark_thresholds": _round_numeric_columns(
            switch_to_benchmark_thresholds
        ),
    }
