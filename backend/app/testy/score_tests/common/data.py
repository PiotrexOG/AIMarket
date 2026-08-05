import pandas as pd

from app.testy.market_return_lookup import (
    add_current_prices,
    load_market_lookup_for_analysis,
    lookup_asof_close_many,
)


def build_horizon_weeks(df):
    if df.empty:
        return []
    first_date = pd.to_datetime(df["start_timestamp"].min()).normalize()
    last_date = pd.to_datetime(df["start_timestamp"].max()).normalize()
    max_horizon_weeks = int((last_date - first_date).days // 7)
    if max_horizon_weeks < 1:
        return []
    return list(range(1, max_horizon_weeks + 1))


def filter_horizon_week_ranges(
    df,
    horizon_week_ranges=None,
    horizon_start=None,
    horizon_end=None,
    align_to_common_horizon_window=False,
):
    if df.empty or "horizon_weeks" not in df.columns:
        return df

    result = df
    if horizon_week_ranges:
        mask = pd.Series(False, index=df.index)
        for timeframe, week_range in horizon_week_ranges.items():
            start_week, end_week = week_range
            mask = mask | (
                (df["timeframe"] == timeframe)
                & df["horizon_weeks"].between(start_week, end_week)
            )
        result = df[mask].copy()

    elif horizon_start is not None and horizon_end is not None:
        result = df[df["horizon_weeks"].between(horizon_start, horizon_end)].copy()

    if align_to_common_horizon_window:
        return align_start_dates_to_common_horizon_window(result)

    return result


def align_start_dates_to_common_horizon_window(df):
    if (
        df.empty
        or not {"timeframe", "horizon_weeks", "start_timestamp"}.issubset(df.columns)
    ):
        return df.copy()

    frames = []
    for _, timeframe_group in df.groupby("timeframe", sort=False):
        horizon_count = timeframe_group["horizon_weeks"].nunique()
        if horizon_count <= 1:
            frames.append(timeframe_group.copy())
            continue

        date_horizon_counts = (
            timeframe_group[["horizon_weeks", "start_timestamp"]]
            .drop_duplicates()
            .groupby("start_timestamp")["horizon_weeks"]
            .nunique()
        )
        common_dates = date_horizon_counts[
            date_horizon_counts == horizon_count
        ].index
        if len(common_dates) == 0:
            continue

        frames.append(
            timeframe_group[
                timeframe_group["start_timestamp"].isin(common_dates)
            ].copy()
        )

    if not frames:
        return df.iloc[0:0].copy()

    return pd.concat(frames, ignore_index=True)


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

    result = df.copy()
    grouped_scores = result.groupby(["timeframe", "start_timestamp"])["score"]
    result["score_percentile"] = grouped_scores.rank(pct=True, method="average")
    score_mean = grouped_scores.transform("mean")
    score_std = grouped_scores.transform(lambda values: values.std(ddof=0))
    result["score_zscore"] = (
        (result["score"] - score_mean) / score_std.replace(0, pd.NA)
    )
    result["score_zscore"] = result["score_zscore"].fillna(0.0)
    return result.reset_index(drop=True)


def build_return_panel(df, horizon_weeks_values):
    if df.empty:
        return pd.DataFrame()

    score_end_time = pd.to_datetime(df["start_timestamp"].max())
    max_horizon_weeks = max(horizon_weeks_values) if horizon_weeks_values else 0
    max_price_timestamp = (
        score_end_time + pd.to_timedelta(max_horizon_weeks * 7, unit="D")
    )
    market_lookup = load_market_lookup_for_analysis(
        df,
        max_timestamp=max_price_timestamp,
    )
    if not market_lookup:
        return pd.DataFrame()

    priced_df = add_current_prices(df, market_lookup)
    rows = []
    for timeframe, timeframe_group in priced_df.groupby("timeframe"):
        timeframe_group = timeframe_group.sort_values(
            ["ticker", "start_timestamp"]
        ).copy()
        for horizon_weeks in horizon_weeks_values:
            horizon_df = timeframe_group[
                ["ticker", "start_timestamp", "score", "current_price"]
            ].copy()
            horizon_df["future_timestamp"] = (
                horizon_df["start_timestamp"]
                + pd.to_timedelta(horizon_weeks * 7, unit="D")
            )
            horizon_df["future_price"] = lookup_asof_close_many(
                market_lookup,
                horizon_df["ticker"],
                horizon_df["future_timestamp"],
            )
            horizon_df = horizon_df.dropna(
                subset=["current_price", "future_timestamp", "future_price"]
            )
            if horizon_df.empty:
                continue

            horizon_df["horizon_days"] = (
                pd.to_datetime(horizon_df["future_timestamp"])
                - pd.to_datetime(horizon_df["start_timestamp"])
            ).dt.total_seconds() / 86400.0
            horizon_df = horizon_df[horizon_df["horizon_days"] > 0].copy()
            if horizon_df.empty:
                continue

            horizon_df["future_return"] = (
                horizon_df["future_price"] - horizon_df["current_price"]
            ) / horizon_df["current_price"]
            horizon_df["timeframe"] = timeframe
            horizon_df["horizon_weeks"] = horizon_weeks
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
