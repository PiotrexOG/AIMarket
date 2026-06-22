import numpy as np
import pandas as pd

from app.testy.score_tests.common.metrics import pearson_or_none, return_summary, round_or_none

from app.testy.score_tests.common.annualization import add_annualized_return_column

TOP_N_VALUES = [1, 2, 3, 5, 7, 9, 14, 18]


def calculate(context, top_n_values=TOP_N_VALUES):
    rows = []
    if context.return_panel.empty:
        return pd.DataFrame()

    for (timeframe, horizon_days), group in context.weekly_ranked.groupby(
        ["timeframe", "horizon_days"]
    ):
        all_weekly = group.groupby("start_timestamp", as_index=False).agg(
            future_return=("future_return", "mean"),
            selected_count=("ticker", "count"),
        )
        rows.append({
            "analysis_group": "A_weekly",
            "test": "A1_top_n",
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
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
                "horizon_days": int(horizon_days),
                "metric": "score",
                "bucket": f"Top {top_n}",
                "top_n": int(top_n),
                **return_summary(weekly),
            })

        for metric_column, metric_label in [
            ("score", "score"),
            ("score_percentile", "percentile"),
            ("score_zscore", "z_score"),
        ]:
            correlations = [
                pearson_or_none(week, metric_column)
                for _, week in group.groupby("start_timestamp")
            ]
            correlations = [value for value in correlations if value is not None]
            rows.append({
                "analysis_group": "A_weekly",
                "test": "A2_weekly_pearson",
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
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


def build_top_n_output(analysis):
    columns = [
        "timeframe",
        "horizon_days",
        "bucket",
        "top_n",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    required = set(columns) - {"annualized_return"}
    if analysis.empty or not {*required, "test"}.issubset(analysis.columns):
        return pd.DataFrame(columns=columns)
    selection = analysis[
        (analysis["test"] == "A1_top_n") & (analysis["bucket"] != "All 18")
    ]
    return (
        add_annualized_return_column(selection)[columns]
        .sort_values(["timeframe", "horizon_days", "top_n"])
        .reset_index(drop=True)
    )


def build_correlation_output(analysis):
    columns = [
        "timeframe",
        "horizon_days",
        "metric",
        "observation_count",
        "pearson",
    ]
    if analysis.empty:
        return pd.DataFrame(columns=columns)
    return (
        analysis[analysis["test"] == "A2_weekly_pearson"][columns]
        .sort_values(["timeframe", "horizon_days", "metric"])
        .reset_index(drop=True)
    )
