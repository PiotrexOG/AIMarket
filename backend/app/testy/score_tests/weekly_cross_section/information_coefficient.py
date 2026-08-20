import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    common_horizon_alignment_title_suffix,
    horizon_x_column,
    horizon_x_label,
    limit_horizon_range,
    mean_label,
    plot_path,
    set_integer_x_axis,
    timeframe_label,
)
from app.testy.score_tests.common.output_paths import (
    WEEKLY_INFORMATION_COEFFICIENT_DIR,
)


def build_correlation_output(analysis):
    columns = [
        "timeframe",
        "horizon_weeks",
        "horizon_days",
        "metric",
        "observation_count",
        "start_date_count",
        "company_count_min",
        "company_count_max",
        "company_observation_count",
        "pearson",
    ]
    if analysis.empty:
        return pd.DataFrame(columns=columns)
    selected = analysis[
        analysis["test"] == "weekly_information_coefficient"
    ].copy()
    for column in columns:
        if column not in selected.columns:
            selected[column] = np.nan
    return (
        selected[columns]
        .sort_values(["timeframe", "horizon_weeks", "metric"])
        .reset_index(drop=True)
    )


def _format_count_range(values):
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return None
    minimum = int(clean.min())
    maximum = int(clean.max())
    return str(minimum) if minimum == maximum else f"{minimum}\N{EN DASH}{maximum}"


def _ic_sample_size_note(data):
    observation_range = _format_count_range(data["company_observation_count"])
    return (
        f"n = {observation_range} na punkt (miara i horyzont)"
    )


def plot(analysis, output_dir):
    data = analysis[
        analysis["test"] == "weekly_information_coefficient"
    ].dropna(subset=["pearson"])
    for timeframe, timeframe_data in data.groupby("timeframe"):
        timeframe_data = limit_horizon_range(timeframe, timeframe_data)
        if timeframe_data.empty:
            continue
        fig, ax = plt.subplots(figsize=(12, 7))
        x_column = horizon_x_column(timeframe_data)
        for metric, group in timeframe_data.groupby("metric", sort=False):
            group = group.sort_values(x_column)
            ax.plot(
                group[x_column],
                group["pearson"],
                marker="o",
                markevery=max(1, len(group) // 30),
                linewidth=1.8,
                markersize=3,
                label=mean_label(
                        metric,
                        group["pearson"],
                        lambda value: f"{value:.3f}",
                    ),
            )
        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(
            f"{timeframe_label(timeframe, timeframe_data)}: tygodniowe miary IC "
            "dla przyszłych stóp zwrotu"
            f"{common_horizon_alignment_title_suffix(timeframe_data)}"
        )
        ax.set_xlabel(horizon_x_label(timeframe_data))
        set_integer_x_axis(ax)
        ax.set_ylabel("Średni tygodniowy IC")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Średnia z pokazanych horyzontów")
        add_sample_size_note(
            fig,
            note=_ic_sample_size_note(timeframe_data),
        )
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                WEEKLY_INFORMATION_COEFFICIENT_DIR,
                f"{timeframe}_weekly_information_coefficient.png",
            ),
            dpi=160,
        )
        plt.close(fig)
