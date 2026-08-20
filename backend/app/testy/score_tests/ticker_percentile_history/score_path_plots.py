import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    plot_path,
    timeframe_label,
)

from .plot_config import MOVING_AVERAGE_COLUMN
from .plot_io import _save_figure


def _save_combined_plot(
    metric_group,
    price_group,
    ticker,
    timeframe,
    directory,
    output_dir,
    moving_average_window,
    horizon_data=None,
):
    percentile_color = "#4C78A8"
    moving_average_color = "#59A14F"
    price_color = "#E15759"

    fig, percentile_ax = plt.subplots(figsize=(13, 7))
    price_ax = percentile_ax.twinx()

    percentile_line = percentile_ax.plot(
        metric_group["timestamp"],
        metric_group["current_score_percentile"],
        color=percentile_color,
        linewidth=2.2,
        label="Surowy percentyl score",
    )[0]
    moving_average_line = None
    if MOVING_AVERAGE_COLUMN in metric_group.columns:
        moving_average_values = metric_group[MOVING_AVERAGE_COLUMN]
        if moving_average_values.notna().any():
            moving_average_line = percentile_ax.plot(
                metric_group["timestamp"],
                moving_average_values,
                color=moving_average_color,
                linewidth=2.4,
                linestyle="--",
                label=(
                    f"{moving_average_window}-punktowa średnia krocząca "
                    "percentyla score"
                ),
            )[0]
    price_line = price_ax.plot(
        price_group["timestamp"],
        price_group["close"],
        color=price_color,
        linewidth=2,
        alpha=0.85,
        label="Cena zamknięcia",
    )[0]

    percentile_ax.set_title(
        f"{ticker}: percentyl score, średnia krocząca i cena "
        f"zamknięcia ({timeframe_label(timeframe, horizon_data)})"
    )
    percentile_ax.set_xlabel("Data")
    percentile_ax.set_ylabel("Percentyl score", color=percentile_color)
    percentile_ax.set_ylim(0, 1)
    percentile_ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    percentile_ax.tick_params(axis="y", colors=percentile_color)
    percentile_ax.grid(True, alpha=0.25)

    price_ax.set_ylabel("Cena zamknięcia", color=price_color)
    price_ax.tick_params(axis="y", colors=price_color)
    legend_handles = [percentile_line, price_line]
    if moving_average_line is not None:
        legend_handles.insert(1, moving_average_line)
    percentile_ax.legend(
        handles=legend_handles,
        loc="best",
    )

    metric_count = int(metric_group["current_score_percentile"].notna().sum())
    price_count = int(price_group["close"].notna().sum())
    add_sample_size_note(
        fig,
        note=(
            f"n={metric_count} dziennych obserwacji percentyla score; "
            f"n={price_count} obserwacji ceny zamknięcia"
        ),
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, f"{ticker}_score_percentile_with_price.png"),
        dpi=180,
    )
    plt.close(fig)
