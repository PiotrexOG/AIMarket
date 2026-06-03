import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def plot_horizon_quantile_pearson(quantile_summary, output_dir):
    if quantile_summary.empty:
        return

    plot_data = quantile_summary.dropna(subset=["pearson"]).copy()

    if plot_data.empty:
        return

    for timeframe, timeframe_group in plot_data.groupby("timeframe"):
        fig, ax = plt.subplots(figsize=(12, 7))

        for top_percent, group in timeframe_group.groupby("top_percent"):
            group = group.sort_values("horizon_days")
            markevery = max(1, len(group) // 30)
            ax.plot(
                group["horizon_days"],
                group["pearson"],
                marker="o",
                markevery=markevery,
                linewidth=1.7,
                markersize=3,
                label=f"top {int(top_percent)}%",
            )

            best = group.loc[group["pearson"].idxmax()]
            ax.scatter(
                [best["horizon_days"]],
                [best["pearson"]],
                s=55,
                zorder=4,
            )

        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: Pearson by return horizon and score threshold")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Pearson correlation inside selected top-score group")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Score threshold")

        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "horizon_quantile_pearson",
                f"{timeframe}_pearson_by_horizon_and_top_score_share.png",
            ),
            dpi=160,
        )
        plt.close(fig)


def format_daily_top_n_label(value):
    if value == "all":
        return "top 100%"

    return f"top {int(value)}"


def plot_horizon_daily_top_n_pearson(daily_top_n_summary, output_dir):
    if daily_top_n_summary.empty:
        return

    plot_data = daily_top_n_summary.dropna(subset=["pearson"]).copy()

    if plot_data.empty:
        return

    for timeframe, timeframe_group in plot_data.groupby("timeframe"):
        fig, ax = plt.subplots(figsize=(12, 7))

        for top_n, group in timeframe_group.groupby("top_n", sort=False):
            group = group.sort_values("horizon_days")
            markevery = max(1, len(group) // 30)
            ax.plot(
                group["horizon_days"],
                group["pearson"],
                marker="o",
                markevery=markevery,
                linewidth=1.7,
                markersize=3,
                label=format_daily_top_n_label(top_n),
            )

            best = group.loc[group["pearson"].idxmax()]
            ax.scatter(
                [best["horizon_days"]],
                [best["pearson"]],
                s=55,
                zorder=4,
            )

        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_title(f"{timeframe}: Pearson by return horizon and daily top N")
        ax.set_xlabel("Return horizon in days")
        ax.set_ylabel("Pearson correlation inside selected daily top-N group")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Daily selection")

        fig.tight_layout()
        fig.savefig(
            plot_path(
                output_dir,
                "horizon_daily_top_n_pearson",
                f"{timeframe}_pearson_by_horizon_and_daily_top_n.png",
            ),
            dpi=160,
        )
        plt.close(fig)


def plot_horizon_daily_cross_section_ic(daily_ic_summary, output_dir):
    if daily_ic_summary.empty:
        return

    plot_configs = [
        {
            "folder": "horizon_daily_cross_section_pearson_ic",
            "filename_suffix": "daily_cross_section_pearson_ic",
            "columns": [
                ("mean_pearson_ic", "mean Pearson IC"),
                ("median_pearson_ic", "median Pearson IC"),
            ],
            "title": "Daily cross-sectional Pearson IC",
            "ylabel": "Pearson IC across stocks, averaged over days",
            "percent": False,
        },
        {
            "folder": "horizon_daily_cross_section_spearman_ic",
            "filename_suffix": "daily_cross_section_spearman_ic",
            "columns": [
                ("mean_spearman_ic", "mean Spearman IC"),
                ("median_spearman_ic", "median Spearman IC"),
            ],
            "title": "Daily cross-sectional Spearman IC",
            "ylabel": "Spearman IC across stocks, averaged over days",
            "percent": False,
        },
        {
            "folder": "horizon_daily_cross_section_positive_ic_share",
            "filename_suffix": "daily_cross_section_positive_ic_share",
            "columns": [
                ("positive_pearson_ic_share", "positive Pearson IC days"),
                ("positive_spearman_ic_share", "positive Spearman IC days"),
            ],
            "title": "Share of days with positive daily IC",
            "ylabel": "Share of days",
            "percent": True,
        },
    ]

    for config in plot_configs:
        available_columns = [
            item
            for item in config["columns"]
            if item[0] in daily_ic_summary.columns
        ]

        if not available_columns:
            continue

        for timeframe, timeframe_group in daily_ic_summary.groupby("timeframe"):
            fig, ax = plt.subplots(figsize=(12, 7))

            for column, label in available_columns:
                plot_data = (
                    timeframe_group
                    .dropna(subset=[column])
                    .sort_values("horizon_days")
                )

                if plot_data.empty:
                    continue

                markevery = max(1, len(plot_data) // 30)
                ax.plot(
                    plot_data["horizon_days"],
                    plot_data[column],
                    marker="o",
                    markevery=markevery,
                    linewidth=1.8,
                    markersize=3,
                    label=label,
                )

            ax.axhline(0, color="#444444", linewidth=1)
            ax.set_title(f"{timeframe}: {config['title']} by return horizon")
            ax.set_xlabel("Return horizon in days")
            ax.set_ylabel(config["ylabel"])
            ax.grid(True, alpha=0.25)
            ax.legend()

            if config["percent"]:
                ax.set_ylim(0, 1)
                ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

            fig.tight_layout()
            fig.savefig(
                plot_path(
                    output_dir,
                    config["folder"],
                    f"{timeframe}_{config['filename_suffix']}.png",
                ),
                dpi=160,
            )
            plt.close(fig)
