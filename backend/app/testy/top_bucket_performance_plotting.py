import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def plot_score_distributions(df, score_column, threshold_summary, output_dir):
    if score_column not in df.columns:
        return

    for timeframe, group in df.groupby("timeframe"):
        scores = group[score_column].dropna().sort_values()

        if scores.empty:
            continue

        mapping = threshold_summary[threshold_summary["timeframe"] == timeframe]

        fig, ax = plt.subplots(figsize=(11, 6))
        ax.hist(scores, bins=np.arange(0, 10.5, 0.5), color="#1f77b4", alpha=0.8)
        ax.axvline(scores.median(), color="#111111", linestyle="--", linewidth=2, label="median")

        for row in mapping.itertuples(index=False):
            if row.top_percent not in (10, 20, 30):
                continue
            ax.axvline(
                row.min_score,
                linestyle=":",
                linewidth=1.7,
                label=f"top {int(row.top_percent)}% >= {row.min_score:.2f}",
            )

        ax.set_title(f"{timeframe}: score distribution")
        ax.set_xlabel("Equal-weight score")
        ax.set_ylabel("Observations")
        ax.set_xlim(0, 10)
        ax.grid(True, axis="y", alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(
            plot_path(output_dir, "score_distribution", f"{timeframe}_score_histogram.png"),
            dpi=160,
        )
        plt.close(fig)

        survival = 1 - (np.arange(len(scores)) / len(scores))
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.step(scores.to_numpy(), survival, where="post", color="#1f77b4", linewidth=2)

        for row in mapping.itertuples(index=False):
            ax.scatter(row.min_score, row.top_share, s=45)
            ax.annotate(
                f"top {int(row.top_percent)}% >= {row.min_score:.2f}",
                xy=(row.min_score, row.top_share),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
            )

        ax.set_title(f"{timeframe}: share of observations at or above score threshold")
        ax.set_xlabel("Minimum score")
        ax.set_ylabel("Share of observations with score >= threshold")
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 1.02)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(
            plot_path(output_dir, "score_distribution", f"{timeframe}_score_survival_ecdf.png"),
            dpi=160,
        )
        plt.close(fig)

    if threshold_summary.empty:
        return

    fig, ax = plt.subplots(figsize=(11, 6))

    for timeframe, group in threshold_summary.groupby("timeframe"):
        group = group.sort_values("top_percent")
        ax.plot(
            group["top_percent"],
            group["min_score"],
            marker="o",
            linewidth=2,
            label=timeframe,
        )

    ax.set_title("Score cutoff represented by each top-score bucket")
    ax.set_xlabel("Selected top share")
    ax.set_ylabel("Minimum score in selected bucket")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax.set_ylim(0, 10)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, "score_distribution", "quantile_to_score_threshold.png"),
        dpi=160,
    )
    plt.close(fig)


def plot_selection_performance(
    selection_summary,
    output_dir,
    policy_column,
    policy_title,
    label_formatter,
    folder_prefix,
):
    if selection_summary.empty:
        return

    plot_configs = [
        {
            "column": "avg_return",
            "benchmark_column": "benchmark_avg_return",
            "folder": f"{folder_prefix}_avg_return",
            "title": "Average return",
            "ylabel": "Average return",
            "include_benchmark": True,
        },
        {
            "column": "excess_avg_return",
            "benchmark_column": None,
            "folder": f"{folder_prefix}_excess_return",
            "title": "Average excess return vs equal-weight benchmark",
            "ylabel": "Top bucket return minus benchmark return",
            "include_benchmark": False,
        },
        {
            "column": "annualized_excess_return",
            "benchmark_column": None,
            "folder": f"{folder_prefix}_annualized_excess_return",
            "title": "Annualized excess return vs equal-weight benchmark",
            "ylabel": "Annualized top bucket return minus benchmark return",
            "include_benchmark": False,
        },
    ]

    for config in plot_configs:
        if config["column"] not in selection_summary.columns:
            continue

        plot_data = selection_summary.dropna(subset=[config["column"]]).copy()

        if plot_data.empty:
            continue

        for timeframe, timeframe_group in plot_data.groupby("timeframe"):
            fig, ax = plt.subplots(figsize=(12, 7))

            if (
                config["include_benchmark"]
                and config["benchmark_column"] in timeframe_group.columns
            ):
                benchmark = (
                    timeframe_group[
                        ["horizon_days", config["benchmark_column"]]
                    ]
                    .drop_duplicates()
                    .dropna()
                    .sort_values("horizon_days")
                )

                if not benchmark.empty:
                    ax.plot(
                        benchmark["horizon_days"],
                        benchmark[config["benchmark_column"]],
                        color="#111111",
                        linewidth=2.2,
                        linestyle="--",
                        label="equal-weight benchmark",
                    )

            for policy_value, group in timeframe_group.groupby(policy_column):
                group = group.sort_values("horizon_days")
                markevery = max(1, len(group) // 30)
                ax.plot(
                    group["horizon_days"],
                    group[config["column"]],
                    marker="o",
                    markevery=markevery,
                    linewidth=1.7,
                    markersize=2.8,
                    label=label_formatter(policy_value),
                )

            ax.axhline(0, color="#444444", linewidth=1)
            ax.set_title(f"{timeframe}: {config['title']} by return horizon ({policy_title})")
            ax.set_xlabel("Return horizon in days")
            ax.set_ylabel(config["ylabel"])
            ax.grid(True, alpha=0.25)
            ax.legend(title=policy_title)
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

            fig.tight_layout()
            fig.savefig(
                plot_path(
                    output_dir,
                    config["folder"],
                    f"{timeframe}_{config['folder']}.png",
                ),
                dpi=160,
            )
            plt.close(fig)


def plot_top_bucket_performance(quantile_summary, output_dir):
    plot_selection_performance(
        quantile_summary,
        output_dir,
        policy_column="top_percent",
        policy_title="Top score share",
        label_formatter=lambda value: f"top {int(value)}%",
        folder_prefix="top_bucket",
    )


def plot_absolute_threshold_performance(threshold_summary, output_dir):
    plot_selection_performance(
        threshold_summary,
        output_dir,
        policy_column="score_threshold",
        policy_title="Minimum score",
        label_formatter=lambda value: f"score >= {value:.1f}",
        folder_prefix="absolute_score",
    )
