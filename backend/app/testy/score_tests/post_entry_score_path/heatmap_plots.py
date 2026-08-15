import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import plot_path, timeframe_label
from app.testy.score_tests.common.output_paths import (
    POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
)

from .plot_helpers import (
    _entry_min_score_percentile,
    _entry_percentile_bins_and_labels,
    _plot_context_title_label,
    _post_entry_dir,
)


def _plot_score_drop_scatter(
    observations,
    regression_average,
    output_dir,
    horizon_label,
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    )

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "entry_score_percentile",
                "score_percentile_drop",
                "annualized_return",
            ]
        ).copy()
        if clean.empty:
            continue

        fig, ax = plt.subplots(figsize=(13, 8))
        points = ax.scatter(
            clean["score_percentile_drop"],
            clean["annualized_return"],
            c=clean["entry_score_percentile"],
            cmap="viridis",
            vmin=_entry_min_score_percentile(clean),
            vmax=1.0,
            alpha=0.14,
            s=15,
            edgecolors="none",
        )
        colorbar = fig.colorbar(points, ax=ax)
        colorbar.set_label("Percentyl score przy wejściu")
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        bins, labels = _entry_percentile_bins_and_labels(clean)
        clean["entry_percentile_band"] = pd.cut(
            clean["entry_score_percentile"],
            bins=bins,
            labels=labels,
            right=False,
            include_lowest=True,
        )
        colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))
        for label, color in zip(labels, colors):
            band = clean[clean["entry_percentile_band"] == label]
            if len(band) < 3 or band["score_percentile_drop"].nunique() < 2:
                continue
            slope, intercept = np.polyfit(
                band["score_percentile_drop"],
                band["annualized_return"],
                1,
            )
            trend_x = np.linspace(
                band["score_percentile_drop"].quantile(0.02),
                band["score_percentile_drop"].quantile(0.98),
                100,
            )
            ax.plot(
                trend_x,
                slope * trend_x + intercept,
                color=color,
                linewidth=2.2,
                label=f"Wejście {label}",
            )

        regression_text = ""
        if regression_average is not None and not regression_average.empty:
            row = regression_average[
                regression_average["timeframe"] == timeframe
            ]
            if not row.empty:
                row = row.iloc[0]
                coefficient = row.get(
                    "mean_score_percentile_drop_coefficient"
                )
                negative_share = row.get(
                    "score_drop_negative_coefficient_share"
                )
                if pd.notna(coefficient) and pd.notna(negative_share):
                    regression_text = (
                        f"\nśredni współczynnik spadku {coefficient:.2f}; "
                        f"ujemny w {negative_share:.0%} horyzontów"
                    )

        ax.axvline(0, color="#444444", linewidth=1)
        ax.axhline(0, color="#444444", linewidth=1)
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{timeframe_label(timeframe)}: stopa zwrotu względem spadku "
            "percentyla score po wejściu, "
            f"horyzonty {context_label}"
            f"{regression_text}"
        )
        ax.set_xlabel(
            "Spadek percentyla score: percentyl wejścia - średnia w horyzoncie"
        )
        ax.set_ylabel("Roczna stopa zwrotu")
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                f"{timeframe}_score_percentile_drop_scatter.png",
            ),
            dpi=180,
        )
        plt.close(fig)


def _plot_relative_score_change_heatmap(
    observations,
    output_dir,
    horizon_label,
    return_metric="annualized_return",
    return_label="roczna stopa zwrotu",
    filename_prefix="",
):
    plot_directory = _post_entry_dir(
        horizon_label,
        POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    )
    change_bins = [
        -np.inf,
        -0.70,
        -0.60,
        -0.50,
        -0.40,
        -0.30,
        -0.20,
        -0.10,
        0.0,
        0.10,
        0.20,
        0.30,
        np.inf,
    ]
    change_labels = [
        "spadek >70%",
        "spadek 60-70%",
        "spadek 50-60%",
        "spadek 40-50%",
        "spadek 30-40%",
        "spadek 20-30%",
        "spadek 10-20%",
        "spadek 0-10%",
        "poprawa 0-10%",
        "poprawa 10-20%",
        "poprawa 20-30%",
        "poprawa >30%",
    ]

    for timeframe, timeframe_data in observations.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=[
                "entry_score_percentile",
                "relative_score_percentile_change",
                return_metric,
            ]
        ).copy()
        entry_bins, entry_labels = _entry_percentile_bins_and_labels(clean)
        clean["entry_band"] = pd.cut(
            clean["entry_score_percentile"],
            bins=entry_bins,
            labels=entry_labels,
            right=False,
            include_lowest=True,
        )
        clean["change_band"] = pd.cut(
            clean["relative_score_percentile_change"],
            bins=change_bins,
            labels=change_labels,
            right=False,
        )
        clean = clean.dropna(subset=["entry_band", "change_band"])
        if clean.empty:
            continue

        mean_returns = clean.pivot_table(
            index="change_band",
            columns="entry_band",
            values=return_metric,
            aggfunc="mean",
            observed=False,
        ).reindex(index=change_labels, columns=entry_labels)
        counts = clean.pivot_table(
            index="change_band",
            columns="entry_band",
            values=return_metric,
            aggfunc="count",
            observed=False,
        ).reindex(index=change_labels, columns=entry_labels)

        values = mean_returns.to_numpy(dtype=float)
        finite_values = values[np.isfinite(values)]
        if finite_values.size == 0:
            continue
        color_limit = max(
            abs(float(np.nanpercentile(finite_values, 5))),
            abs(float(np.nanpercentile(finite_values, 95))),
        )
        if color_limit == 0:
            color_limit = 1.0

        fig, ax = plt.subplots(figsize=(15, 10))
        image = ax.imshow(
            values,
            cmap="RdYlGn",
            vmin=-color_limit,
            vmax=color_limit,
            aspect="auto",
        )
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label(f"Średnia: {return_label}")
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        for row_index in range(len(change_labels)):
            for column_index in range(len(entry_labels)):
                value = values[row_index, column_index]
                count = counts.iloc[row_index, column_index]
                if not np.isfinite(value) or pd.isna(count) or count == 0:
                    continue
                ax.text(
                    column_index,
                    row_index,
                    f"{value:.0%}\nn={int(count)}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="#111111",
                )

        ax.set_xticks(range(len(entry_labels)))
        ax.set_xticklabels(entry_labels)
        ax.set_yticks(range(len(change_labels)))
        ax.set_yticklabels(change_labels)
        ax.set_xlabel("Percentyl score przy wejściu")
        ax.set_ylabel(
            "Względna zmiana percentyla score"
        )
        context_label = _plot_context_title_label(horizon_label)
        ax.set_title(
            f"{timeframe_label(timeframe)}: średnia wartość metryki "
            f"'{return_label}' według percentyla wejścia i względnej zmiany "
            f"score, horyzonty {context_label}"
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                plot_directory,
                (
                    f"{timeframe}_{filename_prefix}"
                    f"entry_percentile_by_relative_score_change_heatmap.png"
                ),
            ),
            dpi=180,
        )
        plt.close(fig)
