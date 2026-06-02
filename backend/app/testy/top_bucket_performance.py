import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def calculate_correlations(group, score_column, return_column="future_return"):
    if score_column not in group.columns or return_column not in group.columns:
        return {
            "count": 0,
            "pearson": None,
            "pearson_p": None,
        }

    clean = group[[score_column, return_column]].dropna()

    if (
        len(clean) < 3
        or clean[score_column].nunique() < 2
        or clean[return_column].nunique() < 2
    ):
        return {
            "count": len(clean),
            "pearson": None,
            "pearson_p": None,
        }

    pearson_corr, pearson_p = pearsonr(clean[score_column], clean[return_column])

    return {
        "count": len(clean),
        "pearson": round(float(pearson_corr), 6),
        "pearson_p": round(float(pearson_p), 6),
    }


def calculate_return_stats(group):
    if "future_return" not in group.columns or group.empty:
        return {
            "avg_return": None,
            "median_return": None,
            "win_rate": None,
        }

    returns = group["future_return"].dropna()

    if returns.empty:
        return {
            "avg_return": None,
            "median_return": None,
            "win_rate": None,
        }

    return {
        "avg_return": round(float(returns.mean()), 6),
        "median_return": round(float(returns.median()), 6),
        "win_rate": round(float((returns > 0).mean()), 6),
    }


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

    timeframe_thresholds = build_timeframe_score_thresholds(
        df,
        score_column,
        top_shares,
    )

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
            min_score = timeframe_thresholds.get(timeframe, {}).get(top_share)

            if min_score is None:
                continue

            selected_count = int((scores >= min_score).sum())
            threshold_rows.append({
                "timeframe": timeframe,
                "top_share": top_share,
                "top_percent": int(top_share * 100),
                "threshold_scope": "timeframe",
                "min_score": round(float(min_score), 6),
                "selected_count": selected_count,
                "selected_share": round(float(selected_count / len(scores)), 6),
                "total_count": int(len(scores)),
            })

    return pd.DataFrame(distribution_rows), pd.DataFrame(threshold_rows)


def build_timeframe_score_thresholds(df, score_column, top_shares):
    if score_column not in df.columns:
        return {}

    thresholds = {}

    for timeframe, group in df.groupby("timeframe"):
        scores = group[score_column].dropna()

        if scores.empty:
            continue

        thresholds[timeframe] = {
            top_share: scores.quantile(1 - top_share)
            for top_share in top_shares
        }

    return thresholds
