import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import (
    CALENDAR_DAYS_PER_YEAR,
    annualize_return,
)
from app.testy.score_tests.downside_information_ratio.observations import (
    FRACTIONAL_TOP_SHARES,
    build_top_m_return_observations,
)


BY_HORIZON_COLUMNS = [
    "timeframe",
    "horizon_weeks",
    "horizon_days",
    "top_share",
    "top_percent",
    "observation_count",
    "mean_strategy_return",
    "mean_benchmark_return",
    "mean_annualized_strategy_return",
    "mean_annualized_benchmark_return",
    "annual_risk_free_rate",
    "horizon_risk_free_rate",
    "beta",
    "jensen_alpha",
    "annualized_jensen_alpha",
]

ANALYSIS_COLUMNS = [
    "timeframe",
    "horizon_week_start",
    "horizon_week_end",
    "horizon_count",
    "aggregation_method",
    "top_share",
    "top_percent",
    "observation_count",
    "annual_risk_free_rate",
    "beta",
    "annualized_jensen_alpha",
]

MIN_CAPM_OBSERVATIONS = 3


def _calculate_beta(strategy_returns, benchmark_returns):
    """Return the OLS/CAPM slope of portfolio returns on benchmark returns."""
    strategy = np.asarray(strategy_returns, dtype=float)
    benchmark = np.asarray(benchmark_returns, dtype=float)
    finite = np.isfinite(strategy) & np.isfinite(benchmark)
    strategy = strategy[finite]
    benchmark = benchmark[finite]

    if len(strategy) < MIN_CAPM_OBSERVATIONS:
        return np.nan

    benchmark_centered = benchmark - benchmark.mean()
    benchmark_sum_of_squares = float(
        np.dot(benchmark_centered, benchmark_centered)
    )
    benchmark_scale = float(np.dot(benchmark, benchmark))
    variance_tolerance = (
        np.finfo(float).eps
        * max(benchmark_scale, np.finfo(float).tiny)
    )
    if benchmark_sum_of_squares <= variance_tolerance:
        return np.nan

    strategy_centered = strategy - strategy.mean()
    return float(
        np.dot(strategy_centered, benchmark_centered)
        / benchmark_sum_of_squares
    )


def _horizon_risk_free_rate(annual_risk_free_rate, horizon_days):
    if annual_risk_free_rate <= -1 or horizon_days <= 0:
        return np.nan
    return float(
        np.power(
            1.0 + annual_risk_free_rate,
            horizon_days / CALENDAR_DAYS_PER_YEAR,
        )
        - 1.0
    )


def _summarize_horizon(group, annual_risk_free_rate):
    horizon_days = float(group["horizon_days"].mean())
    beta = _calculate_beta(
        group["strategy_return"],
        group["benchmark_return"],
    )
    mean_strategy_return = float(group["strategy_return"].mean())
    mean_benchmark_return = float(group["benchmark_return"].mean())
    mean_annualized_strategy_return = float(
        group["strategy_annualized"].mean()
    )
    mean_annualized_benchmark_return = float(
        group["benchmark_annualized"].mean()
    )
    horizon_risk_free_rate = _horizon_risk_free_rate(
        annual_risk_free_rate,
        horizon_days,
    )
    jensen_alpha = (
        mean_strategy_return
        - (
            horizon_risk_free_rate
            + beta
            * (
                mean_benchmark_return
                - horizon_risk_free_rate
            )
        )
        if np.isfinite(beta) and np.isfinite(horizon_risk_free_rate)
        else np.nan
    )
    annualized_jensen_alpha = (
        annualize_return(jensen_alpha, horizon_days)
        if np.isfinite(jensen_alpha)
        else None
    )

    return {
        "observation_count": int(len(group)),
        "mean_strategy_return": mean_strategy_return,
        "mean_benchmark_return": mean_benchmark_return,
        "mean_annualized_strategy_return": mean_annualized_strategy_return,
        "mean_annualized_benchmark_return": (
            mean_annualized_benchmark_return
        ),
        "annual_risk_free_rate": annual_risk_free_rate,
        "horizon_risk_free_rate": horizon_risk_free_rate,
        "beta": beta,
        "jensen_alpha": jensen_alpha,
        "annualized_jensen_alpha": (
            np.nan
            if annualized_jensen_alpha is None
            else annualized_jensen_alpha
        ),
    }


def _empty_result():
    return {
        "analysis": pd.DataFrame(columns=ANALYSIS_COLUMNS),
        "by_horizon": pd.DataFrame(columns=BY_HORIZON_COLUMNS),
    }


def calculate(
    context,
    horizon_week_ranges=None,
    annual_risk_free_rate=0.04,
    top_shares=FRACTIONAL_TOP_SHARES,
):
    """Calculate CAPM beta and Jensen's alpha for Top M% portfolios."""
    observations = build_top_m_return_observations(
        context.weekly_ranked,
        top_shares=top_shares,
        horizon_week_ranges=horizon_week_ranges,
        already_ranked=True,
    )
    if observations.empty:
        return _empty_result()

    annual_risk_free_rate = float(annual_risk_free_rate)
    by_horizon_rows = []
    group_columns = ["timeframe", "horizon_weeks", "top_share"]
    for keys, group in observations.groupby(group_columns, sort=False):
        timeframe, horizon_weeks, top_share = keys
        by_horizon_rows.append({
            "timeframe": timeframe,
            "horizon_weeks": int(horizon_weeks),
            "horizon_days": float(group["horizon_days"].mean()),
            "top_share": float(top_share),
            "top_percent": float(top_share * 100),
            **_summarize_horizon(group, annual_risk_free_rate),
        })

    by_horizon = (
        pd.DataFrame(by_horizon_rows, columns=BY_HORIZON_COLUMNS)
        .sort_values(["timeframe", "top_share", "horizon_weeks"])
        .reset_index(drop=True)
    )

    analysis_rows = []
    for (timeframe, top_share), group in by_horizon.groupby(
        ["timeframe", "top_share"],
        sort=False,
    ):
        valid_group = group.dropna(
            subset=["beta", "annualized_jensen_alpha"]
        )
        if valid_group.empty:
            continue

        analysis_rows.append({
            "timeframe": timeframe,
            "horizon_week_start": int(valid_group["horizon_weeks"].min()),
            "horizon_week_end": int(valid_group["horizon_weeks"].max()),
            "horizon_count": int(valid_group["horizon_weeks"].nunique()),
            "aggregation_method": "equal_weight_mean_across_valid_horizons",
            "top_share": float(top_share),
            "top_percent": float(top_share * 100),
            "observation_count": int(
                valid_group["observation_count"].sum()
            ),
            "annual_risk_free_rate": annual_risk_free_rate,
            "beta": float(valid_group["beta"].mean()),
            "annualized_jensen_alpha": float(
                valid_group["annualized_jensen_alpha"].mean()
            ),
        })

    analysis = (
        pd.DataFrame(analysis_rows, columns=ANALYSIS_COLUMNS)
        .sort_values(["timeframe", "top_share"])
        .reset_index(drop=True)
    )
    return {
        "analysis": analysis,
        "by_horizon": by_horizon,
    }
