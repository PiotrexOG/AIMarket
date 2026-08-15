import numpy as np
import pandas as pd

from app.testy.score_tests.common.data import filter_horizon_week_ranges
from app.testy.score_tests.common.metrics import (
    pearson_or_none,
    return_summary,
    round_or_none,
    spearman_or_none,
)

from app.testy.score_tests.common.annualization import add_annualized_return_column

TOP_N_VALUES = [1, 2, 3, 5, 7, 9, 14, 18]


def calculate(
    context,
    top_n_values=TOP_N_VALUES,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
):
    rows = []
    if context.return_panel.empty:
        return pd.DataFrame()

    ranked = filter_horizon_week_ranges(
        context.weekly_ranked,
        horizon_week_ranges=horizon_week_ranges,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        align_to_common_horizon_window=True,
    )
    for (timeframe, horizon_weeks), group in ranked.groupby(
        ["timeframe", "horizon_weeks"]
    ):
        horizon_days = group["horizon_days"].mean()
        all_weekly = group.groupby("start_timestamp", as_index=False).agg(
            future_return=("future_return", "mean"),
            selected_count=("ticker", "count"),
        )
        rows.append({
            "analysis_group": "A_weekly",
            "test": "A1_top_n",
            "timeframe": timeframe,
            "horizon_weeks": int(horizon_weeks),
            "horizon_days": horizon_days,
            "metric": "score",
            "bucket": "All 18",
            "top_n": 18,
            **return_summary(all_weekly),
        })

        for top_n in top_n_values:
            selected = group.groupby(
                "start_timestamp",
                group_keys=False,
            ).head(top_n)
            weekly = selected.groupby("start_timestamp", as_index=False).agg(
                future_return=("future_return", "mean"),
                selected_count=("ticker", "count"),
            )
            rows.append({
                "analysis_group": "A_weekly",
                "test": "A1_top_n",
                "timeframe": timeframe,
                "horizon_weeks": int(horizon_weeks),
                "horizon_days": horizon_days,
                "metric": "score",
                "bucket": f"Top {top_n}",
                "top_n": int(top_n),
                **return_summary(weekly),
            })

        for metric_label, correlation_function, metric_column in [
            ("Pearson IC", pearson_or_none, "score"),
            ("Spearman IC", spearman_or_none, "score"),
            ("Score Percentile Pearson IC", pearson_or_none, "score_percentile"),
        ]:
            correlations = [
                correlation_function(week, metric_column)
                for _, week in group.groupby("start_timestamp")
            ]
            correlations = [value for value in correlations if value is not None]
            rows.append({
                "analysis_group": "A_weekly",
                "test": "A2_weekly_pearson",
                "timeframe": timeframe,
                "horizon_weeks": int(horizon_weeks),
                "horizon_days": horizon_days,
                "metric": metric_label,
                "bucket": "weekly_mean",
                "top_n": None,
                "observation_count": len(correlations),
                "avg_return": None,
                "pearson": (
                    None
                    if not correlations
                    else round_or_none(np.mean(correlations))
                ),
            })
    return pd.DataFrame(rows)
