from pathlib import Path
import textwrap

import matplotlib


matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.figure import Figure
import numpy as np
import pandas as pd


TIMEFRAME_HORIZON_LIMITS = {
    "short_term_14d": (7, 21),
    "medium_term_50d": (25, 75),
    "long_term_200d": (100, 300),
}

TIMEFRAME_LABELS = {
    "short_term_14d": "Krótki termin (ok. 14 d.)",
    "medium_term_50d": "Średni termin (ok. 50 d.)",
    "long_term_200d": "Długi termin (ok. 200 d.)",
}

SERIES_LABELS = {
    "All": "Wszystkie obserwacje",
    "All 18": "Wszystkie 18 spółek",
    "Pearson IC": "Pearson IC",
    "Spearman IC": "Spearman IC",
    "Score Percentile Pearson IC": "Pearson IC percentyla wyniku",
    "Score percentile Pearson IC": "Pearson IC percentyla wyniku",
}


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def limit_horizon_range(timeframe, df):
    limits = TIMEFRAME_HORIZON_LIMITS.get(timeframe)
    if limits is None:
        return df
    if "horizon_weeks" in df.columns:
        return df
    start_day, end_day = limits
    return df[df["horizon_days"].between(start_day, end_day)]


def horizon_x_column(df):
    return "horizon_weeks" if "horizon_weeks" in df.columns else "horizon_days"


def horizon_x_label(df):
    return (
        "Horyzont przyszłej stopy zwrotu (tygodnie)"
        if horizon_x_column(df) == "horizon_weeks"
        else "Horyzont przyszłej stopy zwrotu (dni)"
    )


def timeframe_label(timeframe):
    text = str(timeframe)
    return TIMEFRAME_LABELS.get(text, text.replace("_", " "))


def plot_label(label):
    text = str(label)
    if text in SERIES_LABELS:
        return SERIES_LABELS[text]
    if text.startswith("Top "):
        return f"Top {text[4:]}"
    if text.startswith("Rank "):
        return f"Poz. {text[5:]}"
    return text.replace("_", " ")


def mean_label(label, values, formatter):
    mean_value = values.dropna().mean()
    label = plot_label(label)
    if mean_value != mean_value:
        return label
    return f"{label} (średnia {formatter(mean_value)})"


def wrap_plot_text(text, width=74):
    if text is None:
        return text
    lines = str(text).splitlines() or [""]
    return "\n".join(
        textwrap.fill(
            line,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        if len(line) > width
        else line
        for line in lines
    )


def wrap_figure_text(fig, title_width=78, axis_width=54):
    if getattr(fig, "_suptitle", None) is not None:
        fig._suptitle.set_text(
            wrap_plot_text(fig._suptitle.get_text(), title_width)
        )

    for ax in fig.axes:
        ax.set_title(wrap_plot_text(ax.get_title(), title_width))
        ax.set_xlabel(wrap_plot_text(ax.get_xlabel(), axis_width))
        ax.set_ylabel(wrap_plot_text(ax.get_ylabel(), axis_width))


def _install_wrapped_tight_layout():
    original_tight_layout = Figure.tight_layout
    if getattr(original_tight_layout, "_score_tests_wraps_text", False):
        return

    def tight_layout_with_wrapped_text(self, *args, **kwargs):
        wrap_figure_text(self)
        return original_tight_layout(self, *args, **kwargs)

    tight_layout_with_wrapped_text._score_tests_wraps_text = True
    Figure.tight_layout = tight_layout_with_wrapped_text


_install_wrapped_tight_layout()


def set_integer_x_axis(ax):
    ax.xaxis.set_major_locator(mtick.MaxNLocator(integer=True))


def plot_bucket_lines(
    data,
    output_dir,
    plot_type,
    filename,
    title,
    bucket_order,
    show_mean_in_legend=False,
):
    if data.empty:
        return
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.RdYlGn_r(np.linspace(0.05, 0.95, len(bucket_order)))
    x_column = horizon_x_column(data)
    for color, bucket in zip(colors, bucket_order):
        group = data[data["bucket"] == bucket].sort_values(x_column)
        if group.empty:
            continue
        ax.plot(
            group[x_column],
            group["annualized_return"],
            marker="o",
            markevery=max(1, len(group) // 30),
            linewidth=1.8,
            markersize=3,
            color=color,
            label=(
                mean_label(
                    bucket,
                    group["annualized_return"],
                    lambda value: f"{value:.2%}",
                )
                if show_mean_in_legend
                else plot_label(bucket)
            ),
        )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel(horizon_x_label(data))
    set_integer_x_axis(ax)
    ax.set_ylabel("Roczna stopa zwrotu")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    ax.legend(
        title=(
            "Średnia z pokazanych horyzontów"
            if show_mean_in_legend
            else "Koszyk"
        ),
        ncol=2,
    )
    wrap_figure_text(fig)
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, plot_type, filename), dpi=160)
    plt.close(fig)


def plot_bucket_average(
    data,
    output_dir,
    plot_type,
    filename,
    title,
    bucket_order,
    score_range_columns=None,
):
    if data.empty:
        return
    aggregations = {"annualized_return": ("annualized_return", "mean")}
    if score_range_columns:
        min_column, max_column = score_range_columns
        aggregations["avg_score_min"] = (min_column, "mean")
        aggregations["avg_score_max"] = (max_column, "mean")

    average = data.groupby("bucket", as_index=False).agg(**aggregations)
    average["bucket"] = pd.Categorical(
        average["bucket"],
        categories=bucket_order,
        ordered=True,
    )
    average = average.sort_values("bucket").dropna(subset=["annualized_return"])
    if average.empty:
        return

    labels = [plot_label(bucket) for bucket in average["bucket"].astype(str)]
    if score_range_columns:
        labels = [
            f"{plot_label(row.bucket)}\nśr. wyn. {row.avg_score_min:.1f}"
            for row in average.itertuples(index=False)
        ]

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar(labels, average["annualized_return"], color="#4C78A8")

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("Koszyk")
    ax.set_ylabel("Średnia roczna stopa zwrotu")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=45)
    wrap_figure_text(fig)
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, plot_type, filename), dpi=160)
    plt.close(fig)
