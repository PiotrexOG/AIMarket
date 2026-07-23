import pandas as pd

from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.data import filter_horizon_week_ranges
from app.testy.score_tests.common.metrics import pearson_or_none, return_summary, round_or_none


TOP_SCORE_SHARES = [0.01, 0.02, 0.03, 0.05, 0.10, 0.20, 0.50, 0.75, 1]


def calculate(
    context,
    top_score_shares=TOP_SCORE_SHARES,
    horizon_start=None,
    horizon_end=None,
    horizon_week_ranges=None,
):
    if context.return_panel.empty:
        return pd.DataFrame()
    rows = []
    ranked_panel = filter_horizon_week_ranges(
        context.global_ranked,
        horizon_week_ranges=horizon_week_ranges,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    for (timeframe, horizon_weeks), ranked in ranked_panel.groupby(
        ["timeframe", "horizon_weeks"],
        sort=False,
    ):
        horizon_days = ranked["horizon_days"].mean()
        rows.append({
            "analysis_group": "B_global",
            "test": "B1_top_percent",
            "timeframe": timeframe,
            "horizon_weeks": int(horizon_weeks),
            "horizon_days": horizon_days,
            "metric": "score",
            "bucket": "All",
            "top_percent": 100,
            "min_score": None,
            **return_summary(ranked),
            "pearson": None,
        })
        scores = ranked["score"].dropna()
        for top_share in top_score_shares:
            min_score = (
                None if scores.empty else float(scores.quantile(1 - top_share))
            )
            selected = (
                pd.DataFrame()
                if min_score is None
                else ranked[ranked["score"] >= min_score]
            )
            rows.append({
                "analysis_group": "B_global",
                "test": "B1_top_percent",
                "timeframe": timeframe,
                "horizon_weeks": int(horizon_weeks),
                "horizon_days": horizon_days,
                "metric": "score",
                "bucket": f"Top {int(top_share * 100)}%",
                "top_percent": int(top_share * 100),
                "min_score": round_or_none(min_score),
                **return_summary(selected),
                "pearson": None,
            })

        metrics = ranked.copy()
        metrics["global_score_percentile"] = metrics["score"].rank(
            pct=True,
            method="average",
        )
        std = metrics["score"].std(ddof=0)
        metrics["global_score_zscore"] = (
            0.0
            if std == 0 or pd.isna(std)
            else (metrics["score"] - metrics["score"].mean()) / std
        )
        for metric_column, metric_label in [
            ("score", "score"),
            ("global_score_percentile", "percentile"),
            ("global_score_zscore", "z_score"),
        ]:
            rows.append({
                "analysis_group": "B_global",
                "test": "B2_global_pearson",
                "timeframe": timeframe,
                "horizon_weeks": int(horizon_weeks),
                "horizon_days": horizon_days,
                "metric": metric_label,
                "bucket": "All",
                "top_percent": None,
                "min_score": None,
                "observation_count": int(
                    len(metrics.dropna(subset=[metric_column, "future_return"]))
                ),
                "avg_return": None,
                "pearson": pearson_or_none(metrics, metric_column),
            })
    return pd.DataFrame(rows)


def build_top_percent_output(analysis):
    columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "bucket",
        "top_percent",
        "min_score",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    required = set(columns) - {"annualized_return"}
    if analysis.empty or not {*required, "test"}.issubset(analysis.columns):
        return pd.DataFrame(columns=columns)
    selection = analysis[
        (analysis["test"] == "B1_top_percent") & (analysis["bucket"] != "All")
    ]
    return (
        add_annualized_return_column(selection)[columns]
        .sort_values(["timeframe", "horizon_weeks", "top_percent"])
        .reset_index(drop=True)
    )


def build_correlation_output(analysis):
    columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "metric",
        "observation_count",
        "pearson",
    ]
    if analysis.empty:
        return pd.DataFrame(columns=columns)
    return (
        analysis[analysis["test"] == "B2_global_pearson"][columns]
        .sort_values(["timeframe", "horizon_weeks", "metric"])
        .reset_index(drop=True)
    )
