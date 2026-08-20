from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.figure import Figure
import numpy as np
import pandas as pd

from app.testy.score_tests.common.data import (
    COMMON_HORIZON_ALIGNMENT_COLUMN,
    COMMON_HORIZON_ALIGNMENT_VALUE,
    COMMON_HORIZON_WEEK_END_COLUMN,
    COMMON_HORIZON_WEEK_START_COLUMN,
)


TIMEFRAME_HORIZON_LIMITS = {
    "short_term_14d": (7, 21),
    "medium_term_50d": (25, 75),
    "long_term_200d": (100, 300),
}

DEFAULT_TIMEFRAME_HORIZON_WEEK_RANGES = {
    "short_term_14d": (1, 3),
    "medium_term_50d": (4, 10),
    "long_term_200d": (21, 35),
}

SERIES_LABELS = {
    "All": "Wszystkie obserwacje",
    "All 18": "Wszystkie 18 spółek",
    "Pearson IC": "Pearson IC",
    "Spearman IC": "Spearman IC",
    "Score Percentile Pearson IC": "Pearson IC percentyla score",
    "Score percentile Pearson IC": "Pearson IC percentyla score",
}


def plot_path(output_dir, plot_type, filename):
    filename = Path(filename)
    artifact_output_dir = output_dir
    if filename.suffix.lower() == ".csv" and output_dir.name == "plots":
        artifact_output_dir = output_dir.parent / "data"
    directory = artifact_output_dir / plot_type
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
        "Horyzont przyszłej stopy zwrotu [tygodnie]"
        if horizon_x_column(df) == "horizon_weeks"
        else "Horyzont przyszłej stopy zwrotu (dni)"
    )


def _finite_integer_values(data, column):
    if data is None or not hasattr(data, "columns") or column not in data.columns:
        return pd.Series(dtype="int64")
    values = pd.to_numeric(data[column], errors="coerce").replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    return values.round().astype(int)


def horizon_week_range(data):
    starts = _finite_integer_values(data, "horizon_week_start")
    ends = _finite_integer_values(data, "horizon_week_end")
    if not starts.empty and not ends.empty:
        return int(starts.min()), int(ends.max())

    weeks = _finite_integer_values(data, "horizon_weeks")
    if not weeks.empty:
        return int(weeks.min()), int(weeks.max())
    return None


def format_horizon_week_range(start_week, end_week):
    start_week = int(start_week)
    end_week = int(end_week)
    if start_week == end_week:
        if end_week == 1:
            unit = "tydzień"
        elif end_week % 10 in {2, 3, 4} and end_week % 100 not in {12, 13, 14}:
            unit = "tygodnie"
        else:
            unit = "tygodni"
        return f"{start_week} {unit}"

    unit = "tygodnie" if end_week <= 4 else "tygodni"
    return f"{start_week}\N{EN DASH}{end_week} {unit}"


def timeframe_label(timeframe, data=None):
    text = str(timeframe)
    week_range = horizon_week_range(data)
    if week_range is None:
        week_range = DEFAULT_TIMEFRAME_HORIZON_WEEK_RANGES.get(text)
    if week_range is not None:
        return format_horizon_week_range(*week_range)
    return text.replace("_", " ")


def common_horizon_alignment_title_suffix(data):
    if (
        data is None
        or not hasattr(data, "columns")
        or COMMON_HORIZON_ALIGNMENT_COLUMN not in data.columns
    ):
        return ""

    alignment_values = data[COMMON_HORIZON_ALIGNMENT_COLUMN].dropna().astype(str)
    if not alignment_values.eq(COMMON_HORIZON_ALIGNMENT_VALUE).any():
        return ""

    return " (wyrównane do wspólnego horyzontu)"


def _sample_size_range(values):
    clean = pd.to_numeric(values, errors="coerce").replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    clean = clean[clean >= 0]
    if clean.empty:
        return None
    minimum = round(clean.min())
    maximum = round(clean.max())
    minimum_text = _format_sample_size(minimum)
    maximum_text = _format_sample_size(maximum)
    return (
        minimum_text
        if np.isclose(minimum, maximum)
        else f"{minimum_text}\N{EN DASH}{maximum_text}"
    )


def _format_sample_size(value):
    value = float(value)
    if np.isclose(value, round(value)):
        return str(int(round(value)))
    return f"{value:.1f}".replace(".", ",")


def label_with_sample_size(label, data, count_column="observation_count"):
    if data is None or count_column not in data.columns:
        return label
    size_range = _sample_size_range(data[count_column])
    if size_range is None:
        return label
    return f"{label}; n={size_range} na punkt"


def sample_size_note(
    data=None,
    count_column=None,
    *,
    per="wykres",
    note=None,
):
    if note:
        return f"Liczebność próby: {note}"
    if data is None:
        return None

    details = []
    if count_column and hasattr(data, "columns") and count_column in data.columns:
        size_range = _sample_size_range(data[count_column])
        if size_range is not None:
            details.append(f"n={size_range} na {per}")
    elif hasattr(data, "__len__"):
        details.append(f"n={len(data)} obserwacji")

    if hasattr(data, "columns"):
        date_column = next(
            (
                column
                for column in ("timestamp", "start_timestamp")
                if column in data.columns
            ),
            None,
        )
        if date_column is not None:
            date_count = int(data[date_column].dropna().nunique())
            if date_count:
                details.append(f"{date_count} dat")

    return f"Liczebność próby: {'; '.join(details)}" if details else None


def add_sample_size_note(
    fig,
    data=None,
    count_column=None,
    *,
    per="punkt",
    note=None,
):
    text = sample_size_note(
        data,
        count_column,
        per=per,
        note=note,
    )
    if not text:
        return
    fig._score_tests_sample_note = text
    fig.text(
        0.01,
        0.012,
        wrap_plot_text(text, width=150),
        ha="left",
        va="bottom",
        fontsize=8,
        color="#444444",
    )


def annotate_sample_sizes(
    ax,
    x_values,
    y_values,
    counts,
    *,
    max_annotations=30,
    label_prefix="n",
):
    points = pd.DataFrame({
        "x": list(x_values),
        "y": list(y_values),
        "n": list(counts),
    })
    for column in points.columns:
        points[column] = pd.to_numeric(points[column], errors="coerce")
    points = points.replace([np.inf, -np.inf], np.nan).dropna()
    points = points[points["n"] >= 0]
    if points.empty or len(points) > max_annotations:
        return

    for point in points.itertuples(index=False):
        ax.annotate(
            f"{label_prefix}={_format_sample_size(point.n)}",
            xy=(point.x, point.y),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7,
            color="#444444",
        )


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
    return f"{label} (śr. {formatter(mean_value)})"


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
        if getattr(self, "_score_tests_sample_note", None) and "rect" not in kwargs:
            kwargs["rect"] = (0, 0.055, 1, 1)
        return original_tight_layout(self, *args, **kwargs)

    tight_layout_with_wrapped_text._score_tests_wraps_text = True
    Figure.tight_layout = tight_layout_with_wrapped_text


_install_wrapped_tight_layout()


def set_integer_x_axis(ax):
    ax.xaxis.set_major_locator(mtick.MaxNLocator(integer=True))


def set_percent_x_axis(ax, xmax=1.0):
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax))


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
            label=mean_label(
                        bucket,
                        group["annualized_return"],
                        lambda value: f"{value:.2%}",
                    ),
        )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(f"{title}{common_horizon_alignment_title_suffix(data)}")
    ax.set_xlabel(horizon_x_label(data))
    set_integer_x_axis(ax)
    ax.set_ylabel("Średnia roczna stopa zwrotu")
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
    add_sample_size_note(
        fig,
        data,
        "observation_count",
        per="punkt (koszyk i horyzont)",
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

    if "observation_count" in data.columns:
        aggregations["sample_size_min"] = ("observation_count", "min")
        aggregations["sample_size_max"] = ("observation_count", "max")
        aggregations["horizon_count"] = ("observation_count", "count")

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
            f"{plot_label(row.bucket)}\nśr. score {row.avg_score_min:.1f}"
            for row in average.itertuples(index=False)
        ]
    if {"sample_size_min", "sample_size_max", "horizon_count"}.issubset(
        average.columns
    ):
        labels = [
            (
                f"{label}"
                if row.sample_size_min == row.sample_size_max
                else (
                    f"{label}"
                    f"\N{EN DASH}{int(row.sample_size_max)}/horyzont"
                )
            )
            for label, row in zip(labels, average.itertuples(index=False))
        ]

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar(labels, average["annualized_return"], color="#4C78A8")

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(f"{title}{common_horizon_alignment_title_suffix(data)}")
    ax.set_xlabel("Koszyk")
    ax.set_ylabel("Średnia roczna stopa zwrotu")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=45)
    if "observation_count" in data.columns:
        bucket_sample_sizes = (
            data.groupby("bucket", as_index=False)["observation_count"]
            .sum()
            .rename(columns={"observation_count": "bucket_observation_count"})
        )
        add_sample_size_note(
            fig,
            bucket_sample_sizes,
            "bucket_observation_count",
            per="koszyk",
        )
    wrap_figure_text(fig)
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, plot_type, filename), dpi=160)
    plt.close(fig)
