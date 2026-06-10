import json

import pandas as pd


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_relative_score_columns(df):
    return [
        column
        for column in df.columns
        if column.startswith("relative_")
    ]


def build_dataframe(data, equal_weight_score_column):
    rows = []

    for timeframe, timeframe_data in data.get("by_timeframe", {}).items():
        for observation in timeframe_data.get("observations", []):
            row = {
                "timeframe": timeframe,
                "ticker": observation["ticker"],
                "start_timestamp": observation["start_timestamp"],
            }

            relative_scores = observation.get("relative_scores")

            if relative_scores:
                row.update(relative_scores)

            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["start_timestamp"] = pd.to_datetime(df["start_timestamp"])

    score_columns = sorted(get_relative_score_columns(df))

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
