import numpy as np
import pandas as pd


def round_or_none(value, digits=6):
    if value is None or pd.isna(value):
        return None
    if np.isinf(value):
        return float(value)
    return round(float(value), digits)


def pearson_or_none(df, metric_column, return_column="future_return"):
    clean = df[[metric_column, return_column]].dropna()
    if (
        len(clean) < 3
        or clean[metric_column].nunique() < 2
        or clean[return_column].nunique() < 2
    ):
        return None
    return round_or_none(clean[metric_column].corr(clean[return_column]))


def spearman_or_none(df, metric_column, return_column="future_return"):
    clean = df[[metric_column, return_column]].dropna()
    if (
        len(clean) < 3
        or clean[metric_column].nunique() < 2
        or clean[return_column].nunique() < 2
    ):
        return None
    return round_or_none(
        clean[metric_column].corr(clean[return_column], method="spearman")
    )


def return_summary(df):
    returns = df["future_return"].dropna()
    if returns.empty:
        return {"observation_count": 0, "avg_return": None}
    return {
        "observation_count": int(len(returns)),
        "avg_return": round_or_none(returns.mean()),
    }


def average_score_range_summary(df):
    if df.empty:
        return {"avg_score_min": None, "avg_score_max": None}
    return {
        "avg_score_min": round_or_none(df["min_score"].mean()),
        "avg_score_max": round_or_none(df["max_score"].mean()),
    }
