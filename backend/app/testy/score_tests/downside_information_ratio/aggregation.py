import numpy as np
import pandas as pd

from app.testy.score_tests.common.metrics import round_or_none

from .observations import (
    FRACTIONAL_TOP_SHARES,
    PLATEAU_TOLERANCE,
    _build_downside_information_ratio_observation_frame,
    _summarize_downside_information_ratio_group,
)


def _build_downside_information_ratio_by_horizon_frame(
    return_panel,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
    top_shares=FRACTIONAL_TOP_SHARES,
    observations=None,
):
    output_columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "top_share",
        "top_percent",
        "observation_count",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "downside_deviation",
        "downside_information_ratio",
    ]
    if observations is None:
        observations = _build_downside_information_ratio_observation_frame(
            return_panel,
            top_shares=top_shares,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            horizon_week_ranges=horizon_week_ranges,
        )

    if observations.empty:
        return pd.DataFrame(columns=output_columns)

    rows = []
    for (timeframe, horizon_weeks, top_share), group in observations.groupby(
        ["timeframe", "horizon_weeks", "top_share"],
        sort=False,
    ):
        summary = _summarize_downside_information_ratio_group(group)
        rows.append({
            "timeframe": timeframe,
            "horizon_weeks": int(horizon_weeks),
            "horizon_days": float(group["horizon_days"].mean()),
            "top_share": float(top_share),
            "top_percent": float(top_share * 100),
            **summary,
        })

    return (
        pd.DataFrame(rows, columns=output_columns)
        .sort_values(["timeframe", "top_share", "horizon_weeks"])
        .reset_index(drop=True)
    )


def build_downside_information_ratio_by_horizon(
    return_panel,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
    top_shares=FRACTIONAL_TOP_SHARES,
    observations=None,
):
    result = _build_downside_information_ratio_by_horizon_frame(
        return_panel,
        top_shares=top_shares,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        horizon_week_ranges=horizon_week_ranges,
        observations=observations,
    )

    if result.empty:
        return result

    rounded = result.copy()
    for column in rounded.columns:
        if column not in {
            "timeframe",
            "horizon_weeks",
            "horizon_days",
            "observation_count",
            "downside_count",
        }:
            rounded[column] = rounded[column].round(6)
    return rounded


def build_downside_information_ratio_analysis(
    return_panel,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
    top_shares=FRACTIONAL_TOP_SHARES,
    plateau_tolerance=PLATEAU_TOLERANCE,
    by_horizon=None,
):
    output_columns = [
        "timeframe",
        "horizon_week_start",
        "horizon_week_end",
        "horizon_count",
        "aggregation_method",
        "top_share",
        "top_percent",
        "observation_count",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "downside_deviation",
        "downside_information_ratio",
        "neighbor_mean_downside_information_ratio",
        "is_max_downside_information_ratio",
        "is_stability_plateau",
        "is_stable_recommendation",
    ]

    if by_horizon is None:
        by_horizon = _build_downside_information_ratio_by_horizon_frame(
            return_panel,
            top_shares=top_shares,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            horizon_week_ranges=horizon_week_ranges,
        )

    if by_horizon.empty:
        return pd.DataFrame(columns=output_columns)

    rows = []

    for (timeframe, top_share), group in by_horizon.groupby(
        ["timeframe", "top_share"],
        sort=False,
    ):
        rows.append({
            "timeframe": timeframe,
            "horizon_week_start": int(group["horizon_weeks"].min()),
            "horizon_week_end": int(group["horizon_weeks"].max()),
            "horizon_count": int(group["horizon_weeks"].nunique()),
            "aggregation_method": "equal_weight_mean_across_horizons",
            "top_share": float(top_share),
            "top_percent": round_or_none(top_share * 100),
            "observation_count": int(group["observation_count"].sum()),
            "downside_count": int(group["downside_count"].sum()),
            "downside_frequency": round_or_none(
                group["downside_frequency"].mean()
            ),
            "mean_strategy_return": round_or_none(
                group["mean_strategy_return"].mean()
            ),
            "mean_annualized_strategy_return": round_or_none(
                group["mean_annualized_strategy_return"].mean()
            ),
            "mean_benchmark_return": round_or_none(
                group["mean_benchmark_return"].mean()
            ),
            "mean_annualized_benchmark_return": round_or_none(
                group["mean_annualized_benchmark_return"].mean()
            ),
            "mean_annualized_alpha": round_or_none(
                group["mean_annualized_alpha"].mean()
            ),
            "downside_deviation": round_or_none(
                group["downside_deviation"].mean()
            ),
            "downside_information_ratio": round_or_none(
                group["downside_information_ratio"].mean()
            ),
        })

    result = pd.DataFrame(rows).sort_values(
        ["timeframe", "top_share"]
    ).reset_index(drop=True)
    result["neighbor_mean_downside_information_ratio"] = np.nan
    result["is_max_downside_information_ratio"] = False
    result["is_stability_plateau"] = False
    result["is_stable_recommendation"] = False

    for _, timeframe_group in result.groupby("timeframe", sort=False):
        finite_group = timeframe_group[
            np.isfinite(timeframe_group["downside_information_ratio"])
        ].copy()

        if finite_group.empty:
            continue

        neighbor_mean = finite_group["downside_information_ratio"].rolling(
            window=3,
            center=True,
            min_periods=2,
        ).mean()
        result.loc[finite_group.index, "neighbor_mean_downside_information_ratio"] = (
            neighbor_mean.round(6)
        )
        max_index = finite_group["downside_information_ratio"].idxmax()
        max_ratio = float(
            finite_group.loc[max_index, "downside_information_ratio"]
        )
        plateau_margin = plateau_tolerance * max(abs(max_ratio), 1e-12)
        plateau_mask = (
            finite_group["downside_information_ratio"]
            >= max_ratio - plateau_margin
        )
        plateau_indexes = finite_group.index[plateau_mask]

        result.loc[max_index, "is_max_downside_information_ratio"] = True
        result.loc[plateau_indexes, "is_stability_plateau"] = True

        recommendation_candidates = result.loc[plateau_indexes].dropna(
            subset=["neighbor_mean_downside_information_ratio"]
        )
        if recommendation_candidates.empty:
            recommendation_index = max_index
        else:
            recommendation_index = recommendation_candidates[
                "neighbor_mean_downside_information_ratio"
            ].idxmax()
        result.loc[recommendation_index, "is_stable_recommendation"] = True

    return result[output_columns]


def build_downside_information_ratio_observations(
    return_panel,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
    top_shares=(FRACTIONAL_TOP_SHARES),
    observations=None,
    summary=None,
):
    output_columns = [
        "timeframe",
        "top_share",
        "top_percent",
        "observation_id",
        "start_timestamp",
        "horizon_weeks",
        "horizon_days",
        "available_count",
        "effective_selected_count",
        "strategy_return",
        "annualized_strategy_return",
        "benchmark_return",
        "annualized_benchmark_return",
        "annualized_alpha",
        "is_downside",
        "downside_alpha",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "downside_deviation",
    ]
    if observations is None:
        observations = _build_downside_information_ratio_observation_frame(
            return_panel,
            top_shares=top_shares,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            horizon_week_ranges=horizon_week_ranges,
        )

    if observations.empty:
        return pd.DataFrame(columns=output_columns)

    summary_columns = [
        "timeframe",
        "top_share",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "downside_deviation",
    ]
    if summary is None:
        summary = build_downside_information_ratio_analysis(
            return_panel,
            top_shares=top_shares,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            horizon_week_ranges=horizon_week_ranges,
        )
    summary = summary[summary_columns]
    result = observations.rename(columns={
        "strategy_annualized": "annualized_strategy_return",
        "benchmark_annualized": "annualized_benchmark_return",
    }).merge(
        summary,
        on=["timeframe", "top_share"],
        how="left",
        validate="many_to_one",
    )
    result = result.sort_values(
        ["timeframe", "top_share", "horizon_weeks", "start_timestamp"]
    ).reset_index(drop=True)
    result["observation_id"] = (
        result.groupby(["timeframe", "top_share"]).cumcount() + 1
    )

    for column in [
        "effective_selected_count",
        "strategy_return",
        "annualized_strategy_return",
        "benchmark_return",
        "annualized_benchmark_return",
        "annualized_alpha",
        "downside_alpha",
    ]:
        result[column] = result[column].round(6)

    return result[output_columns]
