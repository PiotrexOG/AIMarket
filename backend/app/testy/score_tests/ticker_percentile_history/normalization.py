import numpy as np
import pandas as pd


def _format_metric_value(value, metric_format):
    if pd.isna(value):
        return ""
    if np.isclose(value, 0, atol=0.005):
        value = 0.0
    if metric_format == "percent":
        return f"{value:.0%}"
    if metric_format == "signed_percent":
        return f"{value:+.0%}"
    if metric_format == "plain":
        return f"{value:.2f}"
    return f"{value:+.2f}"


def _normalized_excess_by_timestamp(data, weight_column, attribution_column):
    rows = {}
    for timestamp, group in data.groupby("timestamp", sort=True):
        denominator = group[weight_column].abs().sum()
        if pd.isna(denominator) or np.isclose(denominator, 0):
            rows[timestamp] = np.nan
            continue
        rows[timestamp] = group[attribution_column].sum() / denominator
    return pd.Series(rows, dtype=float)


def _zscore_by_group(data, group_column, value_column, output_column):
    result = data.copy()
    mean = result.groupby(group_column)[value_column].transform("mean")
    std = result.groupby(group_column)[value_column].transform(
        lambda values: values.std(ddof=0)
    )
    result[output_column] = (
        (result[value_column] - mean) / std.replace(0, np.nan)
    )
    return result


def _rank_percentile_by_group(data, group_column, value_column, output_column):
    result = data.copy()
    ranks = result.groupby(group_column)[value_column].rank(
        method="average",
        ascending=True,
    )
    counts = result.groupby(group_column)[value_column].transform("count")
    result[output_column] = np.where(
        counts > 1,
        (ranks - 1) / (counts - 1),
        0.5,
    )
    return result
