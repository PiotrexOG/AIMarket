import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.data import filter_horizon_week_ranges

from .config import (
    FORWARD_RETURN_HORIZON_POINT_COLUMNS,
    FORWARD_RETURN_POINT_COLUMNS,
)
from .history import _add_rank_percentile


def _build_forward_return_points(return_panel, horizon_week_ranges=None):
    required = {
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "future_return",
        "horizon_weeks",
        "horizon_days",
    }
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    panel = filter_horizon_week_ranges(
        return_panel,
        horizon_week_ranges=horizon_week_ranges,
    )
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    expected_horizon_counts = {}
    if horizon_week_ranges:
        expected_horizon_counts = {
            timeframe: end_week - start_week + 1
            for timeframe, (start_week, end_week) in horizon_week_ranges.items()
        }

    panel = add_annualized_return_column(
        panel,
        return_column="future_return",
        horizon_column="horizon_days",
    ).dropna(subset=["annualized_return"])
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    grouped = (
        panel.groupby(["timeframe", "ticker", "start_timestamp"], as_index=False)
        .agg(
            score=("score", "last"),
            score_percentile=("score_percentile", "last"),
            mean_forward_annualized_return=("annualized_return", "mean"),
            horizon_week_start=("horizon_weeks", "min"),
            horizon_week_end=("horizon_weeks", "max"),
            horizon_count=("horizon_weeks", "nunique"),
        )
        .rename(columns={"start_timestamp": "timestamp"})
    )
    if expected_horizon_counts:
        grouped["expected_horizon_count"] = grouped["timeframe"].map(
            expected_horizon_counts
        )
        grouped = grouped[
            grouped["horizon_count"] == grouped["expected_horizon_count"]
        ].copy()
        if grouped.empty:
            return pd.DataFrame(columns=FORWARD_RETURN_POINT_COLUMNS)

    grouped = _add_rank_percentile(
        grouped,
        value_column="score",
        output_column="score_percentile",
        group_columns=["timeframe", "timestamp"],
    )
    grouped["forward_return_rank"] = grouped.groupby(
        ["timeframe", "timestamp"]
    )["mean_forward_annualized_return"].rank(method="average", ascending=True)
    grouped["forward_return_count"] = grouped.groupby(
        ["timeframe", "timestamp"]
    )["mean_forward_annualized_return"].transform("count")
    grouped["forward_return_percentile"] = np.where(
        grouped["forward_return_count"] > 1,
        (grouped["forward_return_rank"] - 1)
        / (grouped["forward_return_count"] - 1),
        0.5,
    )
    grouped["cross_section_pearson_score_to_forward_percentile"] = (
        grouped.groupby(["timeframe", "timestamp"], group_keys=False)
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="pearson",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(grouped[["timeframe", "timestamp"]])
        )
        .to_numpy()
    )
    grouped["cross_section_spearman_score_to_forward_percentile"] = (
        grouped.groupby(["timeframe", "timestamp"], group_keys=False)
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="spearman",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(grouped[["timeframe", "timestamp"]])
        )
        .to_numpy()
    )

    return grouped[FORWARD_RETURN_POINT_COLUMNS]


def _build_forward_return_horizon_points(return_panel, horizon_week_ranges=None):
    required = {
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "future_return",
        "horizon_weeks",
        "horizon_days",
    }
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame(columns=FORWARD_RETURN_HORIZON_POINT_COLUMNS)

    panel = filter_horizon_week_ranges(
        return_panel,
        horizon_week_ranges=horizon_week_ranges,
    )
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_HORIZON_POINT_COLUMNS)

    panel = add_annualized_return_column(
        panel,
        return_column="future_return",
        horizon_column="horizon_days",
    ).dropna(subset=["annualized_return"])
    if panel.empty:
        return pd.DataFrame(columns=FORWARD_RETURN_HORIZON_POINT_COLUMNS)

    grouped = (
        panel.groupby(
            ["timeframe", "horizon_weeks", "ticker", "start_timestamp"],
            as_index=False,
        )
        .agg(
            score=("score", "last"),
            score_percentile=("score_percentile", "last"),
            forward_annualized_return=("annualized_return", "mean"),
            horizon_days=("horizon_days", "mean"),
        )
        .rename(columns={"start_timestamp": "timestamp"})
    )
    grouped = _add_rank_percentile(
        grouped,
        value_column="score",
        output_column="score_percentile",
        group_columns=["timeframe", "horizon_weeks", "timestamp"],
    )
    grouped["forward_return_rank"] = grouped.groupby(
        ["timeframe", "horizon_weeks", "timestamp"]
    )["forward_annualized_return"].rank(method="average", ascending=True)
    grouped["forward_return_count"] = grouped.groupby(
        ["timeframe", "horizon_weeks", "timestamp"]
    )["forward_annualized_return"].transform("count")
    grouped["forward_return_percentile"] = np.where(
        grouped["forward_return_count"] > 1,
        (grouped["forward_return_rank"] - 1)
        / (grouped["forward_return_count"] - 1),
        0.5,
    )
    grouped["cross_section_pearson_score_to_forward_percentile"] = (
        grouped.groupby(
            ["timeframe", "horizon_weeks", "timestamp"],
            group_keys=False,
        )
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="pearson",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(
                grouped[["timeframe", "horizon_weeks", "timestamp"]]
            )
        )
        .to_numpy()
    )
    grouped["cross_section_spearman_score_to_forward_percentile"] = (
        grouped.groupby(
            ["timeframe", "horizon_weeks", "timestamp"],
            group_keys=False,
        )
        .apply(
            lambda group: group["score_percentile"].corr(
                group["forward_return_percentile"],
                method="spearman",
            )
            if group["score_percentile"].nunique() > 1
            and group["forward_return_percentile"].nunique() > 1
            else np.nan
        )
        .reindex(
            pd.MultiIndex.from_frame(
                grouped[["timeframe", "horizon_weeks", "timestamp"]]
            )
        )
        .to_numpy()
    )

    return grouped[FORWARD_RETURN_HORIZON_POINT_COLUMNS]
