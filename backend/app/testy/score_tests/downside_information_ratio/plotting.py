from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm
import numpy as np

from app.testy.score_tests.common.plotting import plot_path


ALPHA_HEATMAP_LIMIT = 0.20
DIR_HEATMAP_MAX = 5.0
ALPHA_HEATMAP_CMAP = LinearSegmentedColormap.from_list(
    "alpha_zero_centered",
    ["#C85A3A", "#FFF7BC", "#238B45"],
)


def plot(analysis, output_dir, horizon_label):
    if analysis.empty:
        return
    for timeframe, timeframe_data in analysis.groupby("timeframe"):
        clean = timeframe_data.dropna(
            subset=["top_percent", "downside_information_ratio"]
        ).sort_values("top_percent")
        if clean.empty:
            continue

        plot_directory = Path("downside_information_ratio") / horizon_label
        _plot_returns(clean, timeframe, output_dir, plot_directory, horizon_label)
        _plot_deviation(clean, timeframe, output_dir, plot_directory, horizon_label)
        _plot_ratio(clean, timeframe, output_dir, plot_directory, horizon_label)


def plot_benchmark_return_buckets(analysis, output_dir, horizon_label):
    if analysis.empty:
        return
    plot_directory = (
        Path("downside_information_ratio")
        / horizon_label
        / "benchmark_return_buckets"
    )
    for (timeframe, bucket_id), bucket_data in analysis.groupby(
        ["timeframe", "benchmark_return_bucket_id"],
        sort=False,
    ):
        clean = bucket_data.dropna(
            subset=["top_percent", "downside_information_ratio"]
        ).sort_values("top_percent")
        if clean.empty:
            continue

        bucket_label = clean["benchmark_return_bucket"].iloc[0]
        bucket_directory = plot_directory / f"bucket_{int(bucket_id):02d}"
        _plot_bucket_returns(
            clean,
            timeframe,
            bucket_label,
            output_dir,
            bucket_directory,
        )
        _plot_bucket_deviation(
            clean,
            timeframe,
            bucket_label,
            output_dir,
            bucket_directory,
        )
        _plot_bucket_ratio(
            clean,
            timeframe,
            bucket_label,
            output_dir,
            bucket_directory,
        )

    for timeframe, timeframe_data in analysis.groupby("timeframe", sort=False):
        clean = timeframe_data.dropna(subset=["top_share"])
        if clean.empty:
            continue
        _plot_bucket_heatmaps(clean, timeframe, output_dir, plot_directory)


def _plot_returns(data, timeframe, output_dir, directory, horizon_label):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["mean_annualized_strategy_return"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
        label="Top M strategy",
    )
    ax.plot(
        data["top_percent"],
        data["mean_annualized_benchmark_return"],
        marker="o",
        linewidth=2,
        color="#9C755F",
        label="Top 100% benchmark",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{timeframe}: mean annualized return by Top M, "
        f"equal-weight horizons {horizon_label}"
    )
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Mean annualized return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_mean_annualized_return.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_deviation(data, timeframe, output_dir, directory, horizon_label):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_deviation"],
        marker="o",
        linewidth=2,
        color="#E15759",
    )
    ax.set_title(
        f"{timeframe}: mean downside deviation by Top M, "
        f"equal-weight horizons {horizon_label}"
    )
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Mean downside deviation")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_mean_downside_deviation.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_ratio(data, timeframe, output_dir, directory, horizon_label):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_information_ratio"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
        label="Downside information ratio",
    )
    plateau = data[data["is_stability_plateau"]]
    if not plateau.empty:
        ax.scatter(
            plateau["top_percent"],
            plateau["downside_information_ratio"],
            s=90,
            facecolors="none",
            edgecolors="#F28E2B",
            linewidths=2,
            label="Stability plateau",
        )
    recommendation = data[data["is_stable_recommendation"]]
    if not recommendation.empty:
        point = recommendation.iloc[0]
        ax.scatter(
            [point["top_percent"]],
            [point["downside_information_ratio"]],
            marker="*",
            s=220,
            color="#59A14F",
            label=f"Stable recommendation: {point['top_percent']:.2f}%",
        )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{timeframe}: downside information ratio by Top M, "
        f"equal-weight horizons {horizon_label}"
    )
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Downside information ratio")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        plot_path(
            output_dir,
            directory,
            f"{timeframe}_downside_information_ratio.png",
        ),
        dpi=160,
    )
    plt.close(fig)


def _plot_bucket_returns(data, timeframe, bucket_label, output_dir, directory):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["mean_annualized_strategy_return"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
        label="Top M strategy",
    )
    ax.plot(
        data["top_percent"],
        data["mean_annualized_benchmark_return"],
        marker="o",
        linewidth=2,
        color="#9C755F",
        label="Top 100% benchmark",
    )
    ax.plot(
        data["top_percent"],
        data["mean_annualized_alpha"],
        marker="o",
        linewidth=2,
        color="#59A14F",
        label="Annualized alpha",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(f"{timeframe}: mean annualized return, {bucket_label}")
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Mean annualized return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_bucket_mean_return.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_bucket_deviation(data, timeframe, bucket_label, output_dir, directory):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_deviation"],
        marker="o",
        linewidth=2,
        color="#E15759",
    )
    ax.set_title(f"{timeframe}: downside deviation, {bucket_label}")
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Downside deviation")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_bucket_downside_deviation.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_bucket_ratio(data, timeframe, bucket_label, output_dir, directory):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_information_ratio"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(f"{timeframe}: downside information ratio, {bucket_label}")
    ax.set_xlabel("Top M share (%)")
    ax.set_ylabel("Downside information ratio")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_bucket_downside_ratio.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_bucket_heatmaps(data, timeframe, output_dir, directory):
    metrics = [
        (
            "mean_annualized_alpha",
            "Annualized alpha",
            f"{timeframe}: annualized alpha by market return bucket and Top N",
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
            f"{timeframe}: downside deviation by market return bucket and Top N",
            f"{timeframe}_heatmap_downside_deviation.png",
            "YlOrRd",
            True,
            None,
            None,
        ),
        (
            "downside_information_ratio",
            "Downside information ratio",
            f"{timeframe}: DIR by market return bucket and Top N",
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
    matrix = clean.pivot_table(
        index="benchmark_return_bucket_id",
        columns="top_share",
        values=metric,
        aggfunc="mean",
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
            f"{row.benchmark_bucket_min:.1%} to {row.benchmark_bucket_max:.1%} "
            f"(avg {row.benchmark_bucket_mean:.1%})"
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
    display_values = (
        np.clip(values, clip_limits[0], clip_limits[1])
        if clip_limits is not None
        else values
    )
    fig_width = max(14, len(top_order) * 0.34)
    fig_height = max(7, len(bucket_order) * 0.55 + 2.5)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(display_values, aspect="auto", cmap=cmap, norm=norm)
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
    ax.set_title(title)
    ax.set_xlabel("Top N equivalent")
    ax.set_ylabel("Annualized benchmark return bucket")
    ax.set_xticks(np.arange(-0.5, len(top_order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(bucket_order), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.6)
    ax.tick_params(which="minor", bottom=False, left=False)
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, directory, filename), dpi=170)
    plt.close(fig)
