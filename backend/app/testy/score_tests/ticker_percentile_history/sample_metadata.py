import pandas as pd


BASE_OBSERVATION_COUNT_COLUMN = "base_observation_count"


def horizon_observation_weights(data):
    if data is None or data.empty:
        return pd.Series(dtype="float64")

    if "horizon_count" in data.columns:
        counts = pd.to_numeric(data["horizon_count"], errors="coerce")
    elif {
        "horizon_week_start",
        "horizon_week_end",
    }.issubset(data.columns):
        starts = pd.to_numeric(data["horizon_week_start"], errors="coerce")
        ends = pd.to_numeric(data["horizon_week_end"], errors="coerce")
        counts = ends - starts + 1
    else:
        counts = pd.Series(1.0, index=data.index)

    return counts.where(counts > 0)


def base_observation_count(data, required_columns=()):
    if data is None or data.empty:
        return 0

    clean = data.dropna(subset=list(required_columns)) if required_columns else data
    weights = horizon_observation_weights(clean).dropna()
    return int(round(float(weights.sum()))) if not weights.empty else 0


def base_observation_counts_by_group(
    data,
    group_column,
    required_columns=(),
):
    if data is None or data.empty or group_column not in data.columns:
        return pd.Series(dtype="int64")

    clean = data.dropna(
        subset=[group_column, *required_columns],
    ).copy()
    if clean.empty:
        return pd.Series(dtype="int64")

    clean["_horizon_observation_weight"] = horizon_observation_weights(clean)
    clean = clean.dropna(subset=["_horizon_observation_weight"])
    return (
        clean.groupby(group_column)["_horizon_observation_weight"]
        .sum()
        .round()
        .astype(int)
    )
