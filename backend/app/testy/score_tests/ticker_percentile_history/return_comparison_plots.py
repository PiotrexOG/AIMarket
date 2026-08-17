import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    plot_path,
    timeframe_label,
)

from .plot_io import _save_figure
from .plot_labels import company_horizon_sample_note
from .sample_metadata import (
    BASE_OBSERVATION_COUNT_COLUMN,
    base_observation_counts_by_group,
)


def _save_normalized_excess_comparison_plot(
    data,
    timeframe,
    directory,
    output_dir,
    long_short_normalized_excess,
    long_only_normalized_excess,
):
    benchmark = (
        data.groupby("timestamp")["mean_forward_annualized_return"]
        .mean()
        .sort_index()
    )
    if benchmark.empty:
        return

    horizon_label = timeframe_label(timeframe, data)

    benchmark_std = benchmark.std(ddof=0)
    if pd.notna(benchmark_std) and not np.isclose(benchmark_std, 0):
        benchmark_zscore = (benchmark - benchmark.mean()) / benchmark_std
    else:
        benchmark_zscore = pd.Series(0.0, index=benchmark.index)

    comparison = pd.DataFrame({
        "timestamp": benchmark.index,
        "long_short_normalized_excess": long_short_normalized_excess.reindex(
            benchmark.index
        ).to_numpy(),
        "long_only_normalized_excess": long_only_normalized_excess.reindex(
            benchmark.index
        ).to_numpy(),
        "benchmark_annualized_return": benchmark.to_numpy(),
        "benchmark_zscore": benchmark_zscore.to_numpy(),
        "observation_count": data.groupby("timestamp").size().reindex(
            benchmark.index
        ).to_numpy(),
    })
    base_counts = base_observation_counts_by_group(
        data,
        "timestamp",
        required_columns=(
            "mean_forward_annualized_return",
        ),
    )
    comparison[BASE_OBSERVATION_COUNT_COLUMN] = (
        comparison["timestamp"].map(base_counts)
    )
    comparison = comparison.dropna(
        subset=["long_short_normalized_excess", "long_only_normalized_excess"],
        how="all",
    )
    if comparison.empty:
        return

    save_csv_for_excel(
        comparison,
        plot_path(
            output_dir,
            directory,
            "normalized_excess_attribution_by_timestamp.csv",
        ),
    )

    fig, ax = plt.subplots(figsize=(13.5, 6.2))
    benchmark_ax = ax.twinx()
    benchmark_ax.plot(
        comparison["timestamp"],
        comparison["benchmark_zscore"],
        color="#777777",
        linewidth=2,
        linestyle=":",
        marker="s",
        markersize=3,
        alpha=0.85,
        label="Wynik standaryzowany zwrotu benchmarku",
    )
    benchmark_ax.fill_between(
        comparison["timestamp"],
        0,
        comparison["benchmark_zscore"],
        color="#777777",
        alpha=0.08,
    )
    ax.plot(
        comparison["timestamp"],
        comparison["long_short_normalized_excess"],
        color="#4C78A8",
        linewidth=2.3,
        marker="o",
        markersize=3.5,
        label="Znormalizowany nadwyżkowy zwrot long-short",
    )
    ax.plot(
        comparison["timestamp"],
        comparison["long_only_normalized_excess"],
        color="#F28E2B",
        linewidth=2.3,
        marker="o",
        markersize=3.5,
        label="Znormalizowany nadwyżkowy zwrot long-only",
    )

    long_short_mean = comparison["long_short_normalized_excess"].mean()
    long_only_mean = comparison["long_only_normalized_excess"].mean()
    ax.axhline(0, color="#444444", linewidth=1)
    if pd.notna(long_short_mean):
        ax.axhline(
            long_short_mean,
            color="#4C78A8",
            linewidth=1.5,
            linestyle="--",
            alpha=0.8,
            label=f"Średnia long-short {long_short_mean:.1%}",
        )
    if pd.notna(long_only_mean):
        ax.axhline(
            long_only_mean,
            color="#F28E2B",
            linewidth=1.5,
            linestyle="--",
            alpha=0.8,
            label=f"Średnia long-only {long_only_mean:.1%}",
        )
    benchmark_ax.axhline(0, color="#777777", linewidth=0.9, linestyle=":", alpha=0.7)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_title(
        f"Atrybucja znormalizowanego nadwyżkowego zwrotu według daty scoringu "
        f"({horizon_label})"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_ylabel("Znormalizowany nadwyżkowy zwrot")
    benchmark_ax.set_ylabel("Wynik standaryzowany zwrotu benchmarku")
    benchmark_limit = comparison["benchmark_zscore"].abs().max()
    if pd.notna(benchmark_limit) and benchmark_limit > 0:
        benchmark_ax.set_ylim(
            -max(1.0, float(benchmark_limit) * 1.1),
            max(1.0, float(benchmark_limit) * 1.1),
        )
    ax.grid(True, alpha=0.25)
    handles, labels = ax.get_legend_handles_labels()
    benchmark_handles, benchmark_labels = benchmark_ax.get_legend_handles_labels()
    ax.legend(
        handles + benchmark_handles,
        labels + benchmark_labels,
        loc="best",
    )

    add_sample_size_note(
        fig,
        note=company_horizon_sample_note(
            data[
                data["timestamp"].isin(comparison["timestamp"])
            ].dropna(subset=["mean_forward_annualized_return"]),
        ),
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "normalized_excess_attribution_by_timestamp.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)
