import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import (
    TRADING_DAYS_PER_YEAR,
    annualize_return,
)
from app.testy.score_tests.common.metrics import round_or_none


FRACTIONAL_TOP_SHARE_START = 1 / 18
FRACTIONAL_TOP_SHARE_END = 1
FRACTIONAL_TOP_SHARE_STEP = 0.02
PLATEAU_TOLERANCE = 0.05


def build_fractional_top_shares(
    start=FRACTIONAL_TOP_SHARE_START,
    end=FRACTIONAL_TOP_SHARE_END,
    step=FRACTIONAL_TOP_SHARE_STEP,
):
    shares = []
    value = start

    while value <= end + 1e-12:
        shares.append(float(value))
        value += step

    if shares and not np.isclose(shares[-1], end):
        shares.append(float(end))

    return shares


FRACTIONAL_TOP_SHARES = build_fractional_top_shares()


def _build_downside_information_ratio_observation_frame(
    return_panel,
    top_shares,
    horizon_start,
    horizon_end,
    already_ranked=False,
):
    if return_panel.empty:
        return pd.DataFrame()

    ranked = (
        return_panel[
            return_panel["horizon_days"].between(horizon_start, horizon_end)
        ]
        .dropna(subset=["score", "future_return"])
    )
    if not already_ranked:
        ranked = ranked.sort_values(
            ["timeframe", "horizon_days", "start_timestamp", "score", "ticker"],
            ascending=[True, True, True, False, True],
        )

    if ranked.empty:
        return pd.DataFrame()

    observation_frames = []

    for (timeframe, horizon_days), horizon_group in ranked.groupby(
        ["timeframe", "horizon_days"]
    ):
        start_codes, start_timestamps = pd.factorize(
            horizon_group["start_timestamp"],
            sort=False,
        )
        rank_positions = (
            horizon_group.groupby("start_timestamp").cumcount().to_numpy() + 1
        )
        available_counts = np.bincount(start_codes)
        max_available_count = int(available_counts.max())
        returns_by_rank = np.full(
            (len(available_counts), max_available_count),
            np.nan,
            dtype=float,
        )
        returns_by_rank[start_codes, rank_positions - 1] = (
            horizon_group["future_return"].to_numpy(dtype=float)
        )
        benchmark_returns = np.nanmean(returns_by_rank, axis=1)
        rank_numbers = np.arange(
            1,
            max_available_count + 1,
            dtype=float,
        )[None, :]
        available_counts_column = available_counts[:, None].astype(float)

        for top_share in top_shares:
            target_counts = available_counts_column * float(top_share)
            full_counts = np.floor(target_counts)
            fractional_counts = target_counts - full_counts
            weights = np.where(
                rank_numbers <= full_counts,
                1.0,
                np.where(
                    rank_numbers == full_counts + 1,
                    fractional_counts,
                    0.0,
                ),
            )
            weights = np.where(np.isnan(returns_by_rank), 0.0, weights)
            effective_selected_counts = weights.sum(axis=1)
            valid_selection = effective_selected_counts > 0
            weighted_returns = np.nansum(weights * returns_by_rank, axis=1)
            strategy_returns = np.full(len(available_counts), np.nan, dtype=float)
            strategy_returns[valid_selection] = (
                weighted_returns[valid_selection]
                / effective_selected_counts[valid_selection]
            )
            valid_returns = (
                np.isfinite(strategy_returns)
                & np.isfinite(benchmark_returns)
                & (strategy_returns > -1)
                & (benchmark_returns > -1)
            )

            if not valid_returns.any():
                continue

            strategy_annualized = annualize_return(
                strategy_returns[valid_returns],
                horizon_days
            )
            benchmark_annualized = annualize_return(
                benchmark_returns[valid_returns],
                horizon_days
            )
            annualized_alpha = strategy_annualized - benchmark_annualized
            observation_frames.append(pd.DataFrame({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "start_timestamp": pd.to_datetime(
                    np.asarray(start_timestamps)[valid_returns]
                ),
                "top_share": float(top_share),
                "top_percent": round_or_none(top_share * 100),
                "available_count": available_counts[valid_returns].astype(int),
                "effective_selected_count": (
                    effective_selected_counts[valid_returns]
                ),
                "strategy_return": strategy_returns[valid_returns],
                "strategy_annualized": strategy_annualized,
                "benchmark_return": benchmark_returns[valid_returns],
                "benchmark_annualized": benchmark_annualized,
                "annualized_alpha": annualized_alpha,
                "is_downside": annualized_alpha < 0,
                "downside_alpha": np.minimum(0.0, annualized_alpha),
            }))

    if not observation_frames:
        return pd.DataFrame()

    return pd.concat(observation_frames, ignore_index=True)


def _summarize_downside_information_ratio_group(group):
    annualized_alpha = group["annualized_alpha"].to_numpy(dtype=float)
    downside_alpha = np.minimum(0.0, annualized_alpha)
    mean_alpha = float(annualized_alpha.mean())
    downside_deviation = float(np.sqrt(np.mean(np.square(downside_alpha))))

    if downside_deviation == 0:
        downside_information_ratio = (
            0.0
            if mean_alpha == 0
            else np.inf * np.sign(mean_alpha)
        )
    else:
        downside_information_ratio = mean_alpha / downside_deviation

    return {
        "observation_count": int(len(group)),
        "downside_count": int((annualized_alpha < 0).sum()),
        "downside_frequency": float((annualized_alpha < 0).mean()),
        "mean_strategy_return": float(group["strategy_return"].mean()),
        "mean_annualized_strategy_return": float(
            group["strategy_annualized"].mean()
        ),
        "mean_benchmark_return": float(group["benchmark_return"].mean()),
        "mean_annualized_benchmark_return": float(
            group["benchmark_annualized"].mean()
        ),
        "mean_annualized_alpha": mean_alpha,
        "downside_deviation": downside_deviation,
        "downside_information_ratio": downside_information_ratio,
    }


def _build_downside_information_ratio_by_horizon_frame(
    return_panel,
    horizon_start,
    horizon_end,
    top_shares=FRACTIONAL_TOP_SHARES,
    observations=None,
):
    output_columns = [
        "timeframe",
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
            horizon_end=horizon_end
        )

    if observations.empty:
        return pd.DataFrame(columns=output_columns)

    rows = []
    for (timeframe, horizon_days, top_share), group in observations.groupby(
        ["timeframe", "horizon_days", "top_share"],
        sort=False,
    ):
        summary = _summarize_downside_information_ratio_group(group)
        rows.append({
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
            "top_share": float(top_share),
            "top_percent": float(top_share * 100),
            **summary,
        })

    return (
        pd.DataFrame(rows, columns=output_columns)
        .sort_values(["timeframe", "top_share", "horizon_days"])
        .reset_index(drop=True)
    )


def build_downside_information_ratio_by_horizon(
    return_panel,
    horizon_start,
    horizon_end,
    top_shares=FRACTIONAL_TOP_SHARES,
    observations=None,
):
    result = _build_downside_information_ratio_by_horizon_frame(
        return_panel,
        top_shares=top_shares,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        observations=observations,
    )

    if result.empty:
        return result

    rounded = result.copy()
    for column in rounded.columns:
        if column not in {
            "timeframe",
            "horizon_days",
            "observation_count",
            "downside_count",
        }:
            rounded[column] = rounded[column].round(6)
    return rounded


def build_downside_information_ratio_analysis(
    return_panel,
    horizon_start,
    horizon_end,
    top_shares=FRACTIONAL_TOP_SHARES,
    plateau_tolerance=PLATEAU_TOLERANCE,
    by_horizon=None,
):
    output_columns = [
        "timeframe",
        "horizon_start",
        "horizon_end",
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
            horizon_end=horizon_end
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
            "horizon_start": int(horizon_start),
            "horizon_end": int(horizon_end),
            "horizon_count": int(group["horizon_days"].nunique()),
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
    horizon_start,
    horizon_end,
    top_shares=(FRACTIONAL_TOP_SHARES[0], 1.0),
    observations=None,
    summary=None,
):
    output_columns = [
        "timeframe",
        "top_share",
        "top_percent",
        "observation_id",
        "start_timestamp",
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
            horizon_end=horizon_end
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
            horizon_end=horizon_end
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
        ["timeframe", "top_share", "horizon_days", "start_timestamp"]
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


def calculate(context, horizon_start, horizon_end):
    """Calculate all three outputs while building observations only once."""
    raw_observations = _build_downside_information_ratio_observation_frame(
        context.weekly_ranked,
        top_shares=FRACTIONAL_TOP_SHARES,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        already_ranked=True,
    )
    if raw_observations.empty:
        return {
            "analysis": build_downside_information_ratio_analysis(
                context.return_panel,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                by_horizon=pd.DataFrame(),
            ),
            "by_horizon": build_downside_information_ratio_by_horizon(
                context.return_panel,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                observations=pd.DataFrame(),
            ),
            "observations": build_downside_information_ratio_observations(
                context.return_panel,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                observations=pd.DataFrame(),
            ),
        }
    by_horizon = _build_downside_information_ratio_by_horizon_frame(
        context.return_panel,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        observations=raw_observations,
    )
    analysis = build_downside_information_ratio_analysis(
        context.return_panel,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        by_horizon=by_horizon,
    )

    observation_shares = (FRACTIONAL_TOP_SHARES[0], 1.0)
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
        observations=selected_observations,
        summary=selected_summary,
    )
    return {
        "analysis": analysis,
        "by_horizon": build_downside_information_ratio_by_horizon(
            context.return_panel,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            top_shares=FRACTIONAL_TOP_SHARES,
            observations=raw_observations,
        ),
        "observations": observations,
    }
