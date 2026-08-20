import pandas as pd

from .aggregation import (
    _build_downside_information_ratio_by_horizon_frame,
    build_downside_information_ratio_analysis,
    build_downside_information_ratio_by_horizon,
    build_downside_information_ratio_observations,
)
from .benchmark_buckets import (
    _annualized_benchmark_column,
    _assign_benchmark_return_buckets,
    build_benchmark_return_bucket_analysis,
)
from .observations import (
    BENCHMARK_RETURN_BUCKET_COUNT,
    FRACTIONAL_TOP_SHARES,
    FRACTIONAL_TOP_SHARE_END,
    FRACTIONAL_TOP_SHARE_START,
    FRACTIONAL_TOP_SHARE_STEP,
    PLATEAU_TOLERANCE,
    build_top_m_return_observations,
    _summarize_downside_information_ratio_group,
    build_fractional_top_shares,
)


def calculate(
    context,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
):
    """Calculate all three outputs while building observations only once."""
    raw_observations = build_top_m_return_observations(
        context.weekly_ranked,
        top_shares=FRACTIONAL_TOP_SHARES,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
        already_ranked=True,
    )
    if raw_observations.empty:
        return {
            "analysis": build_downside_information_ratio_analysis(
                context.return_panel,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                horizon_week_ranges=horizon_week_ranges,
                by_horizon=pd.DataFrame(),
            ),
            "by_horizon": build_downside_information_ratio_by_horizon(
                context.return_panel,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                horizon_week_ranges=horizon_week_ranges,
                observations=pd.DataFrame(),
            ),
            "observations": build_downside_information_ratio_observations(
                context.return_panel,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                horizon_week_ranges=horizon_week_ranges,
                observations=pd.DataFrame(),
            ),
            "benchmark_return_buckets": build_benchmark_return_bucket_analysis(
                pd.DataFrame(),
                align_to_common_horizon_window=True,
            ),
        }
    by_horizon = _build_downside_information_ratio_by_horizon_frame(
        context.return_panel,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
        observations=raw_observations,
    )
    analysis = build_downside_information_ratio_analysis(
        context.return_panel,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
        by_horizon=by_horizon,
    )

    observation_shares = FRACTIONAL_TOP_SHARES
    selected_observations = raw_observations[
        raw_observations["top_share"].isin(observation_shares)
    ].copy()
    selected_summary = analysis[
        analysis["top_share"].isin(observation_shares)
    ].copy()
    observations = build_downside_information_ratio_observations(
        context.return_panel,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
        observations=selected_observations,
        summary=selected_summary,
    )
    benchmark_return_buckets = build_benchmark_return_bucket_analysis(
        observations,
        bucket_count=BENCHMARK_RETURN_BUCKET_COUNT,
        align_to_common_horizon_window=True,
    )
    return {
        "analysis": analysis,
        "by_horizon": build_downside_information_ratio_by_horizon(
            context.return_panel,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            horizon_week_ranges=horizon_week_ranges,
            top_shares=FRACTIONAL_TOP_SHARES,
            observations=raw_observations,
        ),
        "observations": observations,
        "benchmark_return_buckets": benchmark_return_buckets,
    }
