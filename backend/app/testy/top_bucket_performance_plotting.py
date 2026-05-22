import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def plot_top_bucket_performance(quantile_summary, output_dir):
    if quantile_summary.empty:
        return

    plot_configs = [
        {
            "column": "avg_return",
            "benchmark_column": "benchmark_avg_return",
            "folder": "top_bucket_avg_return",
            "title": "Average return",
            "ylabel": "Average return",
            "include_benchmark": True,
        },
        {
            "column": "excess_avg_return",
            "benchmark_column": None,
            "folder": "top_bucket_excess_return",
            "title": "Average excess return vs equal-weight benchmark",
            "ylabel": "Top bucket return minus benchmark return",
            "include_benchmark": False,
        },
        {
            "column": "annualized_excess_return",
            "benchmark_column": None,
            "folder": "top_bucket_annualized_excess_return",
            "title": "Annualized excess return vs equal-weight benchmark",
            "ylabel": "Annualized top bucket return minus benchmark return",
            "include_benchmark": False,
        },
    ]

    for config in plot_configs:
        if config["column"] not in quantile_summary.columns:
            continue

        plot_data = quantile_summary.dropna(subset=[config["column"]]).copy()

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

            for top_percent, group in timeframe_group.groupby("top_percent"):
                group = group.sort_values("horizon_days")
                markevery = max(1, len(group) // 30)
                ax.plot(
                    group["horizon_days"],
                    group[config["column"]],
                    marker="o",
                    markevery=markevery,
                    linewidth=1.7,
                    markersize=2.8,
                    label=f"top {int(top_percent)}%",
                )

            ax.axhline(0, color="#444444", linewidth=1)
            ax.set_title(f"{timeframe}: {config['title']} by return horizon")
            ax.set_xlabel("Return horizon in days")
            ax.set_ylabel(config["ylabel"])
            ax.grid(True, alpha=0.25)
            ax.legend(title="Score bucket")
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
