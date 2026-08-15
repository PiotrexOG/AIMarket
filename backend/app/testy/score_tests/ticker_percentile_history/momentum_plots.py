from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.plotting import plot_path, timeframe_label
from app.testy.score_tests.common.output_paths import (
    TICKER_ANTI_MOMENTUM_SECTION,
    TICKER_MODEL_VS_MOMENTUM_SECTION,
)

from .momentum_data import (
    _build_anti_momentum_points,
    _ticker_score_correlation_table,
)
from .normalization import (
    _normalized_excess_by_timestamp,
    _rank_percentile_by_group,
    _zscore_by_group,
)
from .plot_config import ANTI_MOMENTUM_WINDOWS
from .plot_io import _safe_filename, _save_figure
from .statistics import _safe_correlation


def _save_ticker_correlation_bar_chart(
    table,
    output_dir,
    directory,
    filename,
    title,
    x_label,
):
    if table.empty or "correlation" not in table.columns:
        return

    clean = table.dropna(subset=["correlation"]).copy()
    if clean.empty:
        return

    save_csv_for_excel(
        table,
        plot_path(output_dir, directory, f"{Path(filename).stem}.csv"),
    )

    y_positions = np.arange(len(clean))
    colors = np.where(clean["correlation"] >= 0, "#59A14F", "#E15759")
    mean_correlation = clean["correlation"].mean()

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(
        y_positions,
        clean["correlation"],
        color=colors,
        alpha=0.9,
    )
    ax.axvline(0, color="#444444", linewidth=1)
    ax.axvline(
        mean_correlation,
        color="#4C78A8",
        linewidth=1.5,
        linestyle="--",
        label=f"Średnia {mean_correlation:.3f}",
    )
    ax.set_xlim(-1, 1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(clean["ticker"])
    ax.set_ylim(len(clean) - 0.5, -0.5)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Ticker")
    ax.grid(True, axis="x", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, filename),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_anti_momentum_correlation_charts(
    data,
    prices,
    ticker_order,
    timeframe,
    directory,
    output_dir,
    horizon_label,
):
    points = _build_anti_momentum_points(data, prices)
    if points.empty:
        return

    anti_momentum_directory = directory / TICKER_ANTI_MOMENTUM_SECTION
    save_csv_for_excel(
        points,
        plot_path(
            output_dir,
            anti_momentum_directory,
            "anti_momentum_points.csv",
        ),
    )

    configs = [
        {
            "value_column": "mean_forward_annualized_return",
            "filename": (
                "score_to_future_annualized_return_correlation_by_ticker.png"
            ),
            "title": (
                f"Korelacja score z przyszłą roczną "
                f"stopą zwrotu według tickerów "
                f"({horizon_label})"
            ),
            "x_label": (
                "Korelacja Pearsona: wynik modelu względem przyszłej "
                "rocznej stopy zwrotu"
            ),
        },
    ]
    for label, start_week, end_week, skip_weeks in ANTI_MOMENTUM_WINDOWS:
        window_label = (
            f"{start_week}-{end_week} tygodni"
        )
        if skip_weeks:
            window_label = f"{window_label}, pomiń {skip_weeks} tyg."
        column = f"trailing_{label}_annualized_return"
        configs.append(
            {
                "value_column": column,
                "filename": (
                    f"score_to_trailing_{label}_return_correlation_by_ticker.png"
                ),
                "title": (
                    f"Korelacja score z momentum Jegadeesha-Titmana "
                    f"według tickerów ({window_label})"

                ),
                "x_label": (
                    "Korelacja Pearsona: wynik modelu względem historycznej "
                    f"rocznej stopy zwrotu ({window_label})"
                ),
            },
        )

    for config in configs:
        table = _ticker_score_correlation_table(
            points,
            ticker_order,
            config["value_column"],
        )
        _save_ticker_correlation_bar_chart(
            table,
            output_dir,
            anti_momentum_directory,
            config["filename"],
            config["title"],
            config["x_label"],
        )


def _build_model_vs_momentum_comparison(points, momentum_column, window_label):
    required = {
        "ticker",
        "timestamp",
        "score",
        momentum_column,
        "mean_forward_annualized_return",
    }
    if points.empty or not required.issubset(points.columns):
        return pd.DataFrame()

    clean = points.dropna(
        subset=[
            "ticker",
            "timestamp",
            "score",
            momentum_column,
            "mean_forward_annualized_return",
        ]
    ).copy()
    if clean.empty:
        return pd.DataFrame()

    clean = _zscore_by_group(
        clean,
        group_column="timestamp",
        value_column="score",
        output_column="model_score_zscore",
    )
    clean = _zscore_by_group(
        clean,
        group_column="timestamp",
        value_column=momentum_column,
        output_column="momentum_zscore",
    )
    clean = _zscore_by_group(
        clean,
        group_column="timestamp",
        value_column="mean_forward_annualized_return",
        output_column="future_return_zscore",
    )
    clean = _rank_percentile_by_group(
        clean,
        group_column="timestamp",
        value_column="score",
        output_column="model_score_percentile",
    )
    clean = _rank_percentile_by_group(
        clean,
        group_column="timestamp",
        value_column=momentum_column,
        output_column="momentum_percentile",
    )
    clean = _rank_percentile_by_group(
        clean,
        group_column="timestamp",
        value_column="mean_forward_annualized_return",
        output_column="future_return_percentile",
    )
    clean["benchmark_annualized_return"] = clean.groupby("timestamp")[
        "mean_forward_annualized_return"
    ].transform("mean")
    clean["future_excess_return"] = (
        clean["mean_forward_annualized_return"]
        - clean["benchmark_annualized_return"]
    )
    clean["model_long_short_weight"] = clean["model_score_percentile"] - 0.5
    clean["momentum_long_short_weight"] = clean["momentum_percentile"] - 0.5
    clean["model_long_only_weight"] = clean["model_long_short_weight"].clip(
        lower=0.0
    )
    clean["momentum_long_only_weight"] = clean[
        "momentum_long_short_weight"
    ].clip(lower=0.0)
    clean["model_long_short_attribution"] = (
        clean["model_long_short_weight"] * clean["future_excess_return"]
    )
    clean["momentum_long_short_attribution"] = (
        clean["momentum_long_short_weight"] * clean["future_excess_return"]
    )
    clean["model_long_only_attribution"] = (
        clean["model_long_only_weight"] * clean["future_excess_return"]
    )
    clean["momentum_long_only_attribution"] = (
        clean["momentum_long_only_weight"] * clean["future_excess_return"]
    )

    model_long_short = _normalized_excess_by_timestamp(
        clean,
        weight_column="model_long_short_weight",
        attribution_column="model_long_short_attribution",
    )
    momentum_long_short = _normalized_excess_by_timestamp(
        clean,
        weight_column="momentum_long_short_weight",
        attribution_column="momentum_long_short_attribution",
    )
    model_long_only = _normalized_excess_by_timestamp(
        clean,
        weight_column="model_long_only_weight",
        attribution_column="model_long_only_attribution",
    )
    momentum_long_only = _normalized_excess_by_timestamp(
        clean,
        weight_column="momentum_long_only_weight",
        attribution_column="momentum_long_only_attribution",
    )

    rows = []
    for timestamp, group in clean.groupby("timestamp", sort=True):
        rows.append({
            "timestamp": timestamp,
            "momentum_window": window_label,
            "ticker_count": group["ticker"].nunique(),
            "model_pearson_ic": _safe_correlation(
                group,
                "model_score_zscore",
                "future_return_zscore",
                "pearson",
            ),
            "momentum_pearson_ic": _safe_correlation(
                group,
                "momentum_zscore",
                "future_return_zscore",
                "pearson",
            ),
            "model_spearman_ic": _safe_correlation(
                group,
                "model_score_percentile",
                "future_return_percentile",
                "spearman",
            ),
            "momentum_spearman_ic": _safe_correlation(
                group,
                "momentum_percentile",
                "future_return_percentile",
                "spearman",
            ),
            "model_long_short_normalized_excess": model_long_short.get(
                timestamp,
                np.nan,
            ),
            "momentum_long_short_normalized_excess": momentum_long_short.get(
                timestamp,
                np.nan,
            ),
            "model_long_only_normalized_excess": model_long_only.get(
                timestamp,
                np.nan,
            ),
            "momentum_long_only_normalized_excess": momentum_long_only.get(
                timestamp,
                np.nan,
            ),
            "benchmark_annualized_return": group[
                "benchmark_annualized_return"
            ].mean(),
        })

    return pd.DataFrame(rows)


def _plot_model_vs_momentum_panel(
    comparison,
    output_dir,
    directory,
    filename,
    title,
):
    if comparison.empty:
        return

    panels = [
        (
            "model_pearson_ic",
            "momentum_pearson_ic",
            "Pearson IC",
            "Korelacja",
            None,
        ),
        (
            "model_spearman_ic",
            "momentum_spearman_ic",
            "Spearman IC",
            "Korelacja",
            None,
        ),
        (
            "model_long_short_normalized_excess",
            "momentum_long_short_normalized_excess",
            "Znormalizowany nadwyżkowy zwrot long-short",
            "Nadwyżkowy zwrot",
            "percent",
        ),
        (
            "model_long_only_normalized_excess",
            "momentum_long_only_normalized_excess",
            "Znormalizowany nadwyżkowy zwrot long-only",
            "Nadwyżkowy zwrot",
            "percent",
        ),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(15, 9), sharex=True)
    for ax, (model_col, momentum_col, panel_title, y_label, fmt) in zip(
        axes.flatten(),
        panels,
    ):
        panel_data = comparison.dropna(subset=[model_col, momentum_col], how="all")
        if panel_data.empty:
            ax.set_visible(False)
            continue

        model_mean = panel_data[model_col].mean()
        momentum_mean = panel_data[momentum_col].mean()
        ax.plot(
            panel_data["timestamp"],
            panel_data[model_col],
            color="#4C78A8",
            linewidth=2,
            marker="o",
            markersize=3,
            label=f"Model, średnia {model_mean:.3f}"
            if fmt is None
            else f"Model, średnia {model_mean:.1%}",
        )
        ax.plot(
            panel_data["timestamp"],
            panel_data[momentum_col],
            color="#F28E2B",
            linewidth=2,
            marker="o",
            markersize=3,
            label=f"Momentum, średnia {momentum_mean:.3f}"
            if fmt is None
            else f"Momentum, średnia {momentum_mean:.1%}",
        )
        ax.axhline(0, color="#444444", linewidth=1)
        if pd.notna(model_mean):
            ax.axhline(
                model_mean,
                color="#4C78A8",
                linewidth=1.2,
                linestyle="--",
                alpha=0.75,
            )
        if pd.notna(momentum_mean):
            ax.axhline(
                momentum_mean,
                color="#F28E2B",
                linewidth=1.2,
                linestyle="--",
                alpha=0.75,
            )
        if fmt == "percent":
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        else:
            ax.set_ylim(-1, 1)
        ax.set_title(panel_title)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best")

    fig.suptitle(title)
    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, filename),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_model_vs_momentum_comparison_charts(
    data,
    prices,
    timeframe,
    directory,
    output_dir,
    horizon_label,
):
    points = _build_anti_momentum_points(data, prices)
    if points.empty:
        return

    comparison_directory = directory / TICKER_MODEL_VS_MOMENTUM_SECTION
    comparisons = []
    for label, start_week, end_week, skip_weeks in ANTI_MOMENTUM_WINDOWS:
        window_label = (
            f"{start_week}-{end_week} tygodni"
        )
        if skip_weeks:
            window_label = f"{window_label}, pomiń {skip_weeks} tyg."
        column = f"trailing_{label}_annualized_return"
        comparison = _build_model_vs_momentum_comparison(
            points,
            momentum_column=column,
            window_label=window_label,
        )
        if comparison.empty:
            continue
        comparisons.append(comparison)
        safe_label = _safe_filename(label)
        save_csv_for_excel(
            comparison,
            plot_path(
                output_dir,
                comparison_directory,
                f"model_vs_momentum_{safe_label}_by_timestamp.csv",
            ),
        )
        _plot_model_vs_momentum_panel(
            comparison,
            output_dir,
            comparison_directory,
            f"model_vs_momentum_{safe_label}_comparison.png",
            (
                f"Model względem momentum według daty scoringu "
                f"(momentum {window_label})"
            ),
        )

    if not comparisons:
        return

    combined = pd.concat(comparisons, ignore_index=True)
    save_csv_for_excel(
        combined,
        plot_path(
            output_dir,
            comparison_directory,
            "model_vs_momentum_all_windows_by_timestamp.csv",
        ),
    )
    summary = (
        combined.groupby("momentum_window", as_index=False)
        .agg(
            model_pearson_ic_mean=("model_pearson_ic", "mean"),
            momentum_pearson_ic_mean=("momentum_pearson_ic", "mean"),
            model_spearman_ic_mean=("model_spearman_ic", "mean"),
            momentum_spearman_ic_mean=("momentum_spearman_ic", "mean"),
            model_long_short_excess_mean=(
                "model_long_short_normalized_excess",
                "mean",
            ),
            momentum_long_short_excess_mean=(
                "momentum_long_short_normalized_excess",
                "mean",
            ),
            model_long_only_excess_mean=(
                "model_long_only_normalized_excess",
                "mean",
            ),
            momentum_long_only_excess_mean=(
                "momentum_long_only_normalized_excess",
                "mean",
            ),
            timestamp_count=("timestamp", "nunique"),
        )
    )
    save_csv_for_excel(
        summary,
        plot_path(
            output_dir,
            comparison_directory,
            "model_vs_momentum_summary.csv",
        ),
    )
