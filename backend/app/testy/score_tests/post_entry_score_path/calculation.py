import numpy as np
import pandas as pd

from app.testy.score_tests.common.annualization import (
    CALENDAR_DAYS_PER_YEAR,
    annualize_return,
)
from app.testy.score_tests.common.metrics import round_or_none


ENTRY_MIN_SCORE_PERCENTILE = 0.8
PROGRESS_PERCENTAGES = tuple(range(5, 101, 5))
SWITCH_SCORE_CHANGE_THRESHOLDS = tuple(
    round(value, 2) for value in np.arange(-0.80, -0.10, 0.05)
)

CORRELATION_METRICS = [
    "mean_score_percentile",
    "score_percentile_change",
    "relative_score_percentile_change",
]

LIVE_CORRELATION_METRICS = [
    "mean_score_percentile",
    "score_percentile_change",
    "relative_score_percentile_change",
]

def _weighted_mean(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return None
    return float(np.average(values[valid], weights=weights[valid]))


def _overlap_days(segment_starts, segment_days, window_start, window_end):
    segment_ends = segment_starts + segment_days
    return np.maximum(
        0.0,
        np.minimum(segment_ends, window_end) - np.maximum(segment_starts, window_start),
    )


def _safe_corr(group, metric, method):
    return _safe_corr_pair(group, metric, "annualized_return", method)


def _safe_corr_pair(group, metric, return_metric, method):
    clean = group[[metric, return_metric]].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    if (
        len(clean) < 3
        or clean[metric].nunique() < 2
        or clean[return_metric].nunique() < 2
    ):
        return None
    return round_or_none(clean[metric].corr(clean[return_metric], method=method))


def _prepare_score_history(return_panel):
    columns = [
        "timeframe",
        "ticker",
        "start_timestamp",
        "score",
        "score_percentile",
        "score_zscore",
        "current_price",
    ]
    required = set(columns)
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame(columns=columns)

    return (
        return_panel[columns]
        .dropna(subset=["timeframe", "ticker", "start_timestamp", "score"])
        .drop_duplicates(["timeframe", "ticker", "start_timestamp"])
        .sort_values(["timeframe", "ticker", "start_timestamp"])
        .reset_index(drop=True)
    )


def _prepare_top_entry_observations(
    return_panel,
    horizon_start,
    horizon_end
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
        .copy()
    )
    if ranked.empty:
        return pd.DataFrame()

    ranked["entry_rank_position"] = (
        ranked.groupby(["timeframe", "horizon_days", "start_timestamp"]).cumcount()
        + 1
    )
    ranked["entry_available_count"] = ranked.groupby(
        ["timeframe", "horizon_days", "start_timestamp"]
    )["ticker"].transform("count")
    ranked["benchmark_return"] = ranked.groupby(
        ["timeframe", "horizon_days", "start_timestamp"]
    )["future_return"].transform("mean")
    ranked["annualized_benchmark_return"] = [
        annualize_return(total_return, horizon_days)
        for total_return, horizon_days in zip(
            ranked["benchmark_return"],
            ranked["horizon_days"],
        )
    ]
    ranked = ranked[
        ranked["score_percentile"] >= ENTRY_MIN_SCORE_PERCENTILE
    ].copy()
    ranked["annualized_return"] = [
        annualize_return(total_return, horizon_days)
        for total_return, horizon_days in zip(
            ranked["future_return"],
            ranked["horizon_days"],
        )
    ]
    ranked = ranked.dropna(subset=["annualized_return"])
    ranked["annualized_alpha"] = (
        ranked["annualized_return"] - ranked["annualized_benchmark_return"]
    )
    ranked["observation_id"] = (
        ranked.groupby(["timeframe", "horizon_days"]).cumcount() + 1
    )
    return ranked.reset_index(drop=True)


def _prepare_benchmark_observations(
    return_panel,
    horizon_start,
    horizon_end,
):
    required = {
        "timeframe",
        "horizon_days",
        "start_timestamp",
        "future_timestamp",
        "ticker",
        "score",
        "future_return",
        "current_price",
        "future_price",
    }
    if return_panel.empty or not required.issubset(return_panel.columns):
        return pd.DataFrame()

    benchmark = (
        return_panel[
            return_panel["horizon_days"].between(horizon_start, horizon_end)
        ]
        .dropna(
            subset=[
                "score",
                "future_return",
                "current_price",
                "future_price",
            ]
        )
        .sort_values(
            ["timeframe", "horizon_days", "start_timestamp", "score", "ticker"],
            ascending=[True, True, True, False, True],
        )
        .copy()
    )
    if benchmark.empty:
        return pd.DataFrame()

    benchmark = benchmark[
        (benchmark["current_price"] > 0)
        & (benchmark["future_price"] > 0)
        & (benchmark["future_return"] > -1)
    ].copy()
    return benchmark.reset_index(drop=True)


def _build_history_lookup(history):
    return {
        key: group.reset_index(drop=True)
        for key, group in history.groupby(
            ["timeframe", "ticker"],
            sort=False,
        )
    }


def _build_path_for_entry(entry, history_lookup):
    start_timestamp = pd.Timestamp(entry["start_timestamp"])
    end_timestamp = start_timestamp + pd.to_timedelta(
        int(entry["horizon_days"]),
        unit="D",
    )
    ticker_history = history_lookup.get(
        (entry["timeframe"], entry["ticker"])
    )
    if ticker_history is None:
        return pd.DataFrame()
    path = ticker_history[
        (ticker_history["start_timestamp"] >= start_timestamp)
        & (ticker_history["start_timestamp"] <= end_timestamp)
    ].copy()
    if path.empty:
        return path

    path = path.sort_values("start_timestamp").reset_index(drop=True)
    next_timestamps = path["start_timestamp"].shift(-1)
    path["next_score_timestamp"] = next_timestamps.fillna(end_timestamp)
    path["next_score_timestamp"] = pd.to_datetime(
        np.minimum(
            path["next_score_timestamp"].to_numpy(dtype="datetime64[ns]"),
            np.datetime64(end_timestamp),
        )
    )
    path["elapsed_days"] = (
        pd.to_datetime(path["start_timestamp"]) - start_timestamp
    ).dt.days.clip(lower=0)
    path["segment_days"] = (
        path["next_score_timestamp"] - pd.to_datetime(path["start_timestamp"])
    ).dt.days.clip(lower=0)
    path["segment_horizon_share"] = (
        path["segment_days"] / float(entry["horizon_days"])
    )
    return path


def _build_remaining_benchmark_lookup(benchmark_entries, history):
    key_columns = [
        "timeframe",
        "horizon_days",
        "start_timestamp",
        "progress_percent",
    ]
    output_columns = [
        *key_columns,
        "remaining_benchmark_return",
        "remaining_annualized_benchmark_return",
        "benchmark_remaining_observation_count",
    ]
    if benchmark_entries.empty or history.empty:
        return {}

    history_prices = (
        history[
            ["timeframe", "ticker", "start_timestamp", "current_price"]
        ]
        .dropna(subset=["current_price"])
        .rename(
            columns={
                "start_timestamp": "price_timestamp",
                "current_price": "price_at_cutoff",
            }
        )
        .copy()
    )
    history_prices = history_prices[
        (history_prices["price_at_cutoff"] > 0)
    ].copy()
    if history_prices.empty:
        return {}

    history_prices["price_timestamp"] = pd.to_datetime(
        history_prices["price_timestamp"]
    )
    history_prices = history_prices.sort_values(
        ["price_timestamp", "timeframe", "ticker"]
    ).reset_index(drop=True)

    base_entries = benchmark_entries[
        [
            "timeframe",
            "horizon_days",
            "start_timestamp",
            "future_timestamp",
            "ticker",
            "future_price",
        ]
    ].copy()
    base_entries["start_timestamp"] = pd.to_datetime(
        base_entries["start_timestamp"]
    )

    frames = []
    for progress_percent in PROGRESS_PERCENTAGES:
        entries = base_entries.copy()
        entries["progress_percent"] = int(progress_percent)
        entries["cutoff_days"] = (
            entries["horizon_days"] * progress_percent / 100.0
        )
        entries["remaining_days"] = (
            entries["horizon_days"] - entries["cutoff_days"]
        )
        entries = entries[entries["remaining_days"] > 0].copy()
        if entries.empty:
            continue

        entries["cutoff_timestamp"] = (
            entries["start_timestamp"]
            + pd.to_timedelta(entries["cutoff_days"], unit="D")
        )
        entries = entries.sort_values(
            ["cutoff_timestamp", "timeframe", "ticker"]
        ).reset_index(drop=True)

        matched = pd.merge_asof(
            entries,
            history_prices,
            left_on="cutoff_timestamp",
            right_on="price_timestamp",
            by=["timeframe", "ticker"],
            direction="backward",
        )
        matched = matched[
            matched["price_timestamp"].notna()
            & (matched["price_timestamp"] >= matched["start_timestamp"])
            & (matched["price_at_cutoff"] > 0)
            & (matched["future_price"] > 0)
        ].copy()
        if matched.empty:
            continue

        matched["benchmark_constituent_remaining_return"] = (
            matched["future_price"] / matched["price_at_cutoff"] - 1.0
        )
        matched = matched[
            np.isfinite(matched["benchmark_constituent_remaining_return"])
            & (matched["benchmark_constituent_remaining_return"] > -1)
        ]
        if matched.empty:
            continue

        frames.append(matched)

    if not frames:
        return {}

    constituents = pd.concat(frames, ignore_index=True)
    grouped = (
        constituents.groupby(key_columns, sort=False)
        .agg(
            remaining_benchmark_return=(
                "benchmark_constituent_remaining_return",
                "mean",
            ),
            remaining_days=("remaining_days", "mean"),
            benchmark_remaining_observation_count=(
                "benchmark_constituent_remaining_return",
                "count",
            ),
        )
        .reset_index()
    )
    grouped["remaining_annualized_benchmark_return"] = [
        annualize_return(total_return, remaining_days)
        for total_return, remaining_days in zip(
            grouped["remaining_benchmark_return"],
            grouped["remaining_days"],
        )
    ]

    return (
        grouped[output_columns]
        .set_index(key_columns)
        .to_dict(orient="index")
    )


def _summarize_entry_path(entry, path):
    horizon_days = int(entry["horizon_days"])
    segment_days = path["segment_days"].to_numpy(dtype=float)
    covered_days = float(np.nansum(segment_days))

    mean_score_percentile = _weighted_mean(
        path["score_percentile"],
        segment_days,
    )
    score_percentile_drop = (
        float(entry["score_percentile"]) - mean_score_percentile
        if mean_score_percentile is not None
        else None
    )
    relative_score_percentile_drop = (
        score_percentile_drop / float(entry["score_percentile"])
        if score_percentile_drop is not None
        and float(entry["score_percentile"]) > 0
        else None
    )
    score_percentile_change = (
        -score_percentile_drop
        if score_percentile_drop is not None
        else None
    )
    relative_score_percentile_change = (
        -relative_score_percentile_drop
        if relative_score_percentile_drop is not None
        else None
    )

    row = {
        "timeframe": entry["timeframe"],
        "horizon_days": horizon_days,
        "observation_id": int(entry["observation_id"]),
        "start_timestamp": entry["start_timestamp"],
        "future_timestamp": entry["future_timestamp"],
        "ticker": entry["ticker"],
        "entry_score": float(entry["score"]),
        "entry_score_percentile": float(entry["score_percentile"]),
        "entry_score_zscore": float(entry["score_zscore"]),
        "entry_rank_position": int(entry["entry_rank_position"]),
        "entry_available_count": int(entry["entry_available_count"]),
        "current_price": float(entry["current_price"]),
        "future_price": float(entry["future_price"]),
        "future_return": float(entry["future_return"]),
        "annualized_return": float(entry["annualized_return"]),
        "benchmark_return": float(entry["benchmark_return"]),
        "annualized_benchmark_return": (
            float(entry["annualized_benchmark_return"])
            if pd.notna(entry["annualized_benchmark_return"])
            else None
        ),
        "annualized_alpha": (
            float(entry["annualized_alpha"])
            if pd.notna(entry["annualized_alpha"])
            else None
        ),
        "path_point_count": int(len(path)),
        "path_covered_days": covered_days,
        "path_covered_horizon_share": covered_days / horizon_days,
        "mean_score_percentile": mean_score_percentile,
        "score_percentile_drop": score_percentile_drop,
        "relative_score_percentile_drop": relative_score_percentile_drop,
        "score_percentile_change": score_percentile_change,
        "relative_score_percentile_change": relative_score_percentile_change,
    }

    return row


def _summarize_live_progress(entry, path, remaining_benchmark_lookup):
    rows = []
    horizon_days = int(entry["horizon_days"])
    elapsed_days = path["elapsed_days"].to_numpy(dtype=float)
    segment_days = path["segment_days"].to_numpy(dtype=float)
    score_percentiles = path["score_percentile"].to_numpy(dtype=float)
    price_timestamps = pd.to_datetime(path["start_timestamp"])
    prices = path["current_price"].to_numpy(dtype=float)

    for progress_percent in PROGRESS_PERCENTAGES:
        cutoff_days = horizon_days * progress_percent / 100.0
        cutoff_timestamp = pd.Timestamp(
            entry["start_timestamp"]
        ) + pd.to_timedelta(cutoff_days, unit="D")
        live_segment_days = _overlap_days(
            elapsed_days,
            segment_days,
            0.0,
            cutoff_days,
        )
        entry_score_percentile = float(entry["score_percentile"])
        mean_score_percentile = _weighted_mean(
            score_percentiles,
            live_segment_days,
        )
        score_percentile_change = (
            mean_score_percentile - entry_score_percentile
            if mean_score_percentile is not None
            else None
        )
        relative_score_percentile_change = (
            score_percentile_change / entry_score_percentile
            if score_percentile_change is not None
            and entry_score_percentile > 0
            else None
        )
        price_mask = (
            (price_timestamps <= cutoff_timestamp)
            & np.isfinite(prices)
            & (prices > 0)
        )
        if price_mask.any():
            price_index = int(np.flatnonzero(price_mask)[-1])
            price_at_cutoff = float(prices[price_index])
            price_timestamp = price_timestamps.iloc[price_index]
            price_elapsed_days = float(elapsed_days[price_index])
        else:
            price_at_cutoff = None
            price_timestamp = pd.NaT
            price_elapsed_days = None

        remaining_days = horizon_days - cutoff_days
        remaining_return = (
            float(entry["future_price"]) / price_at_cutoff - 1.0
            if price_at_cutoff is not None
            else None
        )
        remaining_annualized_return = (
            annualize_return(remaining_return, remaining_days)
            if remaining_return is not None and remaining_days > 0
            else None
        )
        benchmark_key = (
            entry["timeframe"],
            horizon_days,
            entry["start_timestamp"],
            int(progress_percent),
        )
        remaining_benchmark = remaining_benchmark_lookup.get(
            benchmark_key,
            {},
        )
        remaining_benchmark_return = remaining_benchmark.get(
            "remaining_benchmark_return"
        )
        remaining_annualized_benchmark_return = remaining_benchmark.get(
            "remaining_annualized_benchmark_return"
        )
        switch_to_benchmark_return_gain = (
            remaining_benchmark_return - remaining_return
            if remaining_benchmark_return is not None
            and remaining_return is not None
            else None
        )
        switch_to_benchmark_annualized_gain = (
            remaining_annualized_benchmark_return - remaining_annualized_return
            if remaining_annualized_benchmark_return is not None
            and remaining_annualized_return is not None
            else None
        )
        remaining_annualized_alpha = (
            remaining_annualized_return - remaining_annualized_benchmark_return
            if remaining_annualized_return is not None
            and remaining_annualized_benchmark_return is not None
            else None
        )
        entry_price = float(entry["current_price"])
        price_change_to_cutoff = (
            price_at_cutoff / entry_price - 1.0
            if price_at_cutoff is not None and entry_price > 0
            else None
        )
        rows.append({
            "timeframe": entry["timeframe"],
            "horizon_days": horizon_days,
            "observation_id": int(entry["observation_id"]),
            "start_timestamp": entry["start_timestamp"],
            "future_timestamp": entry["future_timestamp"],
            "ticker": entry["ticker"],
            "progress_percent": progress_percent,
            "progress_share": progress_percent / 100.0,
            "cutoff_days": cutoff_days,
            "cutoff_timestamp": cutoff_timestamp,
            "entry_score_percentile": entry_score_percentile,
            "mean_score_percentile": mean_score_percentile,
            "score_percentile_change": score_percentile_change,
            "relative_score_percentile_change": (
                relative_score_percentile_change
            ),
            "price_at_cutoff": price_at_cutoff,
            "price_timestamp": price_timestamp,
            "price_elapsed_days": price_elapsed_days,
            "price_horizon_share": (
                price_elapsed_days / horizon_days
                if price_elapsed_days is not None
                else None
            ),
            "entry_price": entry_price,
            "price_change_to_cutoff": price_change_to_cutoff,
            "future_price": float(entry["future_price"]),
            "remaining_days": remaining_days,
            "remaining_return": remaining_return,
            "remaining_annualized_return": remaining_annualized_return,
            "remaining_benchmark_return": remaining_benchmark_return,
            "remaining_annualized_benchmark_return": (
                remaining_annualized_benchmark_return
            ),
            "remaining_annualized_alpha": remaining_annualized_alpha,
            "switch_to_benchmark_return_gain": (
                switch_to_benchmark_return_gain
            ),
            "switch_to_benchmark_annualized_gain": (
                switch_to_benchmark_annualized_gain
            ),
            "switch_to_benchmark_would_win": (
                switch_to_benchmark_annualized_gain > 0
                if switch_to_benchmark_annualized_gain is not None
                else None
            ),
            "benchmark_remaining_observation_count": remaining_benchmark.get(
                "benchmark_remaining_observation_count"
            ),
            "future_return": float(entry["future_return"]),
            "annualized_return": float(entry["annualized_return"]),
            "benchmark_return": float(entry["benchmark_return"]),
            "annualized_benchmark_return": (
                float(entry["annualized_benchmark_return"])
                if pd.notna(entry["annualized_benchmark_return"])
                else None
            ),
            "annualized_alpha": (
                float(entry["annualized_alpha"])
                if pd.notna(entry["annualized_alpha"])
                else None
            ),
        })

    return rows


def _build_observations_and_paths(
    entries,
    history_lookup,
    remaining_benchmark_lookup,
):
    observation_rows = []
    live_progress_rows = []
    path_frames = []

    for _, entry in entries.iterrows():
        path = _build_path_for_entry(entry, history_lookup)
        if path.empty:
            continue

        observation_rows.append(_summarize_entry_path(entry, path))
        live_progress_rows.extend(
            _summarize_live_progress(
                entry,
                path,
                remaining_benchmark_lookup,
            )
        )
        path = path.copy()
        path["timeframe"] = entry["timeframe"]
        path["horizon_days"] = int(entry["horizon_days"])
        path["observation_id"] = int(entry["observation_id"])
        path["entry_start_timestamp"] = entry["start_timestamp"]
        path["future_timestamp"] = entry["future_timestamp"]
        path["future_return"] = float(entry["future_return"])
        path["annualized_return"] = float(entry["annualized_return"])
        path["benchmark_return"] = float(entry["benchmark_return"])
        path["annualized_benchmark_return"] = (
            float(entry["annualized_benchmark_return"])
            if pd.notna(entry["annualized_benchmark_return"])
            else None
        )
        path["annualized_alpha"] = (
            float(entry["annualized_alpha"])
            if pd.notna(entry["annualized_alpha"])
            else None
        )
        path_frames.append(path)

    observations = pd.DataFrame(observation_rows)
    path_points = (
        pd.concat(path_frames, ignore_index=True)
        if path_frames
        else pd.DataFrame()
    )
    return observations, path_points, pd.DataFrame(live_progress_rows)


def _summarize_switch_group(group):
    annualized_gain = group["switch_to_benchmark_annualized_gain"].to_numpy(
        dtype=float
    )
    return_gain = group["switch_to_benchmark_return_gain"].to_numpy(dtype=float)
    downside_gain = np.minimum(0.0, annualized_gain)
    mean_annualized_gain = float(annualized_gain.mean())
    downside_deviation = float(np.sqrt(np.mean(np.square(downside_gain))))

    if downside_deviation == 0:
        downside_information_ratio = (
            0.0
            if mean_annualized_gain == 0
            else np.inf * np.sign(mean_annualized_gain)
        )
    else:
        downside_information_ratio = mean_annualized_gain / downside_deviation

    return {
        "switch_count": int(len(group)),
        "downside_count": int((annualized_gain < 0).sum()),
        "downside_frequency": float((annualized_gain < 0).mean()),
        "benchmark_win_frequency": float((annualized_gain > 0).mean()),
        "mean_switch_to_benchmark_return_gain": float(return_gain.mean()),
        "mean_switch_to_benchmark_annualized_gain": mean_annualized_gain,
        "median_switch_to_benchmark_annualized_gain": float(
            np.median(annualized_gain)
        ),
        "downside_deviation": downside_deviation,
        "downside_information_ratio": downside_information_ratio,
        "mean_remaining_return": float(group["remaining_return"].mean()),
        "mean_remaining_annualized_return": float(
            group["remaining_annualized_return"].mean()
        ),
        "mean_remaining_benchmark_return": float(
            group["remaining_benchmark_return"].mean()
        ),
        "mean_remaining_annualized_benchmark_return": float(
            group["remaining_annualized_benchmark_return"].mean()
        ),
    }


def _mark_best_switch_thresholds(result, group_columns):
    if result.empty:
        return result

    result = result.copy()
    result["is_max_downside_information_ratio"] = False
    result["is_max_mean_switch_gain"] = False

    grouped = result.groupby(list(group_columns), sort=False)
    for _, group in grouped:
        finite_ratio = group[
            np.isfinite(group["downside_information_ratio"].to_numpy(dtype=float))
        ]
        if not finite_ratio.empty:
            max_ratio_index = finite_ratio["downside_information_ratio"].idxmax()
            result.loc[max_ratio_index, "is_max_downside_information_ratio"] = True

        finite_gain = group[
            np.isfinite(
                group["mean_switch_to_benchmark_annualized_gain"].to_numpy(
                    dtype=float
                )
            )
        ]
        if not finite_gain.empty:
            max_gain_index = finite_gain[
                "mean_switch_to_benchmark_annualized_gain"
            ].idxmax()
            result.loc[max_gain_index, "is_max_mean_switch_gain"] = True

    return result


def _build_switch_to_benchmark_threshold_analysis(
    live_progress_observations,
    thresholds=SWITCH_SCORE_CHANGE_THRESHOLDS,
    group_columns=("timeframe", "progress_percent"),
):
    columns = [
        *group_columns,
        "progress_share",
        "score_change_threshold",
        "score_change_threshold_percent",
        "observation_count",
        "switch_count",
        "switch_share",
        "downside_count",
        "downside_frequency",
        "benchmark_win_frequency",
        "mean_switch_to_benchmark_return_gain",
        "mean_switch_to_benchmark_annualized_gain",
        "median_switch_to_benchmark_annualized_gain",
        "downside_deviation",
        "downside_information_ratio",
        "mean_remaining_return",
        "mean_remaining_annualized_return",
        "mean_remaining_benchmark_return",
        "mean_remaining_annualized_benchmark_return",
        "is_max_downside_information_ratio",
        "is_max_mean_switch_gain",
    ]
    required = [
        "relative_score_percentile_change",
        "switch_to_benchmark_return_gain",
        "switch_to_benchmark_annualized_gain",
        "remaining_return",
        "remaining_annualized_return",
        "remaining_benchmark_return",
        "remaining_annualized_benchmark_return",
    ]
    if (
        live_progress_observations.empty
        or not set(required).issubset(live_progress_observations.columns)
    ):
        return pd.DataFrame(columns=columns)

    data = (
        live_progress_observations.replace([np.inf, -np.inf], np.nan)
        .dropna(subset=required)
        .copy()
    )
    if data.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for group_key, group in data.groupby(list(group_columns), sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        group_values = dict(zip(group_columns, group_key))
        observation_count = int(len(group))

        for threshold in thresholds:
            selected = group[
                group["relative_score_percentile_change"] <= threshold
            ]
            if selected.empty:
                continue

            summary = _summarize_switch_group(selected)
            rows.append({
                **group_values,
                "progress_share": (
                    float(group["progress_share"].iloc[0])
                    if "progress_share" in group.columns
                    else group_values.get("progress_percent") / 100.0
                ),
                "score_change_threshold": float(threshold),
                "score_change_threshold_percent": round_or_none(
                    float(threshold) * 100
                ),
                "observation_count": observation_count,
                "switch_share": len(selected) / observation_count,
                **summary,
            })

    if not rows:
        return pd.DataFrame(columns=columns)

    result = pd.DataFrame(rows)
    result = _mark_best_switch_thresholds(result, group_columns)
    return (
        result[columns]
        .sort_values([*group_columns, "score_change_threshold"])
        .reset_index(drop=True)
    )


def _build_correlations_by_horizon(observations):
    rows = []
    if observations.empty:
        return pd.DataFrame()

    for (timeframe, horizon_days), group in observations.groupby(
        ["timeframe", "horizon_days"],
        sort=False,
    ):
        for metric in CORRELATION_METRICS:
            rows.append({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "metric": metric,
                "observation_count": int(group[[metric, "annualized_return"]].dropna().shape[0]),
                "pearson_to_annualized_return": _safe_corr(group, metric, "pearson"),
                "spearman_to_annualized_return": _safe_corr(group, metric, "spearman"),
                "mean_metric_value": round_or_none(group[metric].mean()),
                "mean_annualized_return": round_or_none(
                    group["annualized_return"].mean()
                ),
            })

    return pd.DataFrame(rows)


def _build_horizon_average(correlations_by_horizon):
    columns = [
        "timeframe",
        "horizon_start",
        "horizon_end",
        "horizon_count",
        "aggregation_method",
        "metric",
        "mean_observation_count",
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
        "mean_metric_value",
        "mean_annualized_return",
    ]
    if correlations_by_horizon.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (timeframe, metric), group in correlations_by_horizon.groupby(
        ["timeframe", "metric"],
        sort=False,
    ):
        rows.append({
            "timeframe": timeframe,
            "horizon_start": int(group["horizon_days"].min()),
            "horizon_end": int(group["horizon_days"].max()),
            "horizon_count": int(group["horizon_days"].nunique()),
            "aggregation_method": "equal_weight_mean_across_horizons",
            "metric": metric,
            "mean_observation_count": round_or_none(
                group["observation_count"].mean()
            ),
            "mean_pearson_to_annualized_return": round_or_none(
                group["pearson_to_annualized_return"].mean()
            ),
            "mean_spearman_to_annualized_return": round_or_none(
                group["spearman_to_annualized_return"].mean()
            ),
            "mean_metric_value": round_or_none(group["mean_metric_value"].mean()),
            "mean_annualized_return": round_or_none(
                group["mean_annualized_return"].mean()
            ),
        })

    return pd.DataFrame(rows, columns=columns).sort_values(
        ["timeframe", "metric"]
    ).reset_index(drop=True)


def _build_live_progress_correlations_by_horizon(live_progress_observations):
    rows = []
    if live_progress_observations.empty:
        return pd.DataFrame()

    grouped = live_progress_observations.groupby(
        ["timeframe", "horizon_days", "progress_percent"],
        sort=False,
    )
    for (timeframe, horizon_days, progress_percent), group in grouped:
        for metric in LIVE_CORRELATION_METRICS:
            rows.append({
                "timeframe": timeframe,
                "horizon_days": int(horizon_days),
                "progress_percent": int(progress_percent),
                "progress_share": progress_percent / 100.0,
                "cutoff_days": round_or_none(group["cutoff_days"].mean()),
                "metric": metric,
                "observation_count": int(
                    group[[metric, "annualized_return"]].dropna().shape[0]
                ),
                "pearson_to_annualized_return": _safe_corr(
                    group,
                    metric,
                    "pearson",
                ),
                "spearman_to_annualized_return": _safe_corr(
                    group,
                    metric,
                    "spearman",
                ),
            })

    return pd.DataFrame(rows)


def _build_live_progress_average(correlations_by_horizon):
    columns = [
        "timeframe",
        "progress_percent",
        "progress_share",
        "metric",
        "horizon_start",
        "horizon_end",
        "horizon_count",
        "mean_cutoff_days",
        "mean_observation_count",
        "mean_pearson_to_annualized_return",
        "mean_spearman_to_annualized_return",
    ]
    if correlations_by_horizon.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    grouped = correlations_by_horizon.groupby(
        ["timeframe", "progress_percent", "metric"],
        sort=False,
    )
    for (timeframe, progress_percent, metric), group in grouped:
        rows.append({
            "timeframe": timeframe,
            "progress_percent": int(progress_percent),
            "progress_share": progress_percent / 100.0,
            "metric": metric,
            "horizon_start": int(group["horizon_days"].min()),
            "horizon_end": int(group["horizon_days"].max()),
            "horizon_count": int(group["horizon_days"].nunique()),
            "mean_cutoff_days": round_or_none(group["cutoff_days"].mean()),
            "mean_observation_count": round_or_none(
                group["observation_count"].mean()
            ),
            "mean_pearson_to_annualized_return": round_or_none(
                group["pearson_to_annualized_return"].mean()
            ),
            "mean_spearman_to_annualized_return": round_or_none(
                group["spearman_to_annualized_return"].mean()
            ),
        })

    return pd.DataFrame(rows, columns=columns).sort_values(
        ["timeframe", "metric", "progress_percent"]
    ).reset_index(drop=True)


def _fit_drop_regression(group):
    columns = [
        "entry_score_percentile",
        "score_percentile_drop",
        "annualized_return",
    ]
    clean = group[columns].replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 8:
        return None

    entry = clean["entry_score_percentile"].to_numpy(dtype=float)
    drop = clean["score_percentile_drop"].to_numpy(dtype=float)
    response = clean["annualized_return"].to_numpy(dtype=float)
    design = np.column_stack([
        np.ones(len(clean)),
        entry,
        drop,
        entry * drop,
    ])
    if np.linalg.matrix_rank(design) < design.shape[1]:
        return None

    coefficients, _, _, _ = np.linalg.lstsq(design, response, rcond=None)
    fitted = design @ coefficients
    residual_sum_squares = float(np.sum((response - fitted) ** 2))
    total_sum_squares = float(np.sum((response - response.mean()) ** 2))
    r_squared = (
        1.0 - residual_sum_squares / total_sum_squares
        if total_sum_squares > 0
        else None
    )
    return {
        "observation_count": int(len(clean)),
        "intercept": float(coefficients[0]),
        "entry_score_percentile_coefficient": float(coefficients[1]),
        "score_percentile_drop_coefficient": float(coefficients[2]),
        "entry_drop_interaction_coefficient": float(coefficients[3]),
        "r_squared": r_squared,
    }


def _build_drop_regressions_by_horizon(observations):
    rows = []
    if observations.empty:
        return pd.DataFrame()

    for (timeframe, horizon_days), group in observations.groupby(
        ["timeframe", "horizon_days"],
        sort=False,
    ):
        regression = _fit_drop_regression(group)
        if regression is None:
            continue
        rows.append({
            "timeframe": timeframe,
            "horizon_days": int(horizon_days),
            **regression,
        })
    return pd.DataFrame(rows)


def _build_drop_regression_average(regressions):
    columns = [
        "timeframe",
        "horizon_start",
        "horizon_end",
        "horizon_count",
        "mean_observation_count",
        "mean_intercept",
        "mean_entry_score_percentile_coefficient",
        "mean_score_percentile_drop_coefficient",
        "score_drop_negative_coefficient_share",
        "mean_entry_drop_interaction_coefficient",
        "mean_r_squared",
    ]
    if regressions.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for timeframe, group in regressions.groupby("timeframe", sort=False):
        drop_coefficients = group["score_percentile_drop_coefficient"].dropna()
        rows.append({
            "timeframe": timeframe,
            "horizon_start": int(group["horizon_days"].min()),
            "horizon_end": int(group["horizon_days"].max()),
            "horizon_count": int(group["horizon_days"].nunique()),
            "mean_observation_count": group["observation_count"].mean(),
            "mean_intercept": group["intercept"].mean(),
            "mean_entry_score_percentile_coefficient": (
                group["entry_score_percentile_coefficient"].mean()
            ),
            "mean_score_percentile_drop_coefficient": (
                drop_coefficients.mean()
            ),
            "score_drop_negative_coefficient_share": (
                (drop_coefficients < 0).mean()
                if not drop_coefficients.empty
                else None
            ),
            "mean_entry_drop_interaction_coefficient": (
                group["entry_drop_interaction_coefficient"].mean()
            ),
            "mean_r_squared": group["r_squared"].mean(),
        })
    return pd.DataFrame(rows, columns=columns)


def _round_numeric_columns(df):
    if df.empty:
        return df
    result = df.copy()
    for column in result.select_dtypes(include=[np.number]).columns:
        if column not in {
            "horizon_days",
            "observation_id",
            "entry_rank_position",
            "entry_available_count",
            "rank_position",
            "available_count",
            "path_point_count",
        }:
            result[column] = result[column].round(6)
    return result


def calculate(
    context,
    horizon_start,
    horizon_end
):
    history = _prepare_score_history(context.return_panel)
    history_lookup = _build_history_lookup(history)
    entries = _prepare_top_entry_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    benchmark_entries = _prepare_benchmark_observations(
        context.weekly_ranked,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    remaining_benchmark_lookup = _build_remaining_benchmark_lookup(
        benchmark_entries,
        history,
    )
    observations, path_points, live_progress_observations = (
        _build_observations_and_paths(
            entries,
            history_lookup,
            remaining_benchmark_lookup,
        )
    )
    correlations_by_horizon = _build_correlations_by_horizon(observations)
    horizon_average = _build_horizon_average(correlations_by_horizon)
    live_progress_correlations_by_horizon = (
        _build_live_progress_correlations_by_horizon(live_progress_observations)
    )
    live_progress_average = _build_live_progress_average(
        live_progress_correlations_by_horizon
    )
    drop_regressions_by_horizon = _build_drop_regressions_by_horizon(
        observations
    )
    drop_regression_average = _build_drop_regression_average(
        drop_regressions_by_horizon
    )
    switch_to_benchmark_thresholds_by_horizon = (
        _build_switch_to_benchmark_threshold_analysis(
            live_progress_observations,
            group_columns=("timeframe", "horizon_days", "progress_percent"),
        )
    )
    switch_to_benchmark_thresholds = (
        _build_switch_to_benchmark_threshold_analysis(
            live_progress_observations,
            group_columns=("timeframe", "progress_percent"),
        )
    )

    return {
        "observations": _round_numeric_columns(observations),
        "path_points": _round_numeric_columns(path_points),
        "correlations_by_horizon": _round_numeric_columns(correlations_by_horizon),
        "horizon_average": _round_numeric_columns(horizon_average),
        "live_progress_observations": _round_numeric_columns(
            live_progress_observations
        ),
        "live_progress_correlations_by_horizon": _round_numeric_columns(
            live_progress_correlations_by_horizon
        ),
        "live_progress_average": _round_numeric_columns(live_progress_average),
        "drop_regressions_by_horizon": _round_numeric_columns(
            drop_regressions_by_horizon
        ),
        "drop_regression_average": _round_numeric_columns(
            drop_regression_average
        ),
        "switch_to_benchmark_thresholds_by_horizon": _round_numeric_columns(
            switch_to_benchmark_thresholds_by_horizon
        ),
        "switch_to_benchmark_thresholds": _round_numeric_columns(
            switch_to_benchmark_thresholds
        ),
    }
