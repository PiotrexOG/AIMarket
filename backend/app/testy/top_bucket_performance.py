import numpy as np
import pandas as pd


DEBUG_BENCHMARK_HORIZON_DAYS = 300
ABSOLUTE_SCORE_THRESHOLDS = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
STABILITY_HORIZON_WINDOWS = [
    ("all_horizons", 1, 419),
    ("days_1_30", 1, 30),
    ("days_31_69", 31, 69),
    ("days_70_220", 70, 220),
    ("days_221_300", 221, 300),
]


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


def build_score_distribution_summaries(df, score_column, top_shares):
    distribution_rows = []
    threshold_rows = []

    if score_column not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    for timeframe, group in df.groupby("timeframe"):
        scores = group[score_column].dropna()

        if scores.empty:
            continue

        distribution_rows.append({
            "timeframe": timeframe,
            "count": int(len(scores)),
            "mean_score": round(float(scores.mean()), 6),
            "median_score": round(float(scores.median()), 6),
            "std_score": round(float(scores.std()), 6),
            "min_score": round(float(scores.min()), 6),
            "max_score": round(float(scores.max()), 6),
        })

        for top_share in top_shares:
            min_score = scores.quantile(1 - top_share)
            selected_count = int((scores >= min_score).sum())
            threshold_rows.append({
                "timeframe": timeframe,
                "top_share": top_share,
                "top_percent": int(top_share * 100),
                "min_score": round(float(min_score), 6),
                "selected_count": selected_count,
                "selected_share": round(float(selected_count / len(scores)), 6),
                "total_count": int(len(scores)),
            })

    return pd.DataFrame(distribution_rows), pd.DataFrame(threshold_rows)


def build_policy_stability_summary(selection_summary, policy_column, policy_label):
    if selection_summary.empty:
        return pd.DataFrame()

    rows = []

    for window_name, min_days, max_days in STABILITY_HORIZON_WINDOWS:
        window_data = selection_summary[
            selection_summary["horizon_days"].between(min_days, max_days)
        ]

        for (timeframe, policy_value), group in window_data.groupby(
            ["timeframe", policy_column]
        ):
            clean = group.dropna(subset=["annualized_excess_return"])
            correlation_clean = clean.dropna(subset=["pearson"])

            if clean.empty:
                continue

            rows.append({
                "timeframe": timeframe,
                "horizon_window": window_name,
                "min_horizon_days": min_days,
                "max_horizon_days": max_days,
                "policy_type": policy_label,
                "policy_value": policy_value,
                "horizons_count": int(len(clean)),
                "median_count": round(float(clean["count"].median()), 2),
                "min_count": int(clean["count"].min()),
                "mean_annualized_excess_return": round(
                    float(clean["annualized_excess_return"].mean()),
                    6,
                ),
                "median_annualized_excess_return": round(
                    float(clean["annualized_excess_return"].median()),
                    6,
                ),
                "positive_excess_share": round(
                    float((clean["annualized_excess_return"] > 0).mean()),
                    6,
                ),
                "median_pearson": (
                    None if correlation_clean.empty
                    else round(float(correlation_clean["pearson"].median()), 6)
                ),
                "positive_pearson_share": (
                    None if correlation_clean.empty
                    else round(float((correlation_clean["pearson"] > 0).mean()), 6)
                ),
            })

    return pd.DataFrame(rows)


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
