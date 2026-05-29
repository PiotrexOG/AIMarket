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


def calculate_horizon_quantile_summaries(
    df,
    score_column,
    horizon_day_range_map,
    smoothing_window_map,
    top_score_shares,
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
                if horizon_df.empty:
                    selected = pd.DataFrame()
                    min_score = None
                else:
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
