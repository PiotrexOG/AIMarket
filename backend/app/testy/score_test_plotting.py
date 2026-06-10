import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename

def plot_weekly_analysis(weekly_analysis, output_dir):
    if weekly_analysis.empty:
        return

    top_n_data = weekly_analysis[
        weekly_analysis["test"] == "A1_top_n"
    ].dropna(subset=["avg_return"]).copy()

    if not top_n_data.empty:
        for timeframe, timeframe_data in top_n_data.groupby("timeframe"):
            fig, ax = plt.subplots(figsize=(12, 7))

            for bucket, group in timeframe_data.groupby("bucket", sort=False):
                group = group.sort_values("horizon_days")
                ax.plot(
                    group["horizon_days"],
                    group["avg_return"],
                    marker="o",
                    markevery=max(1, len(group) // 30),
                    linewidth=1.8,
                    markersize=3,
                    label=bucket,
                )

            ax.axhline(0, color="#444444", linewidth=1)
            ax.set_title(f"{timeframe}: weekly average return by Top N")
            ax.set_xlabel("Return horizon in days")
            ax.set_ylabel("Average weekly portfolio return")
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            ax.grid(True, alpha=0.25)
            ax.legend(title="Weekly selection")
            fig.tight_layout()
            fig.savefig(
                plot_path(
                    output_dir,
                    "weekly_analysis",
                    f"{timeframe}_a1_top_n_avg_return.png",
                ),
                dpi=160,
            )
            plt.close(fig)

    pearson_data = weekly_analysis[
        weekly_analysis["test"] == "A2_weekly_pearson"
    ].dropna(subset=["pearson"]).copy()

    if pearson_data.empty:
        return

    for timeframe, timeframe_data in pearson_data.groupby("timeframe"):
        fig, ax = plt.subplots(figsize=(12, 7))

        for metric, group in timeframe_data.groupby("metric", sort=False):
            group = group.sort_values("horizon_days")
            ax.plot(
                group["horizon_days"],
                group["pearson"],
                marker="o",
                markevery=max(1, len(group) // 30),
                linewidth=1.8,
                markersize=3,
                label=metric,
            )

        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: mean weekly Pearson correlation")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Mean weekly Pearson correlation")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Metric")
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "weekly_analysis",
                f"{timeframe}_a2_weekly_pearson.png",
            ),
            dpi=160,
        )
        plt.close(fig)


def plot_global_analysis(global_analysis, output_dir):
    if global_analysis.empty:
        return

    top_percent_data = global_analysis[
        global_analysis["test"] == "B1_top_percent"
    ].dropna(subset=["avg_return"]).copy()

    if not top_percent_data.empty:
        for timeframe, timeframe_data in top_percent_data.groupby("timeframe"):
            fig, ax = plt.subplots(figsize=(12, 7))

            for bucket, group in timeframe_data.groupby("bucket", sort=False):
                group = group.sort_values("horizon_days")
                ax.plot(
                    group["horizon_days"],
                    group["avg_return"],
                    marker="o",
                    markevery=max(1, len(group) // 30),
                    linewidth=1.8,
                    markersize=3,
                    label=bucket,
                )

            ax.axhline(0, color="#444444", linewidth=1)
            ax.set_title(f"{timeframe}: global average return by Top X percent")
            ax.set_xlabel("Return horizon in days")
            ax.set_ylabel("Average return")
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            ax.grid(True, alpha=0.25)
            ax.legend(title="Global selection")
            fig.tight_layout()
            fig.savefig(
                plot_path(
                    output_dir,
                    "global_analysis",
                    f"{timeframe}_b1_top_percent_avg_return.png",
                ),
                dpi=160,
            )
            plt.close(fig)

    pearson_data = global_analysis[
        global_analysis["test"] == "B2_global_pearson"
    ].dropna(subset=["pearson"]).copy()

    if pearson_data.empty:
        return

    for timeframe, timeframe_data in pearson_data.groupby("timeframe"):
        fig, ax = plt.subplots(figsize=(12, 7))

        for metric, group in timeframe_data.groupby("metric", sort=False):
            group = group.sort_values("horizon_days")
            ax.plot(
                group["horizon_days"],
                group["pearson"],
                marker="o",
                markevery=max(1, len(group) // 30),
                linewidth=1.8,
                markersize=3,
                label=metric,
            )

        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: global Pearson correlation")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Pearson correlation")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Metric")
        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "global_analysis",
                f"{timeframe}_b2_global_pearson.png",
            ),
            dpi=160,
        )
        plt.close(fig)
