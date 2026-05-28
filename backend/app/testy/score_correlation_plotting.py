import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


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

