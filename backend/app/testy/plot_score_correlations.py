import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


ROOT_FOLDER = Path(__file__).resolve().parents[2]
CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"

INPUT_FILE = CROSS_SECTION_DIR / "score_vs_returns.json"
OUTPUT_DIR = CROSS_SECTION_DIR / "correlation_plots"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_dataframe(data):
    rows = []

    for timeframe, timeframe_data in data.get("by_timeframe", {}).items():
        for observation in timeframe_data.get("observations", []):
            row = {
                "timeframe": timeframe,
                "ticker": observation["ticker"],
                "start_timestamp": observation["start_timestamp"],
                "future_return": observation["future_return"],
            }

            relative_scores = observation.get("relative_scores")

            if relative_scores:
                row.update(relative_scores)
            elif "score" in observation:
                row[EQUAL_WEIGHT_SCORE_COLUMN] = observation["score"]

            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["start_timestamp"] = pd.to_datetime(df["start_timestamp"])
    df["future_return"] = pd.to_numeric(df["future_return"], errors="coerce")

    score_columns = get_score_columns(df, include_equal_weight=False)

    for column in score_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if score_columns and EQUAL_WEIGHT_SCORE_COLUMN not in df.columns:
        df[EQUAL_WEIGHT_SCORE_COLUMN] = df[score_columns].mean(axis=1)

    if EQUAL_WEIGHT_SCORE_COLUMN in df.columns:
        df[EQUAL_WEIGHT_SCORE_COLUMN] = pd.to_numeric(
            df[EQUAL_WEIGHT_SCORE_COLUMN],
            errors="coerce",
        )

    return df.dropna(subset=["future_return"])


def get_score_columns(df, include_equal_weight=True):
    columns = [
        column
        for column in df.columns
        if column.startswith("relative_")
    ]

    if include_equal_weight and EQUAL_WEIGHT_SCORE_COLUMN in df.columns:
        return [EQUAL_WEIGHT_SCORE_COLUMN] + sorted(columns)

    return sorted(columns)


def safe_name(value):
    return value.replace("/", "_").replace(" ", "_")


def calculate_correlations(group, score_column):
    clean = group[[score_column, "future_return"]].dropna()

    if (
        len(clean) < 3
        or clean[score_column].nunique() < 2
        or clean["future_return"].nunique() < 2
    ):
        return {
            "count": len(clean),
            "pearson": None,
            "pearson_p": None,
            "spearman": None,
            "spearman_p": None,
        }

    pearson_corr, pearson_p = pearsonr(clean[score_column], clean["future_return"])
    spearman_corr, spearman_p = spearmanr(clean[score_column], clean["future_return"])

    return {
        "count": len(clean),
        "pearson": round(float(pearson_corr), 6),
        "pearson_p": round(float(pearson_p), 6),
        "spearman": round(float(spearman_corr), 6),
        "spearman_p": round(float(spearman_p), 6),
    }


def save_summary(df, score_columns):
    rows = []

    for score_column in score_columns:
        for timeframe, group in df.groupby("timeframe"):
            row = {
                "timeframe": timeframe,
                "ticker": "ALL",
                "score_column": score_column,
                "baseline_return": round(float(group["future_return"].mean()), 6),
            }
            row.update(calculate_correlations(group, score_column))
            rows.append(row)

        for (timeframe, ticker), group in df.groupby(["timeframe", "ticker"]):
            row = {
                "timeframe": timeframe,
                "ticker": ticker,
                "score_column": score_column,
                "baseline_return": round(float(group["future_return"].mean()), 6),
            }
            row.update(calculate_correlations(group, score_column))
            rows.append(row)

    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT_DIR / "correlation_summary.csv", index=False)

    return summary


def add_regression_line(ax, group, score_column):
    line = group[[score_column, "future_return"]].dropna()

    if len(line) < 2 or line[score_column].nunique() < 2:
        return

    slope, intercept = np.polyfit(line[score_column], line["future_return"], 1)
    x_min = line[score_column].min()
    x_max = line[score_column].max()
    xs = [x_min, x_max]
    ys = [slope * x + intercept for x in xs]
    ax.plot(xs, ys, color="#d62728", linewidth=2, label="linear fit")


def add_baseline_y(ax, baseline_return):
    ax.axhline(
        baseline_return,
        color="#111111",
        linewidth=2,
        linestyle="--",
        label=f"equal-weight hold baseline: {baseline_return:.2%}",
    )


def add_baseline_x(ax, baseline_return):
    ax.axvline(
        baseline_return,
        color="#111111",
        linewidth=2,
        linestyle="--",
        label=f"equal-weight hold baseline: {baseline_return:.2%}",
    )


def plot_scatter_by_timeframe(df, summary):
    score_column = EQUAL_WEIGHT_SCORE_COLUMN

    if score_column not in df.columns:
        return

    for timeframe, group in df.groupby("timeframe"):
        stats = summary[
            (summary["timeframe"] == timeframe)
            & (summary["ticker"] == "ALL")
            & (summary["score_column"] == score_column)
        ].iloc[0]

        baseline_return = float(group["future_return"].mean())

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(
            group[score_column],
            group["future_return"],
            alpha=0.65,
            s=42,
            edgecolors="none",
        )
        add_regression_line(ax, group, score_column)
        add_baseline_y(ax, baseline_return)

        ax.axhline(0, color="#888888", linewidth=1, linestyle=":")
        ax.set_title(
            f"{timeframe}: equal-weight score vs future return\n"
            f"pearson={stats['pearson']} | spearman={stats['spearman']} | n={stats['count']}"
        )
        ax.set_xlabel("Equal-weight score")
        ax.set_ylabel("Future return")
        ax.grid(True, alpha=0.25)
        ax.legend()

        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"{timeframe}_equal_weight_scatter.png", dpi=160)
        plt.close(fig)


def plot_return_distribution(df):
    for timeframe, group in df.groupby("timeframe"):
        baseline_return = float(group["future_return"].mean())

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(group["future_return"], bins=30, color="#1f77b4", alpha=0.8)
        add_baseline_x(ax, baseline_return)
        ax.axvline(0, color="#444444", linewidth=1, linestyle=":")
        ax.set_title(f"{timeframe}: future return distribution")
        ax.set_xlabel("Future return")
        ax.set_ylabel("Count")
        ax.grid(True, axis="y", alpha=0.25)
        ax.legend()

        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"{timeframe}_return_distribution.png", dpi=160)
        plt.close(fig)


def plot_score_buckets(df, score_columns):
    for score_column in score_columns:
        for timeframe, group in df.groupby("timeframe"):
            clean = group.dropna(subset=[score_column, "future_return"]).copy()

            if clean.empty or clean[score_column].nunique() < 2:
                continue

            baseline_return = float(clean["future_return"].mean())
            clean["score_bucket"] = pd.qcut(
                clean[score_column],
                q=min(5, clean[score_column].nunique()),
                duplicates="drop",
            )
            bucket_summary = (
                clean
                .groupby("score_bucket", observed=True)["future_return"]
                .mean()
                .reset_index()
            )

            if bucket_summary.empty:
                continue

            labels = [str(value) for value in bucket_summary["score_bucket"]]

            fig, ax = plt.subplots(figsize=(11, 6))
            ax.bar(labels, bucket_summary["future_return"], color="#9467bd", alpha=0.85)
            add_baseline_y(ax, baseline_return)
            ax.axhline(0, color="#444444", linewidth=1, linestyle=":")
            ax.set_title(f"{timeframe}: average return by {score_column} bucket")
            ax.set_xlabel(f"{score_column} bucket")
            ax.set_ylabel("Average future return")
            ax.tick_params(axis="x", rotation=25)
            ax.grid(True, axis="y", alpha=0.25)
            ax.legend()

            fig.tight_layout()
            fig.savefig(
                OUTPUT_DIR / f"{timeframe}_{safe_name(score_column)}_score_buckets.png",
                dpi=160,
            )
            plt.close(fig)


def plot_metric_summary(summary):
    all_summary = summary[summary["ticker"] == "ALL"]

    for timeframe, group in all_summary.groupby("timeframe"):
        baseline_return = group["baseline_return"].dropna().iloc[0]
        plot_data = group.dropna(subset=["spearman"])[
            ["score_column", "spearman"]
        ].copy()
        plot_data = pd.concat(
            [
                plot_data,
                pd.DataFrame([{
                    "score_column": "avg_future_return",
                    "spearman": baseline_return,
                }]),
            ],
            ignore_index=True,
        ).sort_values("spearman")

        if plot_data.empty:
            continue

        fig, ax = plt.subplots(figsize=(11, 7))
        colors = [
            "#555555" if row.score_column == "avg_future_return"
            else "#2ca02c" if row.spearman >= 0
            else "#d62728"
            for row in plot_data.itertuples()
        ]
        ax.barh(plot_data["score_column"], plot_data["spearman"], color=colors)
        ax.axvline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: Spearman by score component")
        ax.set_xlabel("Spearman correlation / average future return")
        ax.grid(True, axis="x", alpha=0.25)

        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"{timeframe}_metric_spearman_summary.png", dpi=160)
        plt.close(fig)


def plot_average_metric_values(df):
    metric_columns = get_score_columns(df, include_equal_weight=False)

    if not metric_columns:
        return

    for timeframe, group in df.groupby("timeframe"):
        averages = (
            group[metric_columns]
            .mean()
            .sort_values()
        )

        if averages.empty:
            continue

        fig, ax = plt.subplots(figsize=(11, 7))
        ax.barh(averages.index, averages.values, color="#1f77b4", alpha=0.85)
        ax.set_title(f"{timeframe}: average relative score values")
        ax.set_xlabel("Average metric value")
        ax.set_xlim(0, max(10, float(averages.max()) * 1.05))
        ax.grid(True, axis="x", alpha=0.25)

        for idx, value in enumerate(averages.values):
            ax.text(
                value + 0.05,
                idx,
                f"{value:.2f}",
                va="center",
                fontsize=9,
            )

        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"{timeframe}_average_metric_values.png", dpi=160)
        plt.close(fig)


def plot_ticker_score_timeline(df):
    if EQUAL_WEIGHT_SCORE_COLUMN not in df.columns:
        return

    for ticker, group in df.groupby("ticker"):
        fig, ax = plt.subplots(figsize=(12, 6))

        for timeframe, timeframe_group in group.groupby("timeframe"):
            plot_data = timeframe_group.sort_values("start_timestamp")
            ax.plot(
                plot_data["start_timestamp"],
                plot_data[EQUAL_WEIGHT_SCORE_COLUMN],
                marker="o",
                linewidth=1.7,
                markersize=3,
                label=timeframe,
            )

        ax.set_title(f"{ticker}: equal-weight score over time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Equal-weight score")
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.autofmt_xdate()

        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"{ticker}_score_timeline.png", dpi=160)
        plt.close(fig)


def plot_timeframe_ticker_score_timeline(df):
    if EQUAL_WEIGHT_SCORE_COLUMN not in df.columns:
        return

    for timeframe, group in df.groupby("timeframe"):
        fig, ax = plt.subplots(figsize=(14, 8))

        for ticker, ticker_group in group.groupby("ticker"):
            plot_data = ticker_group.sort_values("start_timestamp")
            ax.plot(
                plot_data["start_timestamp"],
                plot_data[EQUAL_WEIGHT_SCORE_COLUMN],
                linewidth=1.3,
                alpha=0.85,
                label=ticker,
            )

        ax.set_title(f"{timeframe}: equal-weight scores by ticker over time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Equal-weight score")
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.25)
        ax.legend(ncol=3, fontsize=8)
        fig.autofmt_xdate()

        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"{timeframe}_ticker_scores_timeline.png", dpi=160)
        plt.close(fig)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = load_json(INPUT_FILE)
    df = build_dataframe(data)

    if df.empty:
        print("[EMPTY] No observations found.")
        return

    score_columns = get_score_columns(df)

    if not score_columns:
        print("[EMPTY] No score columns found.")
        return

    summary = save_summary(df, score_columns)

    plot_scatter_by_timeframe(df, summary)
    plot_return_distribution(df)
    plot_score_buckets(df, score_columns)
    plot_metric_summary(summary)
    plot_average_metric_values(df)
    plot_ticker_score_timeline(df)
    plot_timeframe_ticker_score_timeline(df)

    print("[OK] Saved plots and summary:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
