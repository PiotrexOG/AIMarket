import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from app.testy.score_tests.common.output_paths import (
    CAPM_ALPHA_BETA_DIR,
    CAPM_TOP_M_SELECTION_SECTION,
    horizon_dir,
)
from app.testy.score_tests.common.plotting import (
    add_sample_size_note,
    plot_path,
    set_percent_x_axis,
    timeframe_label,
)


def _plot_beta(data, output_dir, directory, timeframe):
    clean = data.dropna(subset=["top_percent", "beta"]).sort_values(
        "top_percent"
    )
    if clean.empty:
        return None

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        clean["top_percent"],
        clean["beta"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
    )
    ax.axhline(
        1.0,
        color="#9C755F",
        linewidth=1.5,
        linestyle="--",
        label="Benchmark M=100%: beta=1",
    )
    ax.set_title(
        f"{timeframe_label(timeframe, clean)}: beta CAPM portfela "
        "najlepszych M (%) spółek względem benchmarku M=100%, "
        "horyzonty ważone jednakowo"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Beta CAPM")
    ax.grid(True, alpha=0.25)
    ax.legend()
    add_sample_size_note(
        fig,
        clean,
        "observation_count",
        per="punkt M(%) spółek (suma obserwacji ze wszystkich horyzontów)",
    )
    fig.tight_layout()
    output_path = plot_path(
        output_dir,
        directory,
        f"{timeframe}_beta.png",
    )
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def _plot_jensen_alpha(data, output_dir, directory, timeframe):
    clean = data.dropna(
        subset=["top_percent", "annualized_jensen_alpha"]
    ).sort_values("top_percent")
    if clean.empty:
        return None

    risk_free_rate = clean["annual_risk_free_rate"].dropna()
    risk_free_rate = (
        float(risk_free_rate.iloc[0]) if not risk_free_rate.empty else 0.0
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        clean["top_percent"],
        clean["annualized_jensen_alpha"],
        marker="o",
        linewidth=2,
        color="#E15759",
    )
    ax.axhline(0.0, color="#444444", linewidth=1)
    ax.set_title(
        f"{timeframe_label(timeframe, clean)}: roczna alfa Jensena "
        "portfela najlepszych M (%) spółek względem benchmarku M=100% "
        f"(R_f={risk_free_rate:.0%}), horyzonty ważone jednakowo"
    )
    ax.set_xlabel("Udział najlepszych M (%) spółek")
    set_percent_x_axis(ax, xmax=100.0)
    ax.set_ylabel("Roczna alfa Jensena")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.25)
    add_sample_size_note(
        fig,
        clean,
        "observation_count",
        per="punkt M(%) spółek (suma obserwacji ze wszystkich horyzontów)",
    )
    fig.tight_layout()
    output_path = plot_path(
        output_dir,
        directory,
        f"{timeframe}_jensen_alpha.png",
    )
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot(results, output_dir, horizon_label):
    if not results:
        return []
    analysis = results.get("analysis")
    if analysis is None or analysis.empty:
        return []

    directory = horizon_dir(
        CAPM_ALPHA_BETA_DIR,
        horizon_label,
        CAPM_TOP_M_SELECTION_SECTION,
    )
    output_paths = []
    for timeframe, timeframe_data in analysis.groupby("timeframe", sort=True):
        paths = (
            _plot_beta(timeframe_data, output_dir, directory, timeframe),
            _plot_jensen_alpha(
                timeframe_data,
                output_dir,
                directory,
                timeframe,
            ),
        )
        output_paths.extend(path for path in paths if path is not None)
    return output_paths
