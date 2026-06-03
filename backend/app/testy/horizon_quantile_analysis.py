import pandas as pd

from market_price_lookup import (
    add_current_prices,
    build_horizon_return_frame,
    load_market_lookup_for_analysis,
)
from top_bucket_performance import (
    calculate_correlations,
    calculate_return_stats,
)


def calculate_daily_score_return_correlations(group, score_column):
    clean = group[[score_column, "future_return"]].dropna()

    if (
        len(clean) < 3
        or clean[score_column].nunique() < 2
        or clean["future_return"].nunique() < 2
    ):
        return {
            "observation_count": int(len(clean)),
            "pearson_ic": None,
            "spearman_ic": None,
        }

    return {
        "observation_count": int(len(clean)),
        "pearson_ic": round(
            float(clean[score_column].corr(clean["future_return"], method="pearson")),
            6,
        ),
        "spearman_ic": round(
            float(clean[score_column].corr(clean["future_return"], method="spearman")),
            6,
        ),
    }


def summarize_daily_ic(daily_ic_df):
    if daily_ic_df.empty:
        return {
            "days_count": 0,
            "avg_observation_count": None,
            "mean_pearson_ic": None,
            "median_pearson_ic": None,
            "positive_pearson_ic_share": None,
            "mean_spearman_ic": None,
            "median_spearman_ic": None,
            "positive_spearman_ic_share": None,
        }

    pearson = daily_ic_df["pearson_ic"].dropna()
    spearman = daily_ic_df["spearman_ic"].dropna()

    return {
        "days_count": int(len(daily_ic_df)),
        "avg_observation_count": round(
            float(daily_ic_df["observation_count"].mean()),
            6,
        ),
        "mean_pearson_ic": (
            None
            if pearson.empty
            else round(float(pearson.mean()), 6)
        ),
        "median_pearson_ic": (
            None
            if pearson.empty
            else round(float(pearson.median()), 6)
        ),
        "positive_pearson_ic_share": (
            None
            if pearson.empty
            else round(float((pearson > 0).mean()), 6)
        ),
        "mean_spearman_ic": (
            None
            if spearman.empty
            else round(float(spearman.mean()), 6)
        ),
        "median_spearman_ic": (
            None
            if spearman.empty
            else round(float(spearman.median()), 6)
        ),
        "positive_spearman_ic_share": (
            None
            if spearman.empty
            else round(float((spearman > 0).mean()), 6)
        ),
    }


def calculate_horizon_quantile_summaries(
    df,
    score_column,
    horizon_day_range_map,
    smoothing_window_map,
    top_score_shares,
    market_data_buffer_days,
    timeframe_score_thresholds=None,
):
    if score_column not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    market_lookup = load_market_lookup_for_analysis(
        df,
        horizon_day_range_map=horizon_day_range_map,
        smoothing_window_map=smoothing_window_map,
        buffer_days=market_data_buffer_days,
    )

    if not market_lookup:
        return pd.DataFrame(), pd.DataFrame()

    horizon_rows = []
    quantile_rows = []
    priced_df = add_current_prices(df, market_lookup)

    for timeframe, group in priced_df.groupby("timeframe"):
        horizon_days_values = horizon_day_range_map.get(timeframe)

        if not horizon_days_values:
            continue

        window_positions = smoothing_window_map.get(timeframe, 0)

        for horizon_days in horizon_days_values:
            horizon_df = build_horizon_return_frame(
                group,
                market_lookup=market_lookup,
                score_column=score_column,
                horizon_days=horizon_days,
                window_positions=window_positions,
            )
            horizon_rows.append({
                "timeframe": timeframe,
                "horizon_days": horizon_days,
                "window_positions": window_positions,
                **calculate_return_stats(horizon_df),
            })

            for top_share in top_score_shares:
                min_score = (
                    None
                    if timeframe_score_thresholds is None
                    else timeframe_score_thresholds.get(timeframe, {}).get(top_share)
                )

                if horizon_df.empty:
                    selected = pd.DataFrame()
                else:
                    if min_score is None:
                        min_score = horizon_df[score_column].quantile(1 - top_share)
                    selected = horizon_df[horizon_df[score_column] >= min_score]

                selected_stats = calculate_correlations(
                    selected,
                    score_column,
                    return_column="future_return",
                )
                quantile_rows.append({
                    "timeframe": timeframe,
                    "horizon_days": horizon_days,
                    "window_positions": window_positions,
                    "top_share": top_share,
                    "top_percent": int(top_share * 100),
                    "threshold_scope": (
                        "per_horizon"
                        if timeframe_score_thresholds is None
                        else "timeframe"
                    ),
                    "min_score": (
                        None
                        if min_score is None
                        else round(float(min_score), 6)
                    ),
                    **selected_stats,
                    **calculate_return_stats(selected),
                })

    return (
        pd.DataFrame(horizon_rows),
        pd.DataFrame(quantile_rows),
    )


def calculate_horizon_daily_top_n_summaries(
    df,
    score_column,
    horizon_day_range_map,
    smoothing_window_map,
    top_n_values,
    market_data_buffer_days,
):
    if score_column not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    market_lookup = load_market_lookup_for_analysis(
        df,
        horizon_day_range_map=horizon_day_range_map,
        smoothing_window_map=smoothing_window_map,
        buffer_days=market_data_buffer_days,
    )

    if not market_lookup:
        return pd.DataFrame(), pd.DataFrame()

    benchmark_rows = []
    daily_top_n_rows = []
    priced_df = add_current_prices(df, market_lookup)

    for timeframe, group in priced_df.groupby("timeframe"):
        horizon_days_values = horizon_day_range_map.get(timeframe)

        if not horizon_days_values:
            continue

        window_positions = smoothing_window_map.get(timeframe, 0)

        for horizon_days in horizon_days_values:
            horizon_df = build_horizon_return_frame(
                group,
                market_lookup=market_lookup,
                score_column=score_column,
                horizon_days=horizon_days,
                window_positions=window_positions,
            )

            daily_benchmark = (
                horizon_df
                .groupby("start_timestamp", as_index=False)["future_return"]
                .mean()
            )
            benchmark_rows.append({
                "timeframe": timeframe,
                "horizon_days": horizon_days,
                "window_positions": window_positions,
                **calculate_return_stats(daily_benchmark),
            })

            ranked = (
                horizon_df
                .dropna(subset=[score_column])
                .sort_values(
                    ["start_timestamp", score_column, "ticker"],
                    ascending=[True, False, True],
                )
            )

            for top_n in top_n_values:
                if top_n == "all":
                    selected = ranked
                else:
                    selected = ranked.groupby("start_timestamp", group_keys=False).head(top_n)

                daily_selected = (
                    selected
                    .groupby("start_timestamp", as_index=False)
                    .agg(
                        future_return=("future_return", "mean"),
                        selected_count=("ticker", "count"),
                    )
                )

                selected_stats = calculate_correlations(
                    selected,
                    score_column,
                    return_column="future_return",
                )
                daily_top_n_rows.append({
                    "timeframe": timeframe,
                    "horizon_days": horizon_days,
                    "window_positions": window_positions,
                    "top_n": top_n,
                    "days_count": int(len(daily_selected)),
                    "avg_selected_count": (
                        None
                        if daily_selected.empty
                        else round(float(daily_selected["selected_count"].mean()), 6)
                    ),
                    **selected_stats,
                    **calculate_return_stats(daily_selected),
                })

    return (
        pd.DataFrame(benchmark_rows),
        pd.DataFrame(daily_top_n_rows),
    )


def calculate_horizon_daily_ic_summaries(
    df,
    score_column,
    horizon_day_range_map,
    smoothing_window_map,
    market_data_buffer_days,
):
    if score_column not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    market_lookup = load_market_lookup_for_analysis(
        df,
        horizon_day_range_map=horizon_day_range_map,
        smoothing_window_map=smoothing_window_map,
        buffer_days=market_data_buffer_days,
    )

    if not market_lookup:
        return pd.DataFrame(), pd.DataFrame()

    summary_rows = []
    detail_rows = []
    priced_df = add_current_prices(df, market_lookup)

    for timeframe, group in priced_df.groupby("timeframe"):
        horizon_days_values = horizon_day_range_map.get(timeframe)

        if not horizon_days_values:
            continue

        window_positions = smoothing_window_map.get(timeframe, 0)

        for horizon_days in horizon_days_values:
            horizon_df = build_horizon_return_frame(
                group,
                market_lookup=market_lookup,
                score_column=score_column,
                horizon_days=horizon_days,
                window_positions=window_positions,
            )

            daily_rows = []

            for start_timestamp, day_group in horizon_df.groupby("start_timestamp"):
                daily_stats = calculate_daily_score_return_correlations(
                    day_group,
                    score_column,
                )
                daily_row = {
                    "timeframe": timeframe,
                    "horizon_days": horizon_days,
                    "window_positions": window_positions,
                    "start_timestamp": start_timestamp,
                    **daily_stats,
                }
                daily_rows.append(daily_row)
                detail_rows.append(daily_row)

            daily_ic_df = pd.DataFrame(daily_rows)
            summary_rows.append({
                "timeframe": timeframe,
                "horizon_days": horizon_days,
                "window_positions": window_positions,
                **summarize_daily_ic(daily_ic_df),
            })

    return (
        pd.DataFrame(summary_rows),
        pd.DataFrame(detail_rows),
    )
