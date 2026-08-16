import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    label_with_sample_size,
    plot_path,
    timeframe_label,
)

from .plot_config import HAC_DIAGNOSTIC_METRICS
from .plot_io import _save_figure
from .statistics import (
    _metric_horizon_summary,
    _metric_official_summary,
    _official_result_mask,
    _score_return_horizon_correlations,
    _score_return_horizon_hac_summary,
)


def _save_score_return_hac_summary_plot(summary, timeframe, directory, output_dir):
    horizon_summary = summary[~_official_result_mask(summary)].dropna(
        subset=["horizon_weeks"]
    )
    if horizon_summary.empty:
        return

    x_values = np.sort(horizon_summary["horizon_weeks"].unique().astype(float))
    x_min = float(x_values.min())
    x_max = float(x_values.max())

    fig, ax = plt.subplots(figsize=(13, 6.8))
    official_annotations = []
    for config in HAC_DIAGNOSTIC_METRICS:
        metric_summary = _metric_horizon_summary(summary, config["metric"])
        if metric_summary.empty:
            continue

        yerr = [
            (
                metric_summary["mean_ic"]
                - metric_summary["ci_lower_95"]
            ).clip(lower=0),
            (
                metric_summary["ci_upper_95"]
                - metric_summary["mean_ic"]
            ).clip(lower=0),
        ]
        ax.errorbar(
            metric_summary["horizon_weeks"],
            metric_summary["mean_ic"],
            yerr=yerr,
            color=config["color"],
            ecolor=config["color"],
            elinewidth=1.1,
            alpha=0.92,
            linewidth=2,
            marker="o",
            markersize=4,
            capsize=3,
            label=label_with_sample_size(
                f"{config['label']} według horyzontu",
                metric_summary,
                "observations",
            ),
        )

        official = _metric_official_summary(summary, config["metric"])
        if official is None:
            continue
        ax.axhline(
            official["mean_ic"],
            color=config["color"],
            linewidth=1.5,
            linestyle="--",
            alpha=0.85,
        )
        if (
            pd.notna(official["ci_lower_95"])
            and pd.notna(official["ci_upper_95"])
        ):
            ax.fill_between(
                [x_min, x_max],
                official["ci_lower_95"],
                official["ci_upper_95"],
                color=config["color"],
                alpha=0.08,
            )
            official_annotations.append(
                f"{config['short_label']}: średnia oficjalna "
                f"{official['mean_ic']:.3f}, 95% przedział "
                f"[{official['ci_lower_95']:.3f}, "
                f"{official['ci_upper_95']:.3f}]"
                f", n={int(official['observations'])}"
            )

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_ylim(0, 0.5)
    ax.set_xticks(x_values)
    ax.set_xticklabels([str(int(value)).replace("w", "") for value in x_values])
    ax.set_title(
        f"IC score względem przyszłej stopy zwrotu oraz "
        f"przedziały HAC według horyzontu "
        f"({timeframe_label(timeframe, horizon_summary)})"
    )
    ax.set_xlabel("Horyzont przyszłej stopy zwrotu [tygodnie]")
    ax.set_ylabel("Średni IC")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    if official_annotations:
        ax.text(
            0.99,
            0.98,
            "\n".join(official_annotations),
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": "#DDDDDD",
                "alpha": 0.96,
            },
        )

    add_sample_size_note(
        fig,
        horizon_summary,
        "observations",
        per="punkt (miara IC i horyzont; liczba dat)",
    )

    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_hac_diagnostics.png",
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)



def _format_ci_half_width_clean(val):
    """Pomocnicza funkcja formatująca precyzję do 2 miejsc po przecinku bez symboli +/-."""
    if val is None or np.isnan(val):
        return "n/a"
    try:
        val_float = float(val)
        return f"{val_float:.2f}"
    except (ValueError, TypeError):
        return "n/a"


import matplotlib.pyplot as plt
import numpy as np


def _format_ci_half_width_clean(val):
    """Pomocnicza funkcja formatująca precyzję do 2 miejsc po przecinku bez symboli +/-."""
    if val is None or np.isnan(val):
        return "n/a"
    try:
        val_float = float(val * 1.96)
        return f"{val_float:.3f}"
    except (ValueError, TypeError):
        return "n/a"


def _save_score_return_autocorrelation_plot(
    autocorrelations,
    summary,
    timeframe,
    directory,
    output_dir,
    config,
):
    metric_acf = autocorrelations[
        autocorrelations["metric"] == config["metric"]
    ]
    if metric_acf.empty:
        return

    heatmap = (
        metric_acf.pivot_table(
            index="lag",
            columns="horizon_weeks",
            values="autocorrelation",
            aggfunc="mean",
        )
        .sort_index()
        .sort_index(axis=1)
    )
    if heatmap.empty:
        return
    count_heatmap = (
        metric_acf.pivot_table(
            index="lag",
            columns="horizon_weeks",
            values="observations",
            aggfunc="max",
        )
        .reindex(index=heatmap.index, columns=heatmap.columns)
    )

    metric_summary = _metric_horizon_summary(summary, config["metric"])
    summary_by_horizon = {}
    if not metric_summary.empty:
        for row in metric_summary.itertuples(index=False):
            summary_by_horizon[int(round(float(row.horizon_weeks)))] = row

    horizons = [int(round(float(h))) for h in heatmap.columns]

    se_values = []
    hac_values = []

    for horizon in horizons:
        stats = summary_by_horizon.get(horizon)
        if stats is None:
            se_values.append("n/a")
            hac_values.append("n/a")
        else:
            se_values.append(
                _format_ci_half_width_clean(
                    getattr(stats, "naive_standard_error", None)
                )
            )
            hac_values.append(
                _format_ci_half_width_clean(
                    getattr(stats, "newey_west_standard_error", None)
                )
            )

    fig_width = max(12, len(horizons) * 0.85)
    fig_height = max(7, min(10, 5.0 + len(heatmap.index) * 0.08))

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    image = ax.imshow(
        heatmap.to_numpy(dtype=float),
        aspect="auto",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        origin="lower",
    )
    for row_index in range(len(heatmap.index)):
        for column_index in range(len(heatmap.columns)):
            count = count_heatmap.iloc[row_index, column_index]
            if pd.isna(count):
                continue
            ax.text(
                column_index,
                row_index,
                f"n={int(count)}",
                ha="center",
                va="center",
                fontsize=5.5,
                color="#222222",
            )

    # 1. Przewracamy standardowe podpisanie osi X (horyzonty)
    ax.set_xticks(np.arange(len(horizons)))
    ax.set_xticklabels(
        [f"{h}w" for h in horizons],
        fontsize=9,
    )
    # 2. Standardowy opis osi X
    ax.set_xlabel(
        "Horyzont przyszłej stopy zwrotu [tygodnie]",
        fontsize=10,
        labelpad=8,
    )

    # Pozycjonowanie osi Y
    y_tick_step = max(1, int(np.ceil(len(heatmap.index) / 14)))
    y_tick_positions = np.arange(0, len(heatmap.index), y_tick_step)

    if y_tick_positions[-1] != len(heatmap.index) - 1:
        y_tick_positions = np.append(
            y_tick_positions,
            len(heatmap.index) - 1,
        )

    ax.set_yticks(y_tick_positions)
    ax.set_yticklabels([
        str(int(heatmap.index[position])) for position in y_tick_positions
    ])

    # Colorbar
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Autokorelacja", fontsize=10)

    # Opisy osi Y i tytuł
    ax.set_ylabel("Opóźnienie", fontsize=10)
    ax.set_title(
        f"Autokorelacja {config['label']} według horyzontu i opóźnienia "
        f"({timeframe_label(timeframe, metric_acf)})"
    )

    # 3. Tabela umieszczona pod podpisem osi X – BEZ nagłówków kolumn (colLabels=None)
    table = ax.table(
        cellText=[
            se_values,
            hac_values,
        ],
        rowLabels=[
            "Przedział 95% (+/-)",
            "HAC 95% (+/-)",
        ],
        colLabels=None,  # Brak górnego wiersza z horyzontami
        cellLoc="center",
        rowLoc="right",
        loc="bottom",
        bbox=[0.0, -0.22, 1.0, 0.10],  # Pozycja poniżej opisu osi X
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)

    add_sample_size_note(
        fig,
        metric_acf,
        "observations",
        per="komórkę (horyzont i opóźnienie; liczba par czasowych)",
    )

    # Dopasowanie układu
    fig.tight_layout()

    _save_figure(
        fig,
        plot_path(
            output_dir,
            directory,
            (
                "score_return_correlation_"
                f"{config['filename_stem']}_autocorrelation_by_horizon_lag.png"
            ),
        ),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_score_return_autocorrelation_plots(
    autocorrelations,
    summary,
    timeframe,
    directory,
    output_dir,
):
    if autocorrelations.empty:
        return
    for config in HAC_DIAGNOSTIC_METRICS:
        _save_score_return_autocorrelation_plot(
            autocorrelations,
            summary,
            timeframe,
            directory,
            output_dir,
            config,
        )


def _save_score_return_hac_diagnostics(
    correlations,
    data,
    timeframe,
    directory,
    output_dir,
    horizon_points=None,
):
    if correlations.empty:
        return pd.DataFrame()

    horizon_correlations = _score_return_horizon_correlations(horizon_points)
    summary, autocorrelations = _score_return_horizon_hac_summary(
        horizon_correlations,
        timeframe,
    )

    if summary.empty:
        return summary

    save_csv_for_excel(
        summary,
        plot_path(
            output_dir,
            directory,
            "score_return_correlation_hac_summary.csv",
        ),
    )
    if not horizon_correlations.empty:
        save_csv_for_excel(
            horizon_correlations,
            plot_path(
                output_dir,
                directory,
                "score_return_correlation_by_horizon_timestamp.csv",
            ),
        )
    if not autocorrelations.empty:
        save_csv_for_excel(
            autocorrelations,
            plot_path(
                output_dir,
                directory,
                "score_return_correlation_autocorrelation.csv",
            ),
        )

    _save_score_return_hac_summary_plot(
        summary,
        timeframe,
        directory,
        output_dir,
    )
    _save_score_return_autocorrelation_plots(
        autocorrelations,
        summary,
        timeframe,
        directory,
        output_dir,
    )
    return summary
