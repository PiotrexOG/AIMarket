from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.plotting import add_sample_size_note, plot_path

from .normalization import _format_metric_value
from .plot_io import _save_figure, _save_heatmap_csv
from .plot_labels import company_horizon_sample_note


def _save_ticker_date_heatmap(
    data,
    ticker_order,
    value_column,
    timeframe,
    output_dir,
    directory,
    filename,
    title,
    colorbar_label,
    cmap_name,
    vmin=None,
    vmax=None,
    percent_format=False,
    robust=False,
    symmetric=False,
    row_metric=None,
    row_metric_label="ME",
    row_metric_format="signed",
    column_metric=None,
    column_metric_label=None,
    column_metric_format="percent",
):
    heatmap_data = data.pivot_table(
        index="ticker",
        columns="timestamp",
        values=value_column,
        aggfunc="last",
    ).sort_index(axis=1)
    if heatmap_data.empty:
        return

    heatmap_data = heatmap_data.reindex(ticker_order)
    _save_heatmap_csv(heatmap_data, output_dir, directory, filename)
    values = heatmap_data.to_numpy(dtype=float)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return

    if symmetric and vmin is None and vmax is None:
        percentile = 95 if robust else 100
        limit = float(np.nanpercentile(np.abs(finite_values), percentile))
        if np.isclose(limit, 0):
            limit = max(abs(float(np.nanmin(finite_values))), 1.0) * 0.01
        vmin = -limit
        vmax = limit
    elif robust and vmin is None and vmax is None:
        vmin = float(np.nanpercentile(finite_values, 5))
        vmax = float(np.nanpercentile(finite_values, 95))
        if np.isclose(vmin, vmax):
            vmin = float(np.nanmin(finite_values))
            vmax = float(np.nanmax(finite_values))
    if vmin is None:
        vmin = float(np.nanmin(finite_values))
    if vmax is None:
        vmax = float(np.nanmax(finite_values))
    if np.isclose(vmin, vmax):
        spread = max(abs(vmin), 1.0) * 0.01
        vmin -= spread
        vmax += spread

    fig, ax = plt.subplots(figsize=(15.5, 8))
    cmap = plt.cm.get_cmap(cmap_name).copy()
    cmap.set_bad("#F2F2F2")
    image = ax.imshow(
        values,
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )

    y_positions = np.arange(len(heatmap_data.index))
    ax.set_yticks(y_positions)
    ax.set_yticklabels(heatmap_data.index)
    ax.set_ylabel(
        "Ticker, sortowanie według średniej przyszłej rocznej stopy zwrotu"
    )
    ax.set_xlabel("Data scoringu")
    ax.set_title(title)

    date_count = len(heatmap_data.columns)
    tick_count = min(10, date_count)
    tick_positions = (
        np.linspace(0, date_count - 1, tick_count, dtype=int)
        if date_count
        else np.array([], dtype=int)
    )
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(
        [
            heatmap_data.columns[position].strftime("%Y-%m-%d")
            for position in tick_positions
        ],
        rotation=45,
        ha="right",
    )
    ax.set_xticks(np.arange(-0.5, date_count, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(heatmap_data.index), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)

    colorbar_pad = 0.11 if row_metric is not None and not row_metric.empty else 0.02
    colorbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=colorbar_pad)
    colorbar.set_label(colorbar_label)
    if percent_format:
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    if row_metric is not None and not row_metric.empty:
        row_metric = row_metric.reindex(heatmap_data.index)
        metric_ax = ax.twinx()
        metric_ax.set_ylim(ax.get_ylim())
        metric_ax.set_yticks(y_positions)
        metric_ax.set_yticklabels(
            [
                (
                    f"{row_metric_label}="
                    f"{_format_metric_value(value, row_metric_format)}"
                )
                if pd.notna(value)
                else ""
                for value in row_metric
            ]
        )
        metric_ax.tick_params(axis="y", length=0, pad=8)

    if column_metric is not None and not column_metric.empty:
        ax.set_xlabel("")
        column_metric = column_metric.reindex(heatmap_data.columns)
        metric_label = column_metric_label or "Metryka"
        metric_values = pd.DataFrame({
            "timestamp": heatmap_data.columns,
            metric_label: column_metric.to_numpy(),
        })
        metric_filename = f"{Path(filename).stem}_column_metric.csv"
        save_csv_for_excel(
            metric_values,
            plot_path(output_dir, directory, metric_filename),
        )

        metric_ax = ax.twiny()
        metric_ax.set_xlim(ax.get_xlim())
        metric_ax.xaxis.set_ticks_position("bottom")
        metric_ax.xaxis.set_label_position("bottom")
        metric_ax.spines["bottom"].set_position(("outward", 62))
        metric_ax.spines["top"].set_visible(False)
        metric_ax.set_xticks(np.arange(date_count))
        metric_ax.set_xticklabels(
            [
                _format_metric_value(value, column_metric_format)
                for value in column_metric
            ],
            rotation=0,
            ha="center",
            fontsize=7,
        )
        metric_ax.set_xlabel(metric_label)
        metric_ax.tick_params(axis="x", length=0, pad=2)

    sample_data = data.dropna(subset=["ticker", "timestamp", value_column])
    add_sample_size_note(
        fig,
        note=company_horizon_sample_note(sample_data),
    )

    fig.tight_layout()
    _save_figure(
        fig,
        plot_path(output_dir, directory, filename),
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)
