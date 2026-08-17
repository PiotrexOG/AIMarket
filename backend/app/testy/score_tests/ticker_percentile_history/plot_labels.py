import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import format_horizon_week_range
from .sample_metadata import (
    BASE_OBSERVATION_COUNT_COLUMN,
    horizon_observation_weights,
)


def _format_count(value):
    value = float(value)
    if np.isclose(value, round(value)):
        return str(int(round(value)))
    return f"{value:.1f}".replace(".", ",")


def format_count_range(values):
    clean = pd.to_numeric(pd.Series(values), errors="coerce").replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    clean = clean[clean >= 0]
    if clean.empty:
        return None

    minimum = float(clean.min())
    maximum = float(clean.max())
    if np.isclose(minimum, maximum):
        return _format_count(minimum)
    return f"{_format_count(minimum)}\N{EN DASH}{_format_count(maximum)}"


def company_horizon_sample_note(data):
    required = {"timestamp", "ticker"}
    if data is None or data.empty or not required.issubset(data.columns):
        return None

    clean = data.dropna(subset=list(required)).copy()
    clean["_horizon_observation_weight"] = horizon_observation_weights(clean)
    clean = clean.dropna(subset=["_horizon_observation_weight"])
    if clean.empty:
        return None

    per_date = clean.groupby("timestamp")["_horizon_observation_weight"].sum()
    per_company_date = clean.groupby(
        ["timestamp", "ticker"]
    )["_horizon_observation_weight"].sum()
    date_count = int(clean["timestamp"].nunique())
    return (
        f"n={format_count_range(per_date)} obserwacji bazowych "
        f"spółka\N{MULTIPLICATION SIGN}horyzont na datę startową; "
        f"n={format_count_range(per_company_date)} na datę i spółkę; "
        f"{date_count} dat"
    )


def point_sample_note(
    data,
    direct_count_column,
    *,
    direct_unit,
):
    required = {
        "timestamp",
        BASE_OBSERVATION_COUNT_COLUMN,
        direct_count_column,
    }
    if data is None or data.empty or not required.issubset(data.columns):
        return None

    base_range = format_count_range(data[BASE_OBSERVATION_COUNT_COLUMN])
    direct_range = format_count_range(data[direct_count_column])
    date_count = int(data["timestamp"].dropna().nunique())
    return (
        f"n={base_range} obserwacji bazowych "
        f"spółka\N{MULTIPLICATION SIGN}horyzont na punkt; "
        f"{direct_range} {direct_unit} na punkt; {date_count} dat"
    )


def ticker_sample_note(data):
    required = {"observations", BASE_OBSERVATION_COUNT_COLUMN}
    if data is None or data.empty or not required.issubset(data.columns):
        return None

    return (
        f"n={format_count_range(data[BASE_OBSERVATION_COUNT_COLUMN])} "
        f"obserwacji bazowych data\N{MULTIPLICATION SIGN}horyzont na spółkę; "
        f"T={format_count_range(data['observations'])} dat użytych "
        f"w korelacji na spółkę"
    )


def hac_sample_note(data):
    required = {"observations", BASE_OBSERVATION_COUNT_COLUMN}
    if data is None or data.empty or not required.issubset(data.columns):
        return None

    return (
        f"n={format_count_range(data[BASE_OBSERVATION_COUNT_COLUMN])} "
        f"obserwacji bazowych spółka\N{MULTIPLICATION SIGN}data na punkt; "
        f"T={format_count_range(data['observations'])} dat IC użytych w HAC"
    )


def momentum_window_label(data, start_week, end_week, skip_weeks=0):
    if start_week is None or end_week is None:
        starts = (
            pd.to_numeric(data["horizon_week_start"], errors="coerce").dropna()
            if data is not None and "horizon_week_start" in data.columns
            else pd.Series(dtype="float64")
        )
        ends = (
            pd.to_numeric(data["horizon_week_end"], errors="coerce").dropna()
            if data is not None and "horizon_week_end" in data.columns
            else pd.Series(dtype="float64")
        )
        if not starts.empty and not ends.empty:
            start_week = int(starts.min())
            end_week = int(ends.max())

    if start_week is None or end_week is None:
        label = "skonfigurowany zakres momentum"
    else:
        label = format_horizon_week_range(start_week, end_week)
    if skip_weeks:
        label = f"{label}, pomiń {int(skip_weeks)} tyg."
    return label
