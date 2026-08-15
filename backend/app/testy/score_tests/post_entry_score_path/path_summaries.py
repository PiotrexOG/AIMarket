import numpy as np
import pandas as pd

from app.testy.market_return_lookup import lookup_asof_close_many
from app.testy.score_tests.common.annualization import annualize_return

from .config import ENTRY_BUCKET_COLUMNS
from .path_building import _build_path_for_entry
from .utilities import (
    _overlap_days,
    _progress_bucket,
    _progress_weeks_for_horizon,
    _weighted_mean,
)


def _summarize_entry_path(entry, path):
    horizon_days = int(entry["horizon_days"])
    horizon_weeks = int(entry["horizon_weeks"])
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
        **{
            column: entry.get(column)
            for column in ENTRY_BUCKET_COLUMNS
            if column in entry
        },
        "horizon_weeks": horizon_weeks,
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
        "benchmark_return": entry.get("benchmark_return"),
        "annualized_benchmark_return": entry.get(
            "annualized_benchmark_return"
        ),
        "annualized_alpha": entry.get("annualized_alpha"),
        "benchmark_observation_count": entry.get(
            "benchmark_observation_count"
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


def _summarize_live_progress(entry, path, market_lookup, remaining_benchmark_lookup):
    rows = []
    horizon_days = int(entry["horizon_days"])
    horizon_weeks = int(entry["horizon_weeks"])
    current_price = float(entry["current_price"])
    future_price = float(entry["future_price"])
    future_return = float(entry["future_return"])
    elapsed_days = path["elapsed_days"].to_numpy(dtype=float)
    segment_days = path["segment_days"].to_numpy(dtype=float)
    score_percentiles = path["score_percentile"].to_numpy(dtype=float)

    for cutoff_weeks in _progress_weeks_for_horizon(horizon_weeks):
        cutoff_timestamp = pd.Timestamp(entry["start_timestamp"]) + pd.to_timedelta(
            cutoff_weeks * 7,
            unit="D",
        )
        cutoff_days = (
            cutoff_timestamp - pd.Timestamp(entry["start_timestamp"])
        ).total_seconds() / 86400.0
        progress_share = cutoff_weeks / horizon_weeks
        progress_percent = progress_share * 100.0
        progress_bucket = _progress_bucket(progress_percent)
        if progress_bucket is None:
            continue

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
        cutoff_price = lookup_asof_close_many(
            market_lookup,
            [entry["ticker"]],
            [cutoff_timestamp],
        )
        price_at_cutoff = (
            float(cutoff_price[0])
            if len(cutoff_price) and np.isfinite(cutoff_price[0]) and cutoff_price[0] > 0
            else None
        )

        price_change_to_cutoff = (
            price_at_cutoff / current_price - 1.0
            if price_at_cutoff is not None and current_price > 0
            else None
        )
        remaining_days = (
            pd.Timestamp(entry["future_timestamp"]) - cutoff_timestamp
        ).total_seconds() / 86400.0
        remaining_return = (
            future_price / price_at_cutoff - 1.0
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
            horizon_weeks,
            entry["start_timestamp"],
            int(cutoff_weeks),
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
        rows.append({
            "timeframe": entry["timeframe"],
            **{
                column: entry.get(column)
                for column in ENTRY_BUCKET_COLUMNS
                if column in entry
            },
            "horizon_weeks": horizon_weeks,
            "horizon_days": horizon_days,
            "observation_id": int(entry["observation_id"]),
            "start_timestamp": entry["start_timestamp"],
            "future_timestamp": entry["future_timestamp"],
            "ticker": entry["ticker"],
            "current_price": current_price,
            "future_price": future_price,
            "future_return": future_return,
            "cutoff_weeks": int(cutoff_weeks),
            "progress_percent": progress_percent,
            "progress_share": progress_share,
            **progress_bucket,
            "cutoff_days": cutoff_days,
            "cutoff_timestamp": cutoff_timestamp,
            "entry_score_percentile": entry_score_percentile,
            "mean_score_percentile": mean_score_percentile,
            "score_percentile_change": score_percentile_change,
            "relative_score_percentile_change": (
                relative_score_percentile_change
            ),
            "price_at_cutoff": price_at_cutoff,
            "price_change_to_cutoff": price_change_to_cutoff,
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
            "annualized_return": float(entry["annualized_return"]),
            "benchmark_return": entry.get("benchmark_return"),
            "annualized_benchmark_return": entry.get(
                "annualized_benchmark_return"
            ),
            "annualized_alpha": entry.get("annualized_alpha"),
            "benchmark_observation_count": entry.get(
                "benchmark_observation_count"
            ),
        })

    return rows


def _build_observations_and_paths(
    entries,
    history_lookup,
    market_lookup,
    remaining_benchmark_lookup,
):
    observation_rows = []
    live_progress_rows = []

    for _, entry in entries.iterrows():
        path = _build_path_for_entry(entry, history_lookup)
        if path.empty:
            continue

        observation_rows.append(_summarize_entry_path(entry, path))
        live_progress_rows.extend(
            _summarize_live_progress(
                entry,
                path,
                market_lookup,
                remaining_benchmark_lookup,
            )
        )

    observations = pd.DataFrame(observation_rows)
    return observations, pd.DataFrame(live_progress_rows)
