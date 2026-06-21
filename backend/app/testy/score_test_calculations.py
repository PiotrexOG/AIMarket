import numpy as np
import pandas as pd

from market_return_lookup import (
    add_current_prices,
    build_horizon_return_frame,
    load_market_lookup_for_analysis,
)


TOP_N_VALUES = [1, 2, 3, 5, 7, 9, 14, 18]
TOP_SCORE_SHARES = [0.01, 0.02, 0.03, 0.05, 0.10, 0.20, 0.50, 0.75, 1]
FRACTIONAL_TOP_SHARE_START = 1 / 18
FRACTIONAL_TOP_SHARE_END = 1
FRACTIONAL_TOP_SHARE_STEP = 0.01
RELATIVE_SORTINO_HORIZON_START = 100
RELATIVE_SORTINO_HORIZON_END = 300
RELATIVE_SORTINO_ANNUALIZATION_DAYS = 252
RELATIVE_SORTINO_PLATEAU_TOLERANCE = 0.05

punkty = np.linspace(0, 100, 19)


GLOBAL_SCORE_BUCKETS = [
    (punkty[i], punkty[i+1])
    for i in range(len(punkty)-1)
]
PRICE_WINDOW_SHARE_OF_HORIZON = 0.42


def build_fractional_top_shares(
    start=FRACTIONAL_TOP_SHARE_START,
    end=FRACTIONAL_TOP_SHARE_END,
    step=FRACTIONAL_TOP_SHARE_STEP,
):
    shares = []
    value = start

    while value <= end + 1e-12:
        shares.append(float(value))
        value += step

    if shares and not np.isclose(shares[-1], end):
        shares.append(float(end))

    return shares


FRACTIONAL_TOP_SHARES = build_fractional_top_shares()


def _round_or_none(value, digits=6):
    if value is None or pd.isna(value):
        return None

    if np.isinf(value):
        return float(value)

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


def _build_global_relative_sortino_observation_frame(
    return_panel,
    top_shares,
    horizon_start,
    horizon_end,
    annualization_days,
):
    if return_panel.empty:
        return pd.DataFrame()

    ranked = (
        return_panel[
            return_panel["horizon_days"].between(horizon_start, horizon_end)
        ]
        .dropna(subset=["score", "future_return"])
        .sort_values(
            ["timeframe", "horizon_days", "start_timestamp", "score", "ticker"],
            ascending=[True, True, True, False, True],
        )
    )

    if ranked.empty:
        return pd.DataFrame()

    observation_frames = []

    for (timeframe, horizon_days), horizon_group in ranked.groupby(
        ["timeframe", "horizon_days"]
    ):
        start_codes, start_timestamps = pd.factorize(
            horizon_group["start_timestamp"],
            sort=False,
        )
        rank_positions = (
            horizon_group.groupby("start_timestamp").cumcount().to_numpy() + 1
        )
        available_counts = np.bincount(start_codes)
        max_available_count = int(available_counts.max())
        returns_by_rank = np.full(
            (len(available_counts), max_available_count),
            np.nan,
            dtype=float,
        )
        returns_by_rank[start_codes, rank_positions - 1] = (
            horizon_group["future_return"].to_numpy(dtype=float)
        )
        benchmark_returns = np.nanmean(returns_by_rank, axis=1)
        rank_numbers = np.arange(
            1,
            max_available_count + 1,
            dtype=float,
        )[None, :]
        available_counts_column = available_counts[:, None].astype(float)

        for top_share in top_shares:
            target_counts = available_counts_column * float(top_share)
            full_counts = np.floor(target_counts)
            fractional_counts = target_counts - full_counts
            weights = np.where(
                rank_numbers <= full_counts,
                1.0,
                np.where(
                    rank_numbers == full_counts + 1,
                    fractional_counts,
                    0.0,
                ),
            )
            weights = np.where(np.isnan(returns_by_rank), 0.0, weights)
            effective_selected_counts = weights.sum(axis=1)
            valid_selection = effective_selected_counts > 0
            weighted_returns = np.nansum(weights * returns_by_rank, axis=1)
            strategy_returns = np.full(len(available_counts), np.nan, dtype=float)
            strategy_returns[valid_selection] = (
                weighted_returns[valid_selection]
                / effective_selected_counts[valid_selection]
            )
            valid_returns = (
                np.isfinite(strategy_returns)
                & np.isfinite(benchmark_returns)
                & (strategy_returns > -1)
                & (benchmark_returns > -1)
            )

            if not valid_returns.any():
                continue

            strategy_annualized = (
                (1 + strategy_returns[valid_returns])
                ** (annualization_days / horizon_days)
                - 1
            )
            benchmark_annualized = (
                (1 + benchmark_returns[valid_returns])
                ** (annualization_days / horizon_days)
                - 1
            )
            annualized_alpha = strategy_annualized - benchmark_annualized
            observation_frames.append(pd.DataFrame({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "start_timestamp": pd.to_datetime(
                    np.asarray(start_timestamps)[valid_returns]
                ),
                "top_share": float(top_share),
                "top_percent": _round_or_none(top_share * 100),
                "available_count": available_counts[valid_returns].astype(int),
                "effective_selected_count": (
                    effective_selected_counts[valid_returns]
                ),
                "strategy_return": strategy_returns[valid_returns],
                "strategy_annualized": strategy_annualized,
                "benchmark_return": benchmark_returns[valid_returns],
                "benchmark_annualized": benchmark_annualized,
                "annualized_alpha": annualized_alpha,
                "is_downside": annualized_alpha < 0,
                "downside_alpha": np.minimum(0.0, annualized_alpha),
            }))

    if not observation_frames:
        return pd.DataFrame()

    return pd.concat(observation_frames, ignore_index=True)


def _summarize_relative_sortino_group(group):
    annualized_alpha = group["annualized_alpha"].to_numpy(dtype=float)
    downside_alpha = np.minimum(0.0, annualized_alpha)
    mean_alpha = float(annualized_alpha.mean())
    downside_deviation = float(np.sqrt(np.mean(np.square(downside_alpha))))

    if downside_deviation == 0:
        relative_sortino = (
            0.0
            if mean_alpha == 0
            else np.inf * np.sign(mean_alpha)
        )
    else:
        relative_sortino = mean_alpha / downside_deviation

    return {
        "observation_count": int(len(group)),
        "downside_count": int((annualized_alpha < 0).sum()),
        "downside_frequency": float((annualized_alpha < 0).mean()),
        "mean_strategy_return": float(group["strategy_return"].mean()),
        "mean_annualized_strategy_return": float(
            group["strategy_annualized"].mean()
        ),
        "mean_benchmark_return": float(group["benchmark_return"].mean()),
        "mean_annualized_benchmark_return": float(
            group["benchmark_annualized"].mean()
        ),
        "mean_annualized_alpha": mean_alpha,
        "relative_downside_deviation": downside_deviation,
        "relative_sortino": relative_sortino,
    }


def _build_global_relative_sortino_by_horizon_frame(
    return_panel,
    top_shares=FRACTIONAL_TOP_SHARES,
    horizon_start=RELATIVE_SORTINO_HORIZON_START,
    horizon_end=RELATIVE_SORTINO_HORIZON_END,
    annualization_days=RELATIVE_SORTINO_ANNUALIZATION_DAYS,
):
    output_columns = [
        "timeframe",
        "horizon_days",
        "annualization_days",
        "top_share",
        "top_percent",
        "observation_count",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "relative_downside_deviation",
        "relative_sortino",
    ]
    observations = _build_global_relative_sortino_observation_frame(
        return_panel,
        top_shares=top_shares,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        annualization_days=annualization_days,
    )

    if observations.empty:
        return pd.DataFrame(columns=output_columns)

    rows = []
    for (timeframe, horizon_days, top_share), group in observations.groupby(
        ["timeframe", "horizon_days", "top_share"],
        sort=False,
    ):
        summary = _summarize_relative_sortino_group(group)
        rows.append({
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
            "annualization_days": int(annualization_days),
            "top_share": float(top_share),
            "top_percent": float(top_share * 100),
            **summary,
        })

    return (
        pd.DataFrame(rows, columns=output_columns)
        .sort_values(["timeframe", "top_share", "horizon_days"])
        .reset_index(drop=True)
    )


def build_global_relative_sortino_by_horizon(
    return_panel,
    top_shares=FRACTIONAL_TOP_SHARES,
    horizon_start=RELATIVE_SORTINO_HORIZON_START,
    horizon_end=RELATIVE_SORTINO_HORIZON_END,
    annualization_days=RELATIVE_SORTINO_ANNUALIZATION_DAYS,
):
    result = _build_global_relative_sortino_by_horizon_frame(
        return_panel,
        top_shares=top_shares,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        annualization_days=annualization_days,
    )

    if result.empty:
        return result

    rounded = result.copy()
    for column in rounded.columns:
        if column not in {
            "timeframe",
            "horizon_days",
            "annualization_days",
            "observation_count",
            "downside_count",
        }:
            rounded[column] = rounded[column].round(6)
    return rounded


def build_global_relative_sortino_analysis(
    return_panel,
    top_shares=FRACTIONAL_TOP_SHARES,
    horizon_start=RELATIVE_SORTINO_HORIZON_START,
    horizon_end=RELATIVE_SORTINO_HORIZON_END,
    annualization_days=RELATIVE_SORTINO_ANNUALIZATION_DAYS,
    plateau_tolerance=RELATIVE_SORTINO_PLATEAU_TOLERANCE,
):
    output_columns = [
        "timeframe",
        "horizon_start",
        "horizon_end",
        "horizon_count",
        "annualization_days",
        "aggregation_method",
        "top_share",
        "top_percent",
        "observation_count",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "relative_downside_deviation",
        "relative_sortino",
        "neighbor_mean_sortino",
        "is_max_sortino",
        "is_stability_plateau",
        "is_stable_recommendation",
    ]

    by_horizon = _build_global_relative_sortino_by_horizon_frame(
        return_panel,
        top_shares=top_shares,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        annualization_days=annualization_days,
    )

    if by_horizon.empty:
        return pd.DataFrame(columns=output_columns)

    rows = []

    for (timeframe, top_share), group in by_horizon.groupby(
        ["timeframe", "top_share"],
        sort=False,
    ):
        rows.append({
            "timeframe": timeframe,
            "horizon_start": int(horizon_start),
            "horizon_end": int(horizon_end),
            "horizon_count": int(group["horizon_days"].nunique()),
            "annualization_days": int(annualization_days),
            "aggregation_method": "equal_weight_mean_across_horizons",
            "top_share": float(top_share),
            "top_percent": _round_or_none(top_share * 100),
            "observation_count": int(group["observation_count"].sum()),
            "downside_count": int(group["downside_count"].sum()),
            "downside_frequency": _round_or_none(
                group["downside_frequency"].mean()
            ),
            "mean_strategy_return": _round_or_none(
                group["mean_strategy_return"].mean()
            ),
            "mean_annualized_strategy_return": _round_or_none(
                group["mean_annualized_strategy_return"].mean()
            ),
            "mean_benchmark_return": _round_or_none(
                group["mean_benchmark_return"].mean()
            ),
            "mean_annualized_benchmark_return": _round_or_none(
                group["mean_annualized_benchmark_return"].mean()
            ),
            "mean_annualized_alpha": _round_or_none(
                group["mean_annualized_alpha"].mean()
            ),
            "relative_downside_deviation": _round_or_none(
                group["relative_downside_deviation"].mean()
            ),
            "relative_sortino": _round_or_none(
                group["relative_sortino"].mean()
            ),
        })

    result = pd.DataFrame(rows).sort_values(
        ["timeframe", "top_share"]
    ).reset_index(drop=True)
    result["neighbor_mean_sortino"] = np.nan
    result["is_max_sortino"] = False
    result["is_stability_plateau"] = False
    result["is_stable_recommendation"] = False

    for _, timeframe_group in result.groupby("timeframe", sort=False):
        finite_group = timeframe_group[
            np.isfinite(timeframe_group["relative_sortino"])
        ].copy()

        if finite_group.empty:
            continue

        neighbor_mean = finite_group["relative_sortino"].rolling(
            window=3,
            center=True,
            min_periods=2,
        ).mean()
        result.loc[finite_group.index, "neighbor_mean_sortino"] = (
            neighbor_mean.round(6)
        )
        max_index = finite_group["relative_sortino"].idxmax()
        max_sortino = float(finite_group.loc[max_index, "relative_sortino"])
        plateau_margin = plateau_tolerance * max(abs(max_sortino), 1e-12)
        plateau_mask = (
            finite_group["relative_sortino"]
            >= max_sortino - plateau_margin
        )
        plateau_indexes = finite_group.index[plateau_mask]

        result.loc[max_index, "is_max_sortino"] = True
        result.loc[plateau_indexes, "is_stability_plateau"] = True

        recommendation_candidates = result.loc[plateau_indexes].dropna(
            subset=["neighbor_mean_sortino"]
        )
        if recommendation_candidates.empty:
            recommendation_index = max_index
        else:
            recommendation_index = recommendation_candidates[
                "neighbor_mean_sortino"
            ].idxmax()
        result.loc[recommendation_index, "is_stable_recommendation"] = True

    return result[output_columns]


def build_global_relative_sortino_observations(
    return_panel,
    top_shares=(FRACTIONAL_TOP_SHARES[0], 1.0),
    horizon_start=RELATIVE_SORTINO_HORIZON_START,
    horizon_end=RELATIVE_SORTINO_HORIZON_END,
    annualization_days=RELATIVE_SORTINO_ANNUALIZATION_DAYS,
):
    output_columns = [
        "timeframe",
        "top_share",
        "top_percent",
        "observation_id",
        "start_timestamp",
        "horizon_days",
        "available_count",
        "effective_selected_count",
        "strategy_return",
        "annualized_strategy_return",
        "benchmark_return",
        "annualized_benchmark_return",
        "annualized_alpha",
        "is_downside",
        "downside_alpha",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "relative_downside_deviation",
    ]
    observations = _build_global_relative_sortino_observation_frame(
        return_panel,
        top_shares=top_shares,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        annualization_days=annualization_days,
    )

    if observations.empty:
        return pd.DataFrame(columns=output_columns)

    summary_columns = [
        "timeframe",
        "top_share",
        "downside_count",
        "downside_frequency",
        "mean_strategy_return",
        "mean_annualized_strategy_return",
        "mean_benchmark_return",
        "mean_annualized_benchmark_return",
        "mean_annualized_alpha",
        "relative_downside_deviation",
    ]
    summary = build_global_relative_sortino_analysis(
        return_panel,
        top_shares=top_shares,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        annualization_days=annualization_days,
    )[summary_columns]
    result = observations.rename(columns={
        "strategy_annualized": "annualized_strategy_return",
        "benchmark_annualized": "annualized_benchmark_return",
    }).merge(
        summary,
        on=["timeframe", "top_share"],
        how="left",
        validate="many_to_one",
    )
    result = result.sort_values(
        ["timeframe", "top_share", "horizon_days", "start_timestamp"]
    ).reset_index(drop=True)
    result["observation_id"] = (
        result.groupby(["timeframe", "top_share"]).cumcount() + 1
    )

    for column in [
        "effective_selected_count",
        "strategy_return",
        "annualized_strategy_return",
        "benchmark_return",
        "annualized_benchmark_return",
        "annualized_alpha",
        "downside_alpha",
    ]:
        result[column] = result[column].round(6)

    return result[output_columns]


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
