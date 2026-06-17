import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd


TIMEFRAME_HORIZON_LIMITS = {
    "short_term_14d": (7, 21),
    "medium_term_50d": (25, 75),
    "long_term_200d": (100, 300),
}


def plot_path(output_dir, plot_type, filename):
    directory = output_dir / plot_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def annualize_return(total_return, horizon_days):
    if total_return is None or horizon_days <= 0:
        return None

    try:
        total_return = float(total_return)
    except (TypeError, ValueError):
        return None

    if total_return <= -1:
        return None

    return float((1 + total_return) ** (365 / horizon_days) - 1)


def add_annualized_return_column(df):
    result = df.copy()
    result["annualized_return"] = [
        annualize_return(row.avg_return, row.horizon_days)
        for row in result.itertuples(index=False)
    ]
    return result


def limit_horizon_range(timeframe, df):
    limits = TIMEFRAME_HORIZON_LIMITS.get(timeframe)

    if limits is None:
        return df

    start_day, end_day = limits
    return df[
        (df["horizon_days"] >= start_day)
        & (df["horizon_days"] <= end_day)
    ]


def _plot_bucket_lines(
    timeframe_data,
    output_dir,
    plot_type,
    filename,
    title,
    bucket_order,
):
    if timeframe_data.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.RdYlGn_r(np.linspace(0.05, 0.95, len(bucket_order)))

    for color, bucket in zip(colors, bucket_order):
        group = timeframe_data[timeframe_data["bucket"] == bucket].sort_values(
            "horizon_days"
        )

        if group.empty:
            continue

        ax.plot(
            group["horizon_days"],
            group["annualized_return"],
            marker="o",
            markevery=max(1, len(group) // 30),
            linewidth=1.8,
            markersize=3,
            color=color,
            label=bucket,
        )

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("Return horizon in days")
    ax.set_ylabel("Annualized return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    ax.legend(title="Bucket", ncol=2)
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, plot_type, filename), dpi=160)
    plt.close(fig)


def _plot_bucket_average(
    timeframe_data,
    output_dir,
    plot_type,
    filename,
    title,
    bucket_order,
    score_range_columns=None,
):
    if timeframe_data.empty:
        return

    aggregations = {"annualized_return": ("annualized_return", "mean")}

    if score_range_columns is not None:
        min_column, max_column = score_range_columns
        aggregations["avg_score_min"] = (min_column, "mean")
        aggregations["avg_score_max"] = (max_column, "mean")

    average_data = timeframe_data.groupby("bucket", as_index=False).agg(
        **aggregations
    )
    average_data["bucket"] = pd.Categorical(
        average_data["bucket"],
        categories=bucket_order,
        ordered=True,
    )
    average_data = average_data.sort_values("bucket").dropna(
        subset=["annualized_return"]
    )

    if average_data.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 7))
    labels = average_data["bucket"].astype(str)

    if score_range_columns is not None:
        labels = [
            f"{row.bucket}\navg score {row.avg_score_min:.1f}-{row.avg_score_max:.1f}"
            for row in average_data.itertuples(index=False)
        ]

    ax.bar(
        labels,
        average_data["annualized_return"],
        color="#4C78A8",
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("Bucket")
    ax.set_ylabel("Mean annualized return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(plot_path(output_dir, plot_type, filename), dpi=160)
    plt.close(fig)


def _plot_fractional_top_t_stat_average(timeframe_data, output_dir, timeframe):
    clean = timeframe_data.dropna(subset=["top_percent"]).copy()

    if clean.empty:
        return

    average_data = (
        clean.groupby("top_percent", as_index=False)
        .agg(
            t_stat=("t_stat", "mean"),
            excess_t_stat=("excess_t_stat", "mean"),
        )
        .sort_values("top_percent")
    )

    fig, ax = plt.subplots(figsize=(12, 7))

    for column, label in [
        ("t_stat", "raw return t-stat"),
        ("excess_t_stat", "excess vs All 18 t-stat"),
    ]:
        group = average_data.dropna(subset=[column])

        if group.empty:
            continue

        ax.plot(
            group["top_percent"],
            group[column],
            marker="o",
            linewidth=1.8,
            markersize=4,
            label=label,
        )

    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(f"{timeframe}: A4 mean t-stat by fractional Top M%")
    ax.set_xlabel("Weekly selected top share (%)")
    ax.set_ylabel("Mean t-stat across horizons")
    ax.grid(True, alpha=0.25)
    ax.legend(title="T-test")
    fig.tight_layout()
    fig.savefig(
        plot_path(
            output_dir,
            "weekly_analysis",
            f"{timeframe}_a4_fractional_top_t_stat_average.png",
        ),
        dpi=160,
    )
    plt.close(fig)


def _plot_fractional_top_summary_average(
    timeframe_data,
    output_dir,
    timeframe,
    value_column,
    label,
    filename_suffix,
    y_formatter=None,
):
    clean = timeframe_data.dropna(subset=["top_percent", value_column]).copy()

    if clean.empty:
        return

    average_data = (
        clean.groupby("top_percent", as_index=False)
        .agg(value=(value_column, "mean"))
        .sort_values("top_percent")
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        average_data["top_percent"],
        average_data["value"],
        marker="o",
        linewidth=1.8,
        markersize=4,
    )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(f"{timeframe}: A4 mean {label} by fractional Top M%")
    ax.set_xlabel("Weekly selected top share (%)")
    ax.set_ylabel(f"Mean {label} across horizons")

    if y_formatter is not None:
        ax.yaxis.set_major_formatter(y_formatter)

    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        plot_path(
            output_dir,
            "weekly_analysis",
            f"{timeframe}_a4_fractional_top_{filename_suffix}_average.png",
        ),
        dpi=160,
    )
    plt.close(fig)


def _plot_fractional_top_t_stat_heatmap(
    timeframe_data,
    output_dir,
    timeframe,
    value_column,
    label,
    filename_suffix,
):
    clean = timeframe_data.dropna(
        subset=["top_percent", "horizon_days", value_column]
    ).copy()

    if clean.empty:
        return

    pivot = clean.pivot_table(
        index="horizon_days",
        columns="top_percent",
        values=value_column,
        aggfunc="mean",
    ).sort_index()

    if pivot.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 7))
    values = pivot.to_numpy(dtype=float)
    finite_values = values[np.isfinite(values)]
    color_limit = (
        max(abs(finite_values.min()), abs(finite_values.max()))
        if finite_values.size
        else 1.0
    )

    image = ax.imshow(
        values,
        aspect="auto",
        cmap="RdYlGn",
        vmin=-color_limit,
        vmax=color_limit,
        origin="lower",
    )
    ax.set_title(f"{timeframe}: A4 {label} heatmap")
    ax.set_xlabel("Weekly selected top share (%)")
    ax.set_ylabel("Return horizon in days")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([f"{value:.1f}" for value in pivot.columns], rotation=45)

    y_tick_count = min(12, len(pivot.index))
    y_tick_positions = np.linspace(0, len(pivot.index) - 1, y_tick_count, dtype=int)
    ax.set_yticks(y_tick_positions)
    ax.set_yticklabels([
        str(int(pivot.index[position]))
        for position in y_tick_positions
    ])
    fig.colorbar(image, ax=ax, label=label)
    fig.tight_layout()
    fig.savefig(
        plot_path(
            output_dir,
            "weekly_analysis",
            f"{timeframe}_a4_fractional_top_{filename_suffix}_heatmap.png",
        ),
        dpi=160,
    )
    plt.close(fig)


def plot_weekly_analysis(
    weekly_analysis,
    output_dir,
    weekly_bucket_analysis=None,
    weekly_fractional_top_analysis=None,
):
    if not weekly_analysis.empty:
        top_n_data = weekly_analysis[
            (weekly_analysis["test"] == "A1_top_n")
            & (weekly_analysis["bucket"] != "All 18")
        ].dropna(subset=["avg_return"]).copy()
        top_n_data = add_annualized_return_column(top_n_data).dropna(
            subset=["annualized_return"]
        )

        if not top_n_data.empty:
            for timeframe, timeframe_data in top_n_data.groupby("timeframe"):
                timeframe_data = limit_horizon_range(timeframe, timeframe_data)

                if timeframe_data.empty:
                    continue

                fig, ax = plt.subplots(figsize=(12, 7))

                for bucket, group in timeframe_data.groupby("bucket", sort=False):
                    group = group.sort_values("horizon_days")
                    ax.plot(
                        group["horizon_days"],
                        group["annualized_return"],
                        marker="o",
                        markevery=max(1, len(group) // 30),
                        linewidth=1.8,
                        markersize=3,
                        label=bucket,
                    )

                ax.axhline(0, color="#444444", linewidth=1)
                ax.set_title(f"{timeframe}: weekly annualized return by Top N")
                ax.set_xlabel("Return horizon in days")
                ax.set_ylabel("Annualized return")
                ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
                ax.grid(True, alpha=0.25)
                ax.legend(title="Weekly selection")
                fig.tight_layout()
                fig.savefig(
                    plot_path(
                        output_dir,
                        "weekly_analysis",
                        f"{timeframe}_a1_top_n_annualized_return.png",
                    ),
                    dpi=160,
                )
                plt.close(fig)

    if weekly_bucket_analysis is not None and not weekly_bucket_analysis.empty:
        bucket_data = weekly_bucket_analysis.dropna(subset=["avg_return"]).copy()
        bucket_data = add_annualized_return_column(bucket_data).dropna(
            subset=["annualized_return"]
        )

        for timeframe, timeframe_data in bucket_data.groupby("timeframe"):
            timeframe_data = limit_horizon_range(timeframe, timeframe_data)

            if timeframe_data.empty:
                continue

            bucket_order = (
                timeframe_data[["bucket", "bucket_start_rank"]]
                .drop_duplicates()
                .sort_values("bucket_start_rank")["bucket"]
                .tolist()
            )
            _plot_bucket_lines(
                timeframe_data,
                output_dir,
                "weekly_analysis",
                f"{timeframe}_a3_rank_bucket_annualized_return_lines.png",
                f"{timeframe}: weekly rank bucket annualized return",
                bucket_order,
            )
            _plot_bucket_average(
                timeframe_data,
                output_dir,
                "weekly_analysis",
                f"{timeframe}_a3_rank_bucket_annualized_return_average.png",
                f"{timeframe}: weekly rank bucket mean annualized return",
                bucket_order,
                score_range_columns=("avg_score_min", "avg_score_max"),
            )

    if weekly_fractional_top_analysis is not None and not weekly_fractional_top_analysis.empty:
        for timeframe, timeframe_data in weekly_fractional_top_analysis.groupby("timeframe"):
            timeframe_data = limit_horizon_range(timeframe, timeframe_data)

            if timeframe_data.empty:
                continue

            _plot_fractional_top_t_stat_average(
                timeframe_data,
                output_dir,
                timeframe,
            )
            _plot_fractional_top_summary_average(
                timeframe_data,
                output_dir,
                timeframe,
                "avg_return",
                "weekly return",
                "mean_return",
                y_formatter=mtick.PercentFormatter(1.0),
            )
            _plot_fractional_top_summary_average(
                timeframe_data,
                output_dir,
                timeframe,
                "std_return",
                "weekly return standard deviation",
                "std_return",
                y_formatter=mtick.PercentFormatter(1.0),
            )
            _plot_fractional_top_t_stat_heatmap(
                timeframe_data,
                output_dir,
                timeframe,
                "t_stat",
                "raw return t-stat",
                "raw_t_stat",
            )
            _plot_fractional_top_t_stat_heatmap(
                timeframe_data,
                output_dir,
                timeframe,
                "excess_t_stat",
                "excess vs All 18 t-stat",
                "excess_t_stat",
            )

    if weekly_analysis.empty:
        return

    pearson_data = weekly_analysis[
        weekly_analysis["test"] == "A2_weekly_pearson"
    ].dropna(subset=["pearson"]).copy()

    if pearson_data.empty:
        return

    for timeframe, timeframe_data in pearson_data.groupby("timeframe"):
        timeframe_data = limit_horizon_range(timeframe, timeframe_data)

        if timeframe_data.empty:
            continue

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


def plot_global_analysis(global_analysis, output_dir, global_score_bucket_analysis=None):
    if not global_analysis.empty:
        top_percent_data = global_analysis[
            (global_analysis["test"] == "B1_top_percent")
            & (global_analysis["bucket"] != "All")
        ].dropna(subset=["avg_return"]).copy()
        top_percent_data = add_annualized_return_column(top_percent_data).dropna(
            subset=["annualized_return"]
        )

        if not top_percent_data.empty:
            for timeframe, timeframe_data in top_percent_data.groupby("timeframe"):
                timeframe_data = limit_horizon_range(timeframe, timeframe_data)

                if timeframe_data.empty:
                    continue

                fig, ax = plt.subplots(figsize=(12, 7))

                for bucket, group in timeframe_data.groupby("bucket", sort=False):
                    group = group.sort_values("horizon_days")
                    ax.plot(
                        group["horizon_days"],
                        group["annualized_return"],
                        marker="o",
                        markevery=max(1, len(group) // 30),
                        linewidth=1.8,
                        markersize=3,
                        label=bucket,
                    )

                ax.axhline(0, color="#444444", linewidth=1)
                ax.set_title(f"{timeframe}: global annualized return by Top X percent")
                ax.set_xlabel("Return horizon in days")
                ax.set_ylabel("Annualized return")
                ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
                ax.grid(True, alpha=0.25)
                ax.legend(title="Global selection")
                fig.tight_layout()
                fig.savefig(
                    plot_path(
                        output_dir,
                        "global_analysis",
                        f"{timeframe}_b1_top_percent_annualized_return.png",
                    ),
                    dpi=160,
                )
                plt.close(fig)

    if global_score_bucket_analysis is not None and not global_score_bucket_analysis.empty:
        score_bucket_data = global_score_bucket_analysis.dropna(
            subset=["avg_return"]
        ).copy()
        score_bucket_data = add_annualized_return_column(score_bucket_data).dropna(
            subset=["annualized_return"]
        )

        for timeframe, timeframe_data in score_bucket_data.groupby("timeframe"):
            timeframe_data = limit_horizon_range(timeframe, timeframe_data)

            if timeframe_data.empty:
                continue

            bucket_order = (
                timeframe_data[
                    ["bucket", "bucket_start_percent", "bucket_end_percent"]
                ]
                .drop_duplicates()
                .sort_values(["bucket_start_percent", "bucket_end_percent"])["bucket"]
                .tolist()
            )
            _plot_bucket_lines(
                timeframe_data,
                output_dir,
                "global_analysis",
                f"{timeframe}_b3_score_bucket_annualized_return_lines.png",
                f"{timeframe}: global score bucket annualized return",
                bucket_order,
            )
            _plot_bucket_average(
                timeframe_data,
                output_dir,
                "global_analysis",
                f"{timeframe}_b3_score_bucket_annualized_return_average.png",
                f"{timeframe}: global score bucket mean annualized return",
                bucket_order,
            )

    if global_analysis.empty:
        return

    pearson_data = global_analysis[
        global_analysis["test"] == "B2_global_pearson"
    ].dropna(subset=["pearson"]).copy()

    if pearson_data.empty:
        return

    for timeframe, timeframe_data in pearson_data.groupby("timeframe"):
        timeframe_data = limit_horizon_range(timeframe, timeframe_data)

        if timeframe_data.empty:
            continue

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
