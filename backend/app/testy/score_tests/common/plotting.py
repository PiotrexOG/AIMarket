from pathlib import Path

import matplotlib


matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd


TIMEFRAME_HORIZON_LIMITS = {
    "short_term_14d": (7, 21),
    "medium_term_50d": (25, 75),
    "long_term_200d": (100, 300),
}


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def limit_horizon_range(timeframe, df):
    limits = TIMEFRAME_HORIZON_LIMITS.get(timeframe)
    if limits is None:
        return df
    if "horizon_weeks" in df.columns:
        return df
    start_day, end_day = limits
    return df[df["horizon_days"].between(start_day, end_day)]


def horizon_x_column(df):
    return "horizon_weeks" if "horizon_weeks" in df.columns else "horizon_days"


def horizon_x_label(df):
    return (
        "Return horizon in weeks"
        if horizon_x_column(df) == "horizon_weeks"
        else "Return horizon in days"
    )


def _mean_label(label, values, formatter):
    mean_value = values.dropna().mean()
    if mean_value != mean_value:
        return label
    return f"{label} ({formatter(mean_value)})"


def plot_bucket_lines(
    data,
    output_dir,
    plot_type,
    filename,
    title,
    bucket_order,
    show_mean_in_legend=False,
):
    if data.empty:
        return
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.RdYlGn_r(np.linspace(0.05, 0.95, len(bucket_order)))
    x_column = horizon_x_column(data)
    for color, bucket in zip(colors, bucket_order):
        group = data[data["bucket"] == bucket].sort_values(x_column)
        if group.empty:
            continue
        ax.plot(
            group[x_column],
            group["annualized_return"],
            marker="o",
            markevery=max(1, len(group) // 30),
            linewidth=1.8,
            markersize=3,
            color=color,
            label=(
                _mean_label(
                    bucket,
                    group["annualized_return"],
                    lambda value: f"{value:.2%}",
                )
                if show_mean_in_legend
                else bucket
            ),
        )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel(horizon_x_label(data))
    ax.set_ylabel("Annualized return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    ax.legend(
        title="Mean over shown horizons" if show_mean_in_legend else "Bucket",
        ncol=2,
    )
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, plot_type, filename), dpi=160)
    plt.close(fig)


def plot_bucket_average(
    data,
    output_dir,
    plot_type,
    filename,
    title,
    bucket_order,
    score_range_columns=None,
):
    if data.empty:
        return
    aggregations = {"annualized_return": ("annualized_return", "mean")}
    if score_range_columns:
        min_column, max_column = score_range_columns
        aggregations["avg_score_min"] = (min_column, "mean")
        aggregations["avg_score_max"] = (max_column, "mean")

    average = data.groupby("bucket", as_index=False).agg(**aggregations)
    average["bucket"] = pd.Categorical(
        average["bucket"],
        categories=bucket_order,
        ordered=True,
    )
    average = average.sort_values("bucket").dropna(subset=["annualized_return"])
    if average.empty:
        return

    labels = average["bucket"].astype(str)
    if score_range_columns:
        labels = [
            f"{row.bucket}\navg score {row.avg_score_min:.1f}"
            for row in average.itertuples(index=False)
        ]

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar(labels, average["annualized_return"], color="#4C78A8")

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("Bucket")
    ax.set_ylabel("Mean annualized return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, plot_type, filename), dpi=160)
    plt.close(fig)
