import pandas as pd

from app.testy.market_return_lookup import (
    add_current_prices,
    build_horizon_return_frame,
    load_market_lookup_for_analysis,
)


PRICE_WINDOW_SHARE_OF_HORIZON = 0.42


def build_horizon_days(df):
    if df.empty:
        return []
    first_date = pd.to_datetime(df["start_timestamp"].min()).normalize()
    last_date = pd.to_datetime(df["start_timestamp"].max()).normalize()
    max_horizon_days = int((last_date - first_date).days)
    return [] if max_horizon_days < 1 else list(range(1, max_horizon_days + 1))


def build_timeframe_score_observations(df, score_column):
    required = {"timeframe", "ticker", "start_timestamp", score_column}
    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame()

    result = (
        df.dropna(subset=list(required))
        .groupby(["timeframe", "start_timestamp", "ticker"], as_index=False)
        .agg(score=(score_column, "mean"))
    )
    result["score"] = pd.to_numeric(result["score"], errors="coerce")
    return result.dropna(subset=["score"])


def add_weekly_score_metrics(df):
    if df.empty:
        return df

    def add_group_metrics(group):
        group = group.copy()
        group["score_percentile"] = group["score"].rank(pct=True, method="average")
        std = group["score"].std(ddof=0)
        group["score_zscore"] = (
            0.0
            if std == 0 or pd.isna(std)
            else (group["score"] - group["score"].mean()) / std
        )
        return group

    return (
        df.groupby(["timeframe", "start_timestamp"], group_keys=False)
        .apply(add_group_metrics)
        .reset_index(drop=True)
    )


def build_return_panel(df, horizon_days_values):
    if df.empty:
        return pd.DataFrame()

    score_end_time = pd.to_datetime(df["start_timestamp"].max())
    market_lookup = load_market_lookup_for_analysis(df, max_timestamp=score_end_time)
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
    return panel.merge(
        df[
            [
                "timeframe",
                "ticker",
                "start_timestamp",
                "score_percentile",
                "score_zscore",
            ]
        ],
        on=["timeframe", "ticker", "start_timestamp"],
        how="left",
    )
