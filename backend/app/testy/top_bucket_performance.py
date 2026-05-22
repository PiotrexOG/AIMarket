import numpy as np
import pandas as pd


DEBUG_BENCHMARK_HORIZON_DAYS = 300


def annualize_return(total_return, horizon_days):
    if total_return is None or pd.isna(total_return) or horizon_days <= 0:
        return None

    if total_return <= -1:
        return None

    return round(float((1 + total_return) ** (365 / horizon_days) - 1), 6)


def add_benchmark_columns(horizon_summary, quantile_summary):
    if horizon_summary.empty or quantile_summary.empty:
        return quantile_summary

    benchmark = horizon_summary[
        ["timeframe", "horizon_days", "window_positions", "avg_return"]
    ].rename(columns={"avg_return": "benchmark_avg_return"})

    result = quantile_summary.merge(
        benchmark,
        on=["timeframe", "horizon_days", "window_positions"],
        how="left",
    )
    result["excess_avg_return"] = (
        result["avg_return"] - result["benchmark_avg_return"]
    ).round(6)
    result["relative_avg_return_lift"] = np.where(
        result["benchmark_avg_return"].abs() > 1e-9,
        (result["avg_return"] / result["benchmark_avg_return"]) - 1,
        np.nan,
    )
    result["relative_avg_return_lift"] = result["relative_avg_return_lift"].round(6)
    result["annualized_return"] = [
        annualize_return(row.avg_return, row.horizon_days)
        for row in result.itertuples(index=False)
    ]
    result["benchmark_annualized_return"] = [
        annualize_return(row.benchmark_avg_return, row.horizon_days)
        for row in result.itertuples(index=False)
    ]
    result["annualized_excess_return"] = (
        result["annualized_return"] - result["benchmark_annualized_return"]
    ).round(6)

    return result


def build_benchmark_debug_dict(horizon_summary, horizon_days):
    if horizon_summary.empty:
        return {}

    rows = horizon_summary[horizon_summary["horizon_days"] == horizon_days]
    result = {}

    for row in rows.sort_values("timeframe").itertuples(index=False):
        result[row.timeframe] = {
            "horizon_days": int(row.horizon_days),
            "window_positions": int(row.window_positions),
            "sample_count": int(row.count),
            "unique_start_dates": (
                None if pd.isna(row.unique_start_dates)
                else int(row.unique_start_dates)
            ),
            "unique_tickers": (
                None if pd.isna(row.unique_tickers)
                else int(row.unique_tickers)
            ),
            "benchmark_avg_return": (
                None if pd.isna(row.avg_return)
                else round(float(row.avg_return), 6)
            ),
            "benchmark_median_return": (
                None if pd.isna(row.median_return)
                else round(float(row.median_return), 6)
            ),
            "benchmark_win_rate": (
                None if pd.isna(row.win_rate)
                else round(float(row.win_rate), 6)
            ),
        }

    return result
