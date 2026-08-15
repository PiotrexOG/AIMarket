import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.plotting import plot_path, timeframe_label

from .hac_plots import _save_score_return_hac_diagnostics
from .plot_io import _save_figure
from .statistics import _safe_correlation


def _save_score_return_correlation_by_timestamp_plot(
    data,
    timeframe_forward_return_horizons,
    timeframe,
    directory,
    output_dir,
):
    required = {
        "timestamp",
        "score_zscore",
        "forward_return_zscore",
        "score_percentile",
        "forward_return_percentile",
        "mean_forward_annualized_return",
        "excess_forward_annualized_return",
    }
    if data.empty or not required.issubset(data.columns):
        return

    rows = []
    for timestamp, group in data.groupby("timestamp", sort=True):
        pearson = _safe_correlation(
            group,
            "score_zscore",
            "forward_return_zscore",
            "pearson",
        )
        spearman = _safe_correlation(
            group,
            "score_percentile",
            "forward_return_percentile",
            "spearman",
        )
        score_percentile_pearson = _safe_correlation(
            group,
            "score_percentile",
            "excess_forward_annualized_return",
            "pearson",
        )
        benchmark_return = group["mean_forward_annualized_return"].mean()
        rows.append({
            "timestamp": timestamp,
            "pearson": pearson,
            "spearman": spearman,
            "score_percentile_pearson_ic": score_percentile_pearson,
            "benchmark_annualized_return": benchmark_return,
        })

    correlations = pd.DataFrame(rows).dropna(subset=["pearson", "spearman"])
    if correlations.empty:
        return

    pearson_mean = float(correlations["pearson"].mean())
    spearman_mean = float(correlations["spearman"].mean())
    score_percentile_pearson_mean = float(
        correlations["score_percentile_pearson_ic"].mean()
    )
    benchmark_std = correlations["benchmark_annualized_return"].std(ddof=0)
    if pd.notna(benchmark_std) and not np.isclose(benchmark_std, 0):
        correlations["benchmark_zscore"] = (
            correlations["benchmark_annualized_return"]
            - correlations["benchmark_annualized_return"].mean()
        ) / benchmark_std
    else:
        correlations["benchmark_zscore"] = 0.0
    save_csv_for_excel(
        correlations,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_by_timestamp.csv",
        ),
    )
    _save_score_return_hac_diagnostics(
        correlations,
        data,
        timeframe,
        directory,
        output_dir,
        horizon_points=timeframe_forward_return_horizons,
    )

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(
        correlations["timestamp"],
        correlations["pearson"],
        color="#4C78A8",
        linewidth=2,
        marker="o",
        markersize=3,
        label=f"Pearson, średnia {pearson_mean:.3f}",
    )
    ax.plot(
        correlations["timestamp"],
        correlations["spearman"],
        color="#59A14F",
        linewidth=2,
        marker="o",
        markersize=3,
        label=f"Spearman, średnia {spearman_mean:.3f}",
    )
    ax.plot(
        correlations["timestamp"],
        correlations["score_percentile_pearson_ic"],
        color="#F28E2B",
        linewidth=1.8,
        marker="o",
        markersize=2.8,
        label=(
            f"Pearson IC percentyla score, "
            f"średnia {score_percentile_pearson_mean:.3f}"
        ),
    )
    benchmark_ax = ax.twinx()
    benchmark_ax.plot(
        correlations["timestamp"],
        correlations["benchmark_zscore"],
        color="#777777",
        linewidth=1.8,
        linestyle=":",
        marker="s",
        markersize=2.8,
        alpha=0.9,
        label="Wynik standaryzowany zwrotu benchmarku",
    )
    benchmark_ax.axhline(0, color="#777777", linewidth=0.9, linestyle=":", alpha=0.7)
    ax.axhline(0, color="#444444", linewidth=1)
    ax.axhline(
        pearson_mean,
        color="#4C78A8",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
    )
    ax.axhline(
        spearman_mean,
        color="#59A14F",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
    )
    ax.axhline(
        score_percentile_pearson_mean,
        color="#F28E2B",
        linewidth=1.2,
        linestyle="--",
        alpha=0.75,
    )
    ax.set_ylim(-1, 1)
    ax.set_title(
        f"Korelacja score z przyszłą stopą zwrotu według daty scoringu "
        f"({timeframe_label(timeframe)}; średnia Pearson {pearson_mean:.3f}, "
        f"średnia Spearman {spearman_mean:.3f}, "
        f"średnia Pearson IC percentyla score "
        f"{score_percentile_pearson_mean:.3f})"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_ylabel("Korelacja przekrojowa")
    benchmark_ax.set_ylabel("Wynik standaryzowany zwrotu benchmarku")
    benchmark_limit = correlations["benchmark_zscore"].abs().max()
    if pd.notna(benchmark_limit) and benchmark_limit > 0:
        benchmark_limit = max(1.0, float(benchmark_limit) * 1.1)
        benchmark_ax.set_ylim(-benchmark_limit, benchmark_limit)
    ax.grid(True, alpha=0.25)
    handles, labels = ax.get_legend_handles_labels()
    benchmark_handles, benchmark_labels = benchmark_ax.get_legend_handles_labels()
    ax.legend(
        handles + benchmark_handles,
        labels + benchmark_labels,
        loc="best",
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_by_timestamp.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_forward_return_cross_section_correlation_plot(
    timeframe_forward_returns,
    timeframe,
    directory,
    output_dir,
):
    pearson_column = "cross_section_pearson_score_to_forward_percentile"
    spearman_column = "cross_section_spearman_score_to_forward_percentile"
    required = {"timestamp", pearson_column, spearman_column}
    if timeframe_forward_returns.empty or not required.issubset(
        timeframe_forward_returns.columns
    ):
        return

    correlations = (
        timeframe_forward_returns[list(required)]
        .drop_duplicates("timestamp")
        .dropna(subset=[pearson_column, spearman_column])
        .sort_values("timestamp")
    )
    if correlations.empty:
        return

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(
        correlations["timestamp"],
        correlations[pearson_column],
        color="#4C78A8",
        linewidth=2,
        marker="o",
        markersize=3,
        label="Pearson",
    )
    ax.plot(
        correlations["timestamp"],
        correlations[spearman_column],
        color="#59A14F",
        linewidth=2,
        marker="o",
        markersize=3,
        label="Spearman",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.axhline(
        correlations[pearson_column].mean(),
        color="#4C78A8",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
        label="Średnia Pearsona",
    )
    ax.axhline(
        correlations[spearman_column].mean(),
        color="#59A14F",
        linewidth=1.4,
        linestyle="--",
        alpha=0.8,
        label="Średnia Spearmana",
    )
    ax.set_ylim(-1, 1)
    ax.set_title(
        f"Korelacja percentyla score z percentylem przyszłej stopy "
        f"zwrotu ({timeframe_label(timeframe)})"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_ylabel("Korelacja przekrojowa")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "score_percentile_to_forward_return_percentile_correlation.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_raw_score_forward_return_correlation_plot(
    timeframe_forward_returns,
    timeframe,
    directory,
    output_dir,
):
    required = {"ticker", "score", "mean_forward_annualized_return"}
    if timeframe_forward_returns.empty or not required.issubset(
        timeframe_forward_returns.columns
    ):
        return

    data = timeframe_forward_returns.dropna(
        subset=["ticker", "score", "mean_forward_annualized_return"]
    ).copy()
    if data.empty:
        return

    correlations = pd.DataFrame({
        "pearson": data.groupby("ticker").apply(
            _safe_correlation,
            x_column="score",
            y_column="mean_forward_annualized_return",
            method="pearson",
        ),
        "spearman": data.groupby("ticker").apply(
            _safe_correlation,
            x_column="score",
            y_column="mean_forward_annualized_return",
            method="spearman",
        ),
    }).dropna(how="all")
    if correlations.empty:
        return

    correlations["sort_value"] = correlations[["pearson", "spearman"]].mean(axis=1)
    correlations = correlations.sort_values("sort_value", ascending=False)

    y_positions = np.arange(len(correlations.index))
    fig, (pearson_ax, spearman_ax) = plt.subplots(
        1,
        2,
        figsize=(10, 8),
        sharey=True,
    )
    for ax, column, title in [
        (pearson_ax, "pearson", "Pearson"),
        (spearman_ax, "spearman", "Spearman"),
    ]:
        values = correlations[column]
        colors = np.where(values >= 0, "#59A14F", "#E15759")
        ax.barh(y_positions, values, color=colors, alpha=0.9)
        ax.axvline(0, color="#444444", linewidth=1)
        ax.set_xlim(-1, 1)
        ax.set_title(title)
        ax.set_xlabel("Korelacja")
        ax.grid(True, axis="x", alpha=0.25)
        ax.set_ylim(len(correlations.index) - 0.5, -0.5)

    pearson_ax.set_yticks(y_positions)
    pearson_ax.set_yticklabels(correlations.index)
    pearson_ax.set_ylabel("Ticker")
    spearman_ax.tick_params(axis="y", left=False, labelleft=False)
    fig.suptitle(
        f"Korelacja surowego score ze średnią przyszłą "
        f"roczną stopą zwrotu ({timeframe_label(timeframe)})"
    )
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "raw_score_to_forward_annualized_return_correlation_by_ticker.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)
