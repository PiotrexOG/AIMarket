import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import add_annualized_return_column
from app.testy.score_tests.common.metrics import return_summary, round_or_none


BOUNDARIES = np.linspace(0, 100, 19)
DEFAULT_BUCKETS = [
    (BOUNDARIES[index], BOUNDARIES[index + 1])
    for index in range(len(BOUNDARIES) - 1)
]


def calculate(context, score_buckets=DEFAULT_BUCKETS):
    if context.return_panel.empty:
        return pd.DataFrame()
    rows = []
    for (timeframe, horizon_days), ranked in context.global_ranked.groupby(
        ["timeframe", "horizon_days"],
        sort=False,
    ):
        ranked = ranked.dropna(subset=["score"])
        scores = ranked["score"]
        for bucket_start, bucket_end in score_buckets:
            if scores.empty:
                selected = pd.DataFrame()
                min_score = max_score = None
            else:
                min_score = float(scores.quantile(1 - bucket_end / 100))
                max_score = float(scores.quantile(1 - bucket_start / 100))
                selected = ranked[
                    ranked["score"].between(min_score, max_score)
                ]
                if bucket_start > 0:
                    selected = selected[selected["score"] < max_score]
            rows.append({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "bucket": f"Top {bucket_start}-{bucket_end}%",
                "bucket_start_percent": int(bucket_start),
                "bucket_end_percent": int(bucket_end),
                "min_score": round_or_none(min_score),
                "max_score": round_or_none(max_score),
                **return_summary(selected),
            })
    return pd.DataFrame(rows)


def build_output(analysis):
    columns = [
        "timeframe",
        "horizon_days",
        "bucket",
        "bucket_start_percent",
        "bucket_end_percent",
        "min_score",
        "max_score",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    if analysis.empty:
        return pd.DataFrame(columns=columns)
    return (
        add_annualized_return_column(analysis)[columns]
        .sort_values(["timeframe", "horizon_days", "bucket_start_percent"])
        .reset_index(drop=True)
    )
