import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def safe_name(value):
    return value.replace("/", "_").replace(" ", "_")


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


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


def plot_scatter_by_timeframe(df, summary, output_dir, score_column):
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
        fig.savefig(
            plot_path(output_dir, "scatter", f"{timeframe}_equal_weight_scatter.png"),
            dpi=160,
        )
        plt.close(fig)


def plot_return_distribution(df, output_dir):
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
        fig.savefig(
            plot_path(output_dir, "return_distribution", f"{timeframe}_return_distribution.png"),
            dpi=160,
        )
        plt.close(fig)


def plot_score_buckets(df, score_columns, output_dir):
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
                plot_path(
                    output_dir,
                    "score_buckets",
                    f"{timeframe}_{safe_name(score_column)}_score_buckets.png",
                ),
                dpi=160,
            )
            plt.close(fig)


def plot_metric_summary(summary, output_dir):
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
        fig.savefig(
            plot_path(output_dir, "metric_summary", f"{timeframe}_metric_spearman_summary.png"),
            dpi=160,
        )
        plt.close(fig)


def plot_average_metric_values(df, output_dir, metric_columns):
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
        fig.savefig(
            plot_path(output_dir, "average_metric_values", f"{timeframe}_average_metric_values.png"),
            dpi=160,
        )
        plt.close(fig)


def plot_ticker_score_timeline(df, output_dir, score_column):
    if score_column not in df.columns:
        return

    for ticker, group in df.groupby("ticker"):
        fig, ax = plt.subplots(figsize=(12, 6))

        for timeframe, timeframe_group in group.groupby("timeframe"):
            plot_data = timeframe_group.sort_values("start_timestamp")
            ax.plot(
                plot_data["start_timestamp"],
                plot_data[score_column],
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
        fig.savefig(
            plot_path(output_dir, "ticker_score_timeline", f"{ticker}_score_timeline.png"),
            dpi=160,
        )
        plt.close(fig)


def plot_timeframe_ticker_score_timeline(df, output_dir, score_column):
    if score_column not in df.columns:
        return

    for timeframe, group in df.groupby("timeframe"):
        fig, ax = plt.subplots(figsize=(14, 8))

        for ticker, ticker_group in group.groupby("ticker"):
            plot_data = ticker_group.sort_values("start_timestamp")
            ax.plot(
                plot_data["start_timestamp"],
                plot_data[score_column],
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
        fig.savefig(
            plot_path(
                output_dir,
                "timeframe_ticker_score_timeline",
                f"{timeframe}_ticker_scores_timeline.png",
            ),
            dpi=160,
        )
        plt.close(fig)


def plot_horizon_pearson(horizon_summary, output_dir):
    if horizon_summary.empty:
        return

    plot_data = horizon_summary.dropna(subset=["pearson"]).copy()

    if plot_data.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 7))

    for timeframe, group in plot_data.groupby("timeframe"):
        group = group.sort_values("horizon_days")
        markevery = max(1, len(group) // 30)
        ax.plot(
            group["horizon_days"],
            group["pearson"],
            marker="o",
            markevery=markevery,
            linewidth=1.8,
            markersize=3.5,
            label=timeframe,
        )

        best = group.loc[group["pearson"].idxmax()]
        ax.scatter(
            [best["horizon_days"]],
            [best["pearson"]],
            s=75,
            zorder=4,
        )
        ax.annotate(
            f"{int(best['horizon_days'])}d: {best['pearson']:.3f}",
            xy=(best["horizon_days"], best["pearson"]),
            xytext=(6, 8),
            textcoords="offset points",
            fontsize=9,
        )

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title("Pearson correlation by return horizon")
    ax.set_xlabel("Return horizon in days")
    ax.set_ylabel("Pearson correlation")
    ax.grid(True, alpha=0.25)
    ax.legend()

    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, "horizon_pearson", "pearson_by_horizon_days.png"),
        dpi=160,
    )
    plt.close(fig)

    for timeframe, group in plot_data.groupby("timeframe"):
        group = group.sort_values("horizon_days")
        markevery = max(1, len(group) // 30)

        fig, ax = plt.subplots(figsize=(11, 6))
        ax.plot(
            group["horizon_days"],
            group["pearson"],
            marker="o",
            markevery=markevery,
            linewidth=1.8,
            markersize=3.5,
            color="#1f77b4",
        )
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: Pearson correlation by return horizon")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Pearson correlation")
        ax.grid(True, alpha=0.25)

        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "horizon_pearson",
                f"{timeframe}_pearson_by_horizon_days.png",
            ),
            dpi=160,
        )
        plt.close(fig)


def plot_horizon_quantile_pearson(quantile_summary, output_dir):
    if quantile_summary.empty:
        return

    plot_data = quantile_summary.dropna(subset=["pearson"]).copy()

    if plot_data.empty:
        return

    for timeframe, timeframe_group in plot_data.groupby("timeframe"):
        fig, ax = plt.subplots(figsize=(12, 7))

        for top_percent, group in timeframe_group.groupby("top_percent"):
            group = group.sort_values("horizon_days")
            markevery = max(1, len(group) // 30)
            ax.plot(
                group["horizon_days"],
                group["pearson"],
                marker="o",
                markevery=markevery,
                linewidth=1.7,
                markersize=3,
                label=f"top {int(top_percent)}%",
            )

            best = group.loc[group["pearson"].idxmax()]
            ax.scatter(
                [best["horizon_days"]],
                [best["pearson"]],
                s=55,
                zorder=4,
            )

        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: Pearson by return horizon and score threshold")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Pearson correlation inside selected top-score group")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Score threshold")

        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "horizon_quantile_pearson",
                f"{timeframe}_pearson_by_horizon_and_top_score_share.png",
            ),
            dpi=160,
        )
        plt.close(fig)

