import numpy as np
import pandas as pd

from market_return_lookup import (
    add_current_prices,
    build_horizon_return_frame,
    load_market_lookup_for_analysis,
)


TOP_N_VALUES = [1, 2, 3, 5, 7, 9, 14, 18]
TOP_SCORE_SHARES = [0.01, 0.02, 0.03, 0.05, 0.10, 0.20, 0.50, 0.75, 1]

punkty = np.linspace(0, 100, 19)


GLOBAL_SCORE_BUCKETS = [
    (punkty[i], punkty[i+1])
    for i in range(len(punkty)-1)
]
PRICE_WINDOW_SHARE_OF_HORIZON = 0.42


def _round_or_none(value, digits=6):
    if value is None or pd.isna(value):
        return None

    return round(float(value), digits)


def _pearson_or_none(df, metric_column, return_column="future_return"):
    clean = df[[metric_column, return_column]].dropna()

    if (
        len(clean) < 3
        or clean[metric_column].nunique() < 2
        or clean[return_column].nunique() < 2
    ):
        return None

    return _round_or_none(clean[metric_column].corr(clean[return_column], method="pearson"))


def _return_summary(df):
    returns = df["future_return"].dropna()

    if returns.empty:
        return {
            "observation_count": 0,
            "avg_return": None,
        }

    return {
        "observation_count": int(len(returns)),
        "avg_return": _round_or_none(returns.mean()),
    }


def _average_score_range_summary(df):
    if df.empty:
        return {
            "avg_score_min": None,
            "avg_score_max": None,
        }

    return {
        "avg_score_min": _round_or_none(df["min_score"].mean()),
        "avg_score_max": _round_or_none(df["max_score"].mean()),
    }


def build_horizon_days(df):
    if df.empty:
        return []

    first_score_date = pd.to_datetime(df["start_timestamp"].min()).normalize()
    last_score_date = pd.to_datetime(df["start_timestamp"].max()).normalize()
    max_horizon_days = int((last_score_date - first_score_date).days)

    if max_horizon_days < 1:
        return []

    return list(range(1, max_horizon_days + 1))


def build_timeframe_score_observations(df, score_column):
    """
    Keep separate score series for short, medium and long term. Each row is one
    weekly cross-section observation for one ticker and one scoring timeframe.
    """
    required_columns = {"timeframe", "ticker", "start_timestamp", score_column}

    if df.empty or not required_columns.issubset(df.columns):
        return pd.DataFrame()

    result = (
        df.dropna(subset=["timeframe", "ticker", "start_timestamp", score_column])
        .groupby(["timeframe", "start_timestamp", "ticker"], as_index=False)
        .agg(score=(score_column, "mean"))
    )
    result["score"] = pd.to_numeric(result["score"], errors="coerce")
    return result.dropna(subset=["score"])


def add_weekly_score_metrics(df):
    if df.empty:
        return df

    result = df.copy()

    def add_group_metrics(group):
        group = group.copy()
        group["score_percentile"] = group["score"].rank(pct=True, method="average")
        std = group["score"].std(ddof=0)
        group["score_zscore"] = 0.0 if std == 0 or pd.isna(std) else (
            group["score"] - group["score"].mean()
        ) / std
        return group

    return (
        result.groupby(["timeframe", "start_timestamp"], group_keys=False)
        .apply(add_group_metrics)
        .reset_index(drop=True)
    )


def build_return_panel(
    df,
    horizon_days_values,
):
    if df.empty:
        return pd.DataFrame()

    score_end_time = pd.to_datetime(df["start_timestamp"].max())
    market_lookup = load_market_lookup_for_analysis(
        df,
        max_timestamp=score_end_time,
    )

    if not market_lookup:
        return pd.DataFrame()

    priced_df = add_current_prices(df, market_lookup)
    rows = []

    for timeframe, timeframe_group in priced_df.groupby("timeframe"):
        for horizon_days in horizon_days_values:
            window_positions = max(
                1,
                int(horizon_days * PRICE_WINDOW_SHARE_OF_HORIZON),
            )
            horizon_df = build_horizon_return_frame(
                timeframe_group,
                market_lookup=market_lookup,
                score_column="score",
                horizon_days=horizon_days,
                window_positions=window_positions,
            )

            if horizon_df.empty:
                continue

            horizon_df = horizon_df[horizon_df["future_timestamp"] <= score_end_time]

            if horizon_df.empty:
                continue

            horizon_df["timeframe"] = timeframe
            horizon_df["horizon_days"] = horizon_days
            horizon_df["window_positions"] = window_positions
            rows.append(horizon_df)

    if not rows:
        return pd.DataFrame()

    panel = pd.concat(rows, ignore_index=True)
    metric_columns = ["score_percentile", "score_zscore"]
    panel = panel.merge(
        df[["timeframe", "ticker", "start_timestamp", *metric_columns]],
        on=["timeframe", "ticker", "start_timestamp"],
        how="left",
    )
    return panel


def build_weekly_analysis(return_panel, top_n_values=TOP_N_VALUES):
    rows = []

    if return_panel.empty:
        return pd.DataFrame()

    ranked = return_panel.sort_values(
        ["timeframe", "horizon_days", "start_timestamp", "score", "ticker"],
        ascending=[True, True, True, False, True],
    )

    for (timeframe, horizon_days), horizon_group in ranked.groupby(["timeframe", "horizon_days"]):
        all_weekly = (
            horizon_group.groupby("start_timestamp", as_index=False)
            .agg(future_return=("future_return", "mean"), selected_count=("ticker", "count"))
        )
        rows.append({
            "analysis_group": "A_weekly",
            "test": "A1_top_n",
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
            "metric": "score",
            "bucket": "All 18",
            "top_n": 18,
            **_return_summary(all_weekly),
        })

        for top_n in top_n_values:
            selected = horizon_group.groupby("start_timestamp", group_keys=False).head(top_n)
            weekly_selected = (
                selected.groupby("start_timestamp", as_index=False)
                .agg(future_return=("future_return", "mean"), selected_count=("ticker", "count"))
            )
            rows.append({
                "analysis_group": "A_weekly",
                "test": "A1_top_n",
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "metric": "score",
                "bucket": f"Top {top_n}",
                "top_n": int(top_n),
                **_return_summary(weekly_selected),
            })

        for metric_column, metric_label in [
            ("score", "score"),
            ("score_percentile", "percentile"),
            ("score_zscore", "z_score"),
        ]:
            weekly_correlations = []

            for _, week_group in horizon_group.groupby("start_timestamp"):
                weekly_correlations.append(_pearson_or_none(week_group, metric_column))

            clean_correlations = [
                value for value in weekly_correlations if value is not None
            ]
            rows.append({
                "analysis_group": "A_weekly",
                "test": "A2_weekly_pearson",
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "metric": metric_label,
                "bucket": "weekly_mean",
                "top_n": None,
                "observation_count": int(len(clean_correlations)),
                "avg_return": None,
                "pearson": (
                    None
                    if not clean_correlations
                    else _round_or_none(np.mean(clean_correlations))
                ),
            })

    return pd.DataFrame(rows)


def build_weekly_bucket_analysis(return_panel, bucket_size=1):
    rows = []

    if return_panel.empty:
        return pd.DataFrame()

    ranked = return_panel.sort_values(
        ["timeframe", "horizon_days", "start_timestamp", "score", "ticker"],
        ascending=[True, True, True, False, True],
    ).copy()
    ranked["rank_position"] = (
        ranked.groupby(["timeframe", "horizon_days", "start_timestamp"])
        .cumcount()
        + 1
    )
    ranked["bucket_start_rank"] = (
        ((ranked["rank_position"] - 1) // bucket_size) * bucket_size + 1
    )
    ranked["bucket_end_rank"] = ranked["bucket_start_rank"] + bucket_size - 1
    ranked["bucket"] = (
        "Rank "
        + ranked["bucket_start_rank"].astype(str)
        + "-"
        + ranked["bucket_end_rank"].astype(str)
    )

    group_columns = [
        "timeframe",
        "horizon_days",
        "bucket_start_rank",
        "bucket_end_rank",
        "bucket",
    ]

    for group_key, bucket_group in ranked.groupby(group_columns, sort=False):
        (
            timeframe,
            horizon_days,
            bucket_start_rank,
            bucket_end_rank,
            bucket,
        ) = group_key
        weekly_bucket = (
            bucket_group.groupby("start_timestamp", as_index=False)
            .agg(
                future_return=("future_return", "mean"),
                selected_count=("ticker", "count"),
                min_score=("score", "min"),
                max_score=("score", "max"),
            )
        )
        rows.append({
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
            "bucket": bucket,
            "bucket_start_rank": int(bucket_start_rank),
            "bucket_end_rank": int(bucket_end_rank),
            **_average_score_range_summary(weekly_bucket),
            **_return_summary(weekly_bucket),
        })

    return pd.DataFrame(rows)


def build_global_score_bucket_analysis(
    return_panel,
    score_buckets=GLOBAL_SCORE_BUCKETS,
):
    rows = []

    if return_panel.empty:
        return pd.DataFrame()

    for (timeframe, horizon_days), horizon_group in return_panel.groupby(["timeframe", "horizon_days"]):
        ranked = horizon_group.dropna(subset=["score"]).sort_values(
            ["score", "start_timestamp", "ticker"],
            ascending=[False, True, True],
        )
        scores = ranked["score"].dropna()

        for bucket_start, bucket_end in score_buckets:
            if scores.empty:
                selected = pd.DataFrame()
                min_score = None
                max_score = None
            else:
                min_score = float(scores.quantile(1 - bucket_end / 100))
                max_score = float(scores.quantile(1 - bucket_start / 100))
                selected = ranked[
                    (ranked["score"] >= min_score)
                    & (ranked["score"] <= max_score)
                ]

                if bucket_start > 0:
                    selected = selected[selected["score"] < max_score]

            rows.append({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "bucket": f"Top {bucket_start}-{bucket_end}%",
                "bucket_start_percent": int(bucket_start),
                "bucket_end_percent": int(bucket_end),
                "min_score": _round_or_none(min_score),
                "max_score": _round_or_none(max_score),
                **_return_summary(selected),
            })

    return pd.DataFrame(rows)


def build_global_analysis(
    return_panel,
    top_score_shares=TOP_SCORE_SHARES,
):
    rows = []

    if return_panel.empty:
        return pd.DataFrame()

    for (timeframe, horizon_days), horizon_group in return_panel.groupby(["timeframe", "horizon_days"]):
        rows.append({
            "analysis_group": "B_global",
            "test": "B1_top_percent",
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
            "metric": "score",
            "bucket": "All",
            "top_percent": 100,
            "min_score": None,
            **_return_summary(horizon_group),
            "pearson": None,
        })

        ranked = horizon_group.dropna(subset=["score"]).sort_values(
            ["score", "start_timestamp", "ticker"],
            ascending=[False, True, True],
        )
        scores = ranked["score"].dropna()

        for top_share in top_score_shares:
            min_score = (
                None
                if scores.empty
                else float(scores.quantile(1 - top_share))
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
                "horizon_days": int(horizon_days),
                "metric": "score",
                "bucket": f"Top {int(top_share * 100)}%",
                "top_percent": int(top_share * 100),
                "min_score": _round_or_none(min_score),
                **_return_summary(selected),
                "pearson": None,
            })

        global_metric_group = horizon_group.copy()
        global_metric_group["global_score_percentile"] = (
            global_metric_group["score"].rank(pct=True, method="average")
        )
        global_score_std = global_metric_group["score"].std(ddof=0)
        global_metric_group["global_score_zscore"] = (
            0.0
            if global_score_std == 0 or pd.isna(global_score_std)
            else (
                global_metric_group["score"] - global_metric_group["score"].mean()
            ) / global_score_std
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
                "horizon_days": int(horizon_days),
                "metric": metric_label,
                "bucket": "All",
                "top_percent": None,
                "min_score": None,
                "observation_count": int(len(global_metric_group.dropna(subset=[metric_column, "future_return"]))),
                "avg_return": None,
                "pearson": _pearson_or_none(global_metric_group, metric_column),
            })

    return pd.DataFrame(rows)
