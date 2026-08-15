import numpy as np
import pandas as pd

from app.testy.score_tests.common.data import (
    align_start_dates_to_common_horizon_window,
    filter_horizon_week_ranges,
)
from app.testy.score_tests.common.annualization import (
    CALENDAR_DAYS_PER_YEAR,
    annualize_return,
)
from app.testy.score_tests.common.metrics import round_or_none


FRACTIONAL_TOP_SHARE_START = 1 / 18
FRACTIONAL_TOP_SHARE_END = 1
FRACTIONAL_TOP_SHARE_STEP = 0.05
PLATEAU_TOLERANCE = 0.05
BENCHMARK_RETURN_BUCKET_COUNT = 10


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
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
    already_ranked=False,
):
    if return_panel.empty:
        return pd.DataFrame()

    ranked = (
        filter_horizon_week_ranges(
            return_panel,
            horizon_week_ranges=horizon_week_ranges,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )
        .dropna(subset=["score", "future_return"])
    )
    if not already_ranked:
        ranked = ranked.sort_values(
            [
                "timeframe",
                "horizon_weeks",
                "horizon_days",
                "start_timestamp",
                "score",
                "ticker",
            ],
            ascending=[True, True, True, True, False, True],
        )

    if ranked.empty:
        return pd.DataFrame()

    observation_frames = []

    for (timeframe, horizon_weeks), horizon_group in ranked.groupby(
        ["timeframe", "horizon_weeks"]
    ):
        horizon_days = float(horizon_group["horizon_days"].mean())
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
                "horizon_weeks": int(horizon_weeks),
                "horizon_days": horizon_days,
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
