import json

import pandas as pd


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_score_columns(df, equal_weight_score_column, include_equal_weight=True):
    columns = [
        column
        for column in df.columns
        if column.startswith("relative_")
    ]

    if include_equal_weight and equal_weight_score_column in df.columns:
        return [equal_weight_score_column] + sorted(columns)

    return sorted(columns)


def build_dataframe(data, equal_weight_score_column):
    rows = []

    for timeframe, timeframe_data in data.get("by_timeframe", {}).items():
        for observation in timeframe_data.get("observations", []):
            row = {
                "timeframe": timeframe,
                "ticker": observation["ticker"],
                "start_timestamp": observation["start_timestamp"],
            }

            if "future_return" in observation:
                row["future_return"] = observation["future_return"]

            relative_scores = observation.get("relative_scores")

            if relative_scores:
                row.update(relative_scores)
            elif "score" in observation:
                row[equal_weight_score_column] = observation["score"]

            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["start_timestamp"] = pd.to_datetime(df["start_timestamp"])

    if "future_return" in df.columns:
        df["future_return"] = pd.to_numeric(df["future_return"], errors="coerce")

    score_columns = get_score_columns(
        df,
        equal_weight_score_column,
        include_equal_weight=False,
    )

    for column in score_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if score_columns and equal_weight_score_column not in df.columns:
        df[equal_weight_score_column] = df[score_columns].mean(axis=1)

    if equal_weight_score_column in df.columns:
        df[equal_weight_score_column] = pd.to_numeric(
            df[equal_weight_score_column],
            errors="coerce",
        )

    return df.dropna(subset=["ticker", "start_timestamp"])
