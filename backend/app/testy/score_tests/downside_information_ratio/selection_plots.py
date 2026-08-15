import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from app.testy.score_tests.common.plotting import (
    plot_path,
    set_percent_x_axis,
    timeframe_label,
)
from app.testy.score_tests.common.output_paths import (
    DOWNSIDE_INFORMATION_RATIO_DIR,
    DOWNSIDE_TOP_M_SELECTION_SECTION,
    horizon_dir,
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

        plot_directory = horizon_dir(
            DOWNSIDE_INFORMATION_RATIO_DIR,
            horizon_label,
            DOWNSIDE_TOP_M_SELECTION_SECTION,
        )
        _plot_returns(clean, timeframe, output_dir, plot_directory, horizon_label)
        _plot_deviation(clean, timeframe, output_dir, plot_directory, horizon_label)
        _plot_ratio(clean, timeframe, output_dir, plot_directory, horizon_label)


def _plot_returns(data, timeframe, output_dir, directory, horizon_label):
    title_timeframe = timeframe_label(timeframe)
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
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{title_timeframe}: Średnia roczna stopa zwrotu "
        f"strategii najlepszych M (%) spółek i benchmarku, "
        f"równo ważone horyzonty {horizon_label}"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Średnia roczna stopa zwrotu")
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
    title_timeframe = timeframe_label(timeframe)
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
        f"dla najlepszych M (%) spółek, równo ważone horyzonty {horizon_label}"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Średnie downside deviation")

    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        plot_path(output_dir, directory, f"{timeframe}_mean_downside_deviation.png"),
        dpi=160,
    )
    plt.close(fig)


def _plot_ratio(data, timeframe, output_dir, directory, horizon_label):
    title_timeframe = timeframe_label(timeframe)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["top_percent"],
        data["downside_information_ratio"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
        label="Wskaźnik DIR",
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
            label="Stabilny zakres",
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
            label=f"Stabilna rekomendacja: {point['top_percent']:.2f}%",
        )
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_title(
        f"{title_timeframe}: wskaźnik DIR nadwyżkowego zwrotu "
        f"według najlepszych M (%) spółek, równo ważone horyzonty {horizon_label}"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Wskaźnik DIR")
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
