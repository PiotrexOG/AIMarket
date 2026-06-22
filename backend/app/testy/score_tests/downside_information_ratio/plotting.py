from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from app.testy.score_tests.common.plotting import plot_path


def plot(analysis, output_dir, horizon_label):
    if analysis.empty:
        return
    for timeframe, timeframe_data in analysis.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=["top_percent", "downside_information_ratio"]
        ).sort_values("top_percent")
        if clean.empty:
            continue

        plot_directory = Path("downside_information_ratio") / horizon_label
        _plot_returns(clean, timeframe, output_dir, plot_directory, horizon_label)
        _plot_deviation(clean, timeframe, output_dir, plot_directory, horizon_label)
        _plot_ratio(clean, timeframe, output_dir, plot_directory, horizon_label)


def _plot_returns(data, timeframe, output_dir, directory, horizon_label):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["mean_annualized_strategy_return"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
        label="Top M strategy",
    )
    ax.plot(
        data["top_percent"],
        data["mean_annualized_benchmark_return"],
        marker="o",
        linewidth=2,
        color="#9C755F",
        label="Top 100% benchmark",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{timeframe}: mean annualized return by Top M, "
        f"equal-weight horizons {horizon_label}"
    )
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Mean annualized return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_mean_annualized_return.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_deviation(data, timeframe, output_dir, directory, horizon_label):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_deviation"],
        marker="o",
        linewidth=2,
        color="#E15759",
    )
    ax.set_title(
        f"{timeframe}: mean downside deviation by Top M, "
        f"equal-weight horizons {horizon_label}"
    )
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Mean downside deviation")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_mean_downside_deviation.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_ratio(data, timeframe, output_dir, directory, horizon_label):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_information_ratio"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
        label="Downside information ratio",
    )
    plateau = data[data["is_stability_plateau"]]
    if not plateau.empty:
        ax.scatter(
            plateau["top_percent"],
            plateau["downside_information_ratio"],
            s=90,
            facecolors="none",
            edgecolors="#F28E2B",
            linewidths=2,
            label="Stability plateau",
        )
    recommendation = data[data["is_stable_recommendation"]]
    if not recommendation.empty:
        point = recommendation.iloc[0]
        ax.scatter(
            [point["top_percent"]],
            [point["downside_information_ratio"]],
            marker="*",
            s=220,
            color="#59A14F",
            label=f"Stable recommendation: {point['top_percent']:.2f}%",
        )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{timeframe}: downside information ratio by Top M, "
        f"equal-weight horizons {horizon_label}"
    )
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Downside information ratio")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        plot_path(
            output_dir,
            directory,
            f"{timeframe}_downside_information_ratio.png",
        ),
        dpi=160,
    )
    plt.close(fig)
