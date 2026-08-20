import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm
import numpy as np
import pandas as pd

from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    annotate_sample_sizes,
    common_horizon_alignment_title_suffix,
    plot_path,
    set_percent_x_axis,
    timeframe_label,
)
from app.testy.score_tests.common.output_paths import (
    DOWNSIDE_BENCHMARK_RETURN_BUCKETS_SECTION,
    DOWNSIDE_INFORMATION_RATIO_DIR,
    horizon_dir,
)



ALPHA_HEATMAP_LIMIT = 0.20
DIR_HEATMAP_MAX = 5.0
ALPHA_HEATMAP_CMAP = LinearSegmentedColormap.from_list(
    "alpha_zero_centered",
    ["#C85A3A", "#FFF7BC", "#238B45"],
)



def plot_benchmark_return_buckets(analysis, output_dir, horizon_label):
    if analysis.empty:
        return
    plot_directory = horizon_dir(
        DOWNSIDE_INFORMATION_RATIO_DIR,
        horizon_label,
        DOWNSIDE_BENCHMARK_RETURN_BUCKETS_SECTION,
    )
    # for (timeframe, bucket_id), bucket_data in analysis.groupby(
    #     ["timeframe", "benchmark_return_bucket_id"],
    #     sort=False,
    # ):
    #     clean = bucket_data.dropna(
    #         subset=["top_percent", "downside_information_ratio"]
    #     ).sort_values("top_percent")
    #     if clean.empty:
    #         continue
    #
    #     bucket_row = clean.iloc[0]
    #     bucket_label = (
    #         f"B{int(bucket_id):02d}: "
    #         f"{bucket_row.benchmark_bucket_min:.2%} do "
    #         f"{bucket_row.benchmark_bucket_max:.2%}"
    #     )
    #     bucket_directory = plot_directory / f"bucket_{int(bucket_id):02d}"
    #     _plot_bucket_returns(
    #         clean,
    #         timeframe,
    #         bucket_label,
    #         output_dir,
    #         bucket_directory,
    #     )
    #     _plot_bucket_deviation(
    #         clean,
    #         timeframe,
    #         bucket_label,
    #         output_dir,
    #         bucket_directory,
    #     )
    #     _plot_bucket_ratio(
    #         clean,
    #         timeframe,
    #         bucket_label,
    #         output_dir,
    #         bucket_directory,
    #     )

    for timeframe, timeframe_data in analysis.groupby("timeframe", sort=False):
        clean = timeframe_data.dropna(subset=["top_share"])
        if clean.empty:
            continue
        _plot_bucket_heatmaps(clean, timeframe, output_dir, plot_directory)


def _plot_bucket_returns(data, timeframe, bucket_label, output_dir, directory):
    title_timeframe = timeframe_label(timeframe, data)
    title_suffix = common_horizon_alignment_title_suffix(data)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["mean_annualized_strategy_return"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
        label="Strategia najlepszych M (%) spółek",
    )
    ax.plot(
        data["top_percent"],
        data["mean_annualized_benchmark_return"],
        marker="o",
        linewidth=2,
        color="#9C755F",
        label="Benchmark wszystkich spółek",
    )
    ax.plot(
        data["top_percent"],
        data["mean_annualized_alpha"],
        marker="o",
        linewidth=2,
        color="#59A14F",
        label="Roczny nadwyżkowy zwrot względem benchmarku",
    )
    if "observation_count" in data.columns:
        annotate_sample_sizes(
            ax,
            data["top_percent"],
            data["mean_annualized_strategy_return"],
            data["observation_count"],
        )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{title_timeframe}: średnia roczna stopa zwrotu "
        f"w koszyku benchmarku {bucket_label}"
        f"{title_suffix}"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Średnia roczna stopa zwrotu")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    ax.legend()
    add_sample_size_note(
        fig,
        data,
        "observation_count",
        per="punkt M(%) spółek w koszyku benchmarku",
    )
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_bucket_mean_return.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_bucket_deviation(data, timeframe, bucket_label, output_dir, directory):
    title_timeframe = timeframe_label(timeframe, data)
    title_suffix = common_horizon_alignment_title_suffix(data)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_deviation"],
        marker="o",
        linewidth=2,
        color="#E15759",
    )
    ax.set_title(
        f"{title_timeframe}: downside deviation nadwyżkowego zwrotu "
        f"w koszyku benchmarku {bucket_label}"
        f"{title_suffix}"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Downside deviation")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    if "observation_count" in data.columns:
        annotate_sample_sizes(
            ax,
            data["top_percent"],
            data["downside_deviation"],
            data["observation_count"],
        )
    ax.grid(True, alpha=0.25)
    add_sample_size_note(
        fig,
        data,
        "observation_count",
        per="punkt M(%) spółek w koszyku benchmarku",
    )
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_bucket_downside_deviation.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_bucket_ratio(data, timeframe, bucket_label, output_dir, directory):
    title_timeframe = timeframe_label(timeframe, data)
    title_suffix = common_horizon_alignment_title_suffix(data)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_information_ratio"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{title_timeframe}: wskaźnik DIR nadwyżkowego zwrotu "
        f"w koszyku benchmarku {bucket_label}"
        f"{title_suffix}"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Wskaźnik DIR")
    if "observation_count" in data.columns:
        annotate_sample_sizes(
            ax,
            data["top_percent"],
            data["downside_information_ratio"],
            data["observation_count"],
        )
    ax.grid(True, alpha=0.25)
    add_sample_size_note(
        fig,
        data,
        "observation_count",
        per="punkt M(%) spółek w koszyku benchmarku",
    )
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_bucket_downside_ratio.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_bucket_heatmaps(data, timeframe, output_dir, directory):
    title_timeframe = timeframe_label(timeframe, data)
    metrics = [
        (
            "mean_annualized_alpha",
            "Roczny nadwyżkowy zwrot względem benchmarku",
            (
                f"{title_timeframe}: roczny nadwyżkowy zwrot "
                "według koszyka zwrotu benchmarku i najlepszych N spółek"
            ),
            f"{timeframe}_heatmap_annualized_alpha.png",
            ALPHA_HEATMAP_CMAP,
            True,
            TwoSlopeNorm(
                vmin=-ALPHA_HEATMAP_LIMIT,
                vcenter=0.0,
                vmax=ALPHA_HEATMAP_LIMIT,
            ),
            (-ALPHA_HEATMAP_LIMIT, ALPHA_HEATMAP_LIMIT),
        ),
        (
            "downside_deviation",
            "Downside deviation",
            (
                f"{title_timeframe}: downside deviation nadwyżkowego zwrotu "
                "według koszyka zwrotu benchmarku i najlepszych N spółek"
            ),
            f"{timeframe}_heatmap_downside_deviation.png",
            "YlOrRd",
            True,
            None,
            None,
        ),
        (
            "downside_information_ratio",
            "Wskaźnik DIR",
            (
                f"{title_timeframe}: wskaźnik DIR według koszyka zwrotu "
                "benchmarku i najlepszych N spółek"
            ),
            f"{timeframe}_heatmap_downside_information_ratio.png",
            "YlGn",
            False,
            Normalize(vmin=0.0, vmax=DIR_HEATMAP_MAX, clip=True),
            None,
        ),
    ]
    for metric, label, title, filename, cmap, is_percent, norm, clip_limits in metrics:
        _plot_metric_heatmap(
            data,
            metric,
            label,
            title,
            filename,
            cmap,
            is_percent,
            norm,
            clip_limits,
            output_dir,
            directory,
        )


def _plot_metric_heatmap(
        data,
        metric,
        colorbar_label,
        title,
        filename,
        cmap,
        is_percent,
        norm,
        clip_limits,
        output_dir,
        directory,
):
    clean = data.dropna(subset=[metric]).copy()
    if clean.empty:
        return

    clean["top_n_equivalent"] = clean["top_share"] * 18
    bucket_order = sorted(clean["benchmark_return_bucket_id"].unique())
    top_order = sorted(clean["top_share"].unique())

    # Pivot tworzy macierz; brakujące kombinacje będą miały wartość np.nan
    matrix = clean.pivot_table(
        index="benchmark_return_bucket_id",
        columns="top_share",
        values=metric,
        aggfunc="mean",
    ).reindex(index=bucket_order, columns=top_order)
    counts = clean.pivot_table(
        index="benchmark_return_bucket_id",
        columns="top_share",
        values="observation_count",
        aggfunc="max",
    ).reindex(index=bucket_order, columns=top_order)

    if matrix.empty:
        return

    bucket_info = (
        clean.drop_duplicates("benchmark_return_bucket_id")
        .set_index("benchmark_return_bucket_id")
        .reindex(bucket_order)
    )
    y_labels = [
        (
            f"B{int(bucket_id):02d} "
            f"{row.benchmark_bucket_min:.1%} do {row.benchmark_bucket_max:.1%} "
            f"(średnia {row.benchmark_bucket_mean:.1%})"
        )
        for bucket_id, row in bucket_info.iterrows()
    ]
    x_labels = [
        f"{top_n:.1f}"
        for top_n in (
            clean.drop_duplicates("top_share")
            .set_index("top_share")
            .reindex(top_order)["top_n_equivalent"]
        )
    ]

    values = matrix.to_numpy(dtype=float)

    # Maska dla wartości nieprawidłowych / niepoliczalnych (NaN lub np. inf)
    invalid_mask = np.isnan(values) | np.isinf(values)

    display_values = (
        np.clip(values, clip_limits[0], clip_limits[1])
        if clip_limits is not None
        else values
    )

    fig_width = max(14, len(top_order) * 0.34)
    fig_height = max(7, len(bucket_order) * 0.55 + 2.5)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Rysowanie głównej heatmapy
    image = ax.imshow(display_values, aspect="auto", cmap=cmap, norm=norm)

    for row_index in range(len(bucket_order)):
        for column_index in range(len(top_order)):
            count = counts.iloc[row_index, column_index]
            if pd.isna(count) or count <= 0 or invalid_mask[row_index, column_index]:
                continue

    # --- DODANY FRAGMENT: NAKŁADANIE SKOŚNYCH SZARYCH KRESEK ---
    y_indices, x_indices = np.where(invalid_mask)
    for x, y in zip(x_indices, y_indices):
        # Rysujemy prostokąt w miejscu nieprawidłowej komórki
        rect = plt.Rectangle(
            (x - 0.5, y - 0.5), 1, 1,
            fill=True,
            facecolor='#E0E0E0',  # Tło kafelka: jasnoszary
            hatch='//',  # Skośne kreski
            edgecolor='#888888',  # Kolor szarych kresek
            linewidth=0.5
        )
        ax.add_patch(rect)
    # ------------------------------------------------------------

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label(colorbar_label)
    if is_percent:
        colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    tick_step = max(1, int(np.ceil(len(top_order) / 18)))
    visible_x_ticks = np.arange(0, len(top_order), tick_step)
    ax.set_xticks(visible_x_ticks)
    ax.set_xticklabels(
        [x_labels[index] for index in visible_x_ticks],
        rotation=45,
        ha="right",
    )
    ax.set_yticks(np.arange(len(bucket_order)))
    ax.set_yticklabels(y_labels)
    ax.set_title(f"{title}{common_horizon_alignment_title_suffix(clean)}")
    ax.set_xlabel("Ekwiwalent liczby najlepszych N spółek")
    ax.set_ylabel("Koszyk rocznej stopy zwrotu benchmarku")
    ax.set_xticks(np.arange(-0.5, len(top_order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(bucket_order), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.6)
    ax.tick_params(which="minor", bottom=False, left=False)
    add_sample_size_note(
        fig,
        clean,
        "observation_count",
        per="komórkę (koszyk benchmarku i liczba N spółek)",
    )
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, directory, filename), dpi=170)
    plt.close(fig)
