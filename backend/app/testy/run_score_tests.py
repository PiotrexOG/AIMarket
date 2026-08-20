import sys
import types
from pathlib import Path

import pandas as pd


ROOT_FOLDER = Path(__file__).resolve().parents[2]
APP_FOLDER = Path(__file__).resolve().parents[1]
TESTY_FOLDER = Path(__file__).resolve().parent

for path in [ROOT_FOLDER, APP_FOLDER, TESTY_FOLDER]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

app_module = types.ModuleType("app")
app_module.__path__ = [str(APP_FOLDER)]
sys.modules["app"] = app_module

from score_observations import build_dataframe, load_json
from score_tests.global_score_calibration.analysis import (
    calculate as calculate_global_score_calibration,
)
from score_tests.global_score_calibration.information_coefficient import (
    build_correlation_output as build_global_correlation_output,
)
from score_tests.global_score_calibration.plotting import (
    plot as plot_global_score_calibration,
)
from score_tests.global_score_calibration.score_percentile_buckets import (
    build_output as build_global_bucket_output,
    calculate as calculate_global_score_buckets,
    plot as plot_global_score_buckets,
)
from score_tests.global_score_calibration.top_percent_selection import (
    build_top_percent_output,
)
from score_tests.common.context import ScoreTestContext
from score_tests.common.data import (
    add_weekly_score_metrics,
    build_horizon_weeks,
    build_return_panel,
    build_timeframe_score_observations,
)
from score_tests.common.io import save_csv_for_excel
from score_tests.common.output_paths import (
    DOWNSIDE_BENCHMARK_RETURN_BUCKETS_SECTION,
    DOWNSIDE_INFORMATION_RATIO_DIR,
    DOWNSIDE_TOP_M_SELECTION_SECTION,
    GLOBAL_INFORMATION_COEFFICIENT_DIR,
    GLOBAL_SCORE_PERCENTILE_BUCKETS_DIR,
    GLOBAL_TOP_PERCENT_SELECTION_DIR,
    POST_ENTRY_LIVE_PROGRESS_SECTION,
    POST_ENTRY_SCORE_PATH_DIR,
    POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
    POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION,
    TICKER_PERCENTILE_HISTORY_DIR,
    WEEKLY_INFORMATION_COEFFICIENT_DIR,
    WEEKLY_RANK_BUCKET_RETURNS_DIR,
    WEEKLY_TOP_N_SELECTION_DIR,
    horizon_dir,
)
from score_tests.downside_information_ratio.calculation import (
    calculate as calculate_downside_information_ratio,
)
from score_tests.downside_information_ratio.plotting import (
    plot as plot_downside_information_ratio,
    plot_benchmark_return_buckets as plot_downside_information_ratio_buckets,
)
from score_tests.post_entry_score_path.calculation import (
    calculate as calculate_post_entry_score_path,
)
from score_tests.post_entry_score_path.plotting import (
    plot as plot_post_entry_score_path,
)
from score_tests.ticker_percentile_history.calculation import (
    calculate as calculate_ticker_percentile_history,
)
from score_tests.ticker_percentile_history.plotting import (
    plot as plot_ticker_percentile_history,
)
from score_tests.weekly_cross_section.analysis import (
    calculate as calculate_weekly_cross_section,
)
from score_tests.weekly_cross_section.information_coefficient import (
    build_correlation_output as build_weekly_correlation_output,
)
from score_tests.weekly_cross_section.plotting import (
    plot as plot_weekly_cross_section,
    plot_weekly_information_coefficient,
)
from score_tests.weekly_cross_section.rank_bucket_returns import (
    build_output as build_weekly_bucket_output,
    calculate as calculate_weekly_rank_buckets,
    plot as plot_weekly_rank_buckets,
)
from score_tests.weekly_cross_section.top_n_selection import build_top_n_output


CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"
INPUT_FILE = CROSS_SECTION_DIR / "score_observations.json"
RESULTS_DIR = ROOT_FOLDER / "data" / "results"
PLOTS_OUTPUT_DIR = RESULTS_DIR / "plots"
DATA_OUTPUT_DIR = RESULTS_DIR / "data"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"

ENABLED_TESTS = {
    "A1_A2_weekly_top_n_and_correlation": True,
    "A3_weekly_rank_buckets": True,
    "downside_information_ratio": True,
    "post_entry_score_path": True,
    "ticker_percentile_history": True,
    "B1_B2_global_top_percent_and_correlation": True,
    "B3_global_score_buckets": True,
}

ENABLED_TIMEFRAMES = {
    "short_term_14d": False,
    "medium_term_50d": False,
    "long_term_200d": True,
}

HORIZON_WEEK_RANGES = {
    "short_term_14d": (1, 3),
    "medium_term_50d": (4, 10),
    "long_term_200d": (21, 35),
    #"long_term_200d": (26, 30),
}

POST_ENTRY_SCORE_PATH_VARIANTS = (
    {
        "slug": "entry_min_score_percentile_70",
        "entry_min_score_percentile": 0.70,
    },
    {
        "slug": "all_scores",
        "entry_min_score_percentile": 0.0,
    },
)


def migrate_csv_files_from_plots_directory():
    if not PLOTS_OUTPUT_DIR.exists():
        return []

    moved_files = []
    for source in PLOTS_OUTPUT_DIR.rglob("*.csv"):
        target = DATA_OUTPUT_DIR / source.relative_to(PLOTS_OUTPUT_DIR)
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        moved_files.append(target)
    return moved_files


def filter_enabled_timeframes(df):
    enabled = [
        timeframe
        for timeframe, is_enabled in ENABLED_TIMEFRAMES.items()
        if is_enabled
    ]
    return (
        df[df["timeframe"].isin(enabled)].copy()
        if enabled
        else df.iloc[0:0].copy()
    )


def enabled_horizon_week_ranges():
    return {
        timeframe: HORIZON_WEEK_RANGES[timeframe]
        for timeframe, is_enabled in ENABLED_TIMEFRAMES.items()
        if is_enabled and timeframe in HORIZON_WEEK_RANGES
    }


def all_timeframe_horizon_week_ranges():
    return {
        timeframe: HORIZON_WEEK_RANGES[timeframe]
        for timeframe in ENABLED_TIMEFRAMES
        if timeframe in HORIZON_WEEK_RANGES
    }


def horizon_weeks_from_ranges(horizon_week_ranges):
    weeks = {
        week
        for start_week, end_week in horizon_week_ranges.values()
        for week in range(start_week, end_week + 1)
    }
    return sorted(weeks)


def enabled_timeframe_label():
    enabled = [
        timeframe
        for timeframe, is_enabled in ENABLED_TIMEFRAMES.items()
        if is_enabled
    ]
    if len(enabled) == 1:
        return enabled[0]
    return "_".join(enabled) if enabled else "all_timeframes"


def horizon_week_label():
    ranges = enabled_horizon_week_ranges()
    if len(ranges) == 1:
        start_week, end_week = next(iter(ranges.values()))
        return f"{start_week}-{end_week}w"
    return "_".join(
        f"{timeframe}_{start_week}-{end_week}w"
        for timeframe, (start_week, end_week) in ranges.items()
    )


def empty_post_entry_score_path_result():
    return {
        "observations": pd.DataFrame(),
        "horizon_alpha_average": pd.DataFrame(),
        "live_progress_observations": pd.DataFrame(),
        "live_progress_alpha_average": pd.DataFrame(),
        "switch_to_benchmark_thresholds": pd.DataFrame(),
    }


def run_configured_score_tests(context):
    results = {
        "a1_a2": pd.DataFrame(),
        "a3": pd.DataFrame(),
        "downside_information_ratio": {
            "analysis": pd.DataFrame(),
            "by_horizon": pd.DataFrame(),
            "observations": pd.DataFrame(),
            "benchmark_return_buckets": pd.DataFrame(),
        },
        "post_entry_score_path": {
            variant["slug"]: empty_post_entry_score_path_result()
            for variant in POST_ENTRY_SCORE_PATH_VARIANTS
        },
        "ticker_percentile_history": {
            "metrics": pd.DataFrame(),
            "forward_return_points": pd.DataFrame(),
            "forward_return_horizon_points": pd.DataFrame(),
            "prices": pd.DataFrame(),
        },
        "b1_b2": pd.DataFrame(),
        "b3": pd.DataFrame(),
    }

    if ENABLED_TESTS["A1_A2_weekly_top_n_and_correlation"]:
        results["a1_a2"] = calculate_weekly_cross_section(
            context,
            horizon_week_ranges=enabled_horizon_week_ranges(),
        )
    if ENABLED_TESTS["A3_weekly_rank_buckets"]:
        results["a3"] = calculate_weekly_rank_buckets(
            context,
            horizon_week_ranges=enabled_horizon_week_ranges(),
        )
    if ENABLED_TESTS["downside_information_ratio"]:
        results["downside_information_ratio"] = (
            calculate_downside_information_ratio(
                context,
                horizon_week_ranges=enabled_horizon_week_ranges(),
            )
        )
    if ENABLED_TESTS["post_entry_score_path"]:
        results["post_entry_score_path"] = {
            variant["slug"]: calculate_post_entry_score_path(
                context,
                horizon_week_ranges=enabled_horizon_week_ranges(),
                entry_min_score_percentile=variant[
                    "entry_min_score_percentile"
                ],
            )
            for variant in POST_ENTRY_SCORE_PATH_VARIANTS
        }
    if ENABLED_TESTS["ticker_percentile_history"]:
        results["ticker_percentile_history"] = (
            calculate_ticker_percentile_history(
                context,
                horizon_week_ranges=enabled_horizon_week_ranges(),
            )
        )
    if ENABLED_TESTS["B1_B2_global_top_percent_and_correlation"]:
        results["b1_b2"] = calculate_global_score_calibration(
            context,
            horizon_week_ranges=enabled_horizon_week_ranges(),
        )
    if ENABLED_TESTS["B3_global_score_buckets"]:
        results["b3"] = calculate_global_score_buckets(
            context,
            horizon_week_ranges=enabled_horizon_week_ranges(),
        )

    return results


def save_analysis_outputs(results, output_dir):
    outputs = {}
    horizon_label = horizon_week_label()

    if ENABLED_TESTS["A1_A2_weekly_top_n_and_correlation"]:
        outputs.update({
            WEEKLY_INFORMATION_COEFFICIENT_DIR
            / "weekly_information_coefficient_analysis.csv": (
                build_weekly_correlation_output(results["a1_a2"])
            ),
            WEEKLY_TOP_N_SELECTION_DIR / "weekly_top_n_return_analysis.csv": (
                build_top_n_output(results["a1_a2"])
            ),
        })

    if ENABLED_TESTS["A3_weekly_rank_buckets"]:
        outputs[
            WEEKLY_RANK_BUCKET_RETURNS_DIR
            / "weekly_rank_bucket_return_analysis.csv"
        ] = (
            build_weekly_bucket_output(results["a3"])
        )

    if ENABLED_TESTS["downside_information_ratio"]:
        ratio = results["downside_information_ratio"]
        ratio_top_m_dir = horizon_dir(
            DOWNSIDE_INFORMATION_RATIO_DIR,
            horizon_label,
            DOWNSIDE_TOP_M_SELECTION_SECTION,
        )
        ratio_benchmark_dir = horizon_dir(
            DOWNSIDE_INFORMATION_RATIO_DIR,
            horizon_label,
            DOWNSIDE_BENCHMARK_RETURN_BUCKETS_SECTION,
        )
        outputs.update({
            ratio_top_m_dir / "downside_information_ratio_analysis.csv": (
                ratio["analysis"]
            ),
            ratio_top_m_dir / "downside_information_ratio_by_horizon.csv": (
                ratio["by_horizon"]
            ),
            ratio_top_m_dir / "downside_information_ratio_observations.csv": (
                ratio["observations"]
            ),
            ratio_benchmark_dir
            / "downside_information_ratio_benchmark_return_buckets.csv": (
                ratio["benchmark_return_buckets"]
            ),
        })

    if ENABLED_TESTS["post_entry_score_path"]:
        for variant_slug, path in results["post_entry_score_path"].items():
            path_observations_dir = horizon_dir(
                POST_ENTRY_SCORE_PATH_DIR,
                horizon_label,
                variant_slug,
                POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
            )
            path_live_progress_dir = horizon_dir(
                POST_ENTRY_SCORE_PATH_DIR,
                horizon_label,
                variant_slug,
                POST_ENTRY_LIVE_PROGRESS_SECTION,
            )
            path_switch_dir = horizon_dir(
                POST_ENTRY_SCORE_PATH_DIR,
                horizon_label,
                variant_slug,
                POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION,
            )
            outputs.update({
                path_observations_dir
                / "post_entry_score_path_observations.csv": (
                    path["observations"]
                ),
                path_observations_dir
                / "post_entry_score_path_horizon_alpha_average.csv": (
                    path["horizon_alpha_average"]
                ),
                path_live_progress_dir
                / "post_entry_score_path_live_progress_observations.csv": (
                    path["live_progress_observations"]
                ),
                path_live_progress_dir
                / "post_entry_score_path_live_progress_alpha_average.csv": (
                    path["live_progress_alpha_average"]
                ),
                path_switch_dir
                / "post_entry_score_path_switch_to_benchmark_thresholds.csv": (
                    path["switch_to_benchmark_thresholds"]
                ),
            })

    if ENABLED_TESTS["ticker_percentile_history"]:
        ticker_history = results["ticker_percentile_history"]
        ticker_history_raw_data_dir = (
            TICKER_PERCENTILE_HISTORY_DIR
            / enabled_timeframe_label()
            / "raw_data"
        )
        outputs.update({
            ticker_history_raw_data_dir / "ticker_percentile_history_metrics.csv": (
                ticker_history["metrics"]
            ),
            ticker_history_raw_data_dir
            / "ticker_percentile_history_forward_returns.csv": (
                ticker_history["forward_return_points"]
            ),
            ticker_history_raw_data_dir
            / "ticker_percentile_history_forward_return_horizons.csv": (
                ticker_history["forward_return_horizon_points"]
            ),
            ticker_history_raw_data_dir / "ticker_percentile_history_prices.csv": (
                ticker_history["prices"]
            ),
        })

    if ENABLED_TESTS["B1_B2_global_top_percent_and_correlation"]:
        outputs.update({
            GLOBAL_INFORMATION_COEFFICIENT_DIR
            / "global_information_coefficient_analysis.csv": (
                build_global_correlation_output(results["b1_b2"])
            ),
            GLOBAL_TOP_PERCENT_SELECTION_DIR
            / "global_top_percent_return_analysis.csv": (
                build_top_percent_output(results["b1_b2"])
            ),
        })

    if ENABLED_TESTS["B3_global_score_buckets"]:
        outputs[
            GLOBAL_SCORE_PERCENTILE_BUCKETS_DIR
            / "global_score_bucket_return_analysis.csv"
        ] = (
            build_global_bucket_output(results["b3"])
        )

    output_files = []
    for filename, dataframe in outputs.items():
        path = output_dir / filename
        save_csv_for_excel(dataframe, path)
        output_files.append(path)
    return output_files


def plot_analysis_outputs(results, output_dir):
    if ENABLED_TESTS["A1_A2_weekly_top_n_and_correlation"]:
        plot_weekly_cross_section(results["a1_a2"], output_dir)
    if ENABLED_TESTS["A3_weekly_rank_buckets"]:
        plot_weekly_rank_buckets(results["a3"], output_dir)
    if ENABLED_TESTS["B1_B2_global_top_percent_and_correlation"]:
        plot_global_score_calibration(results["b1_b2"], output_dir)
    if ENABLED_TESTS["B3_global_score_buckets"]:
        plot_global_score_buckets(results["b3"], output_dir)

    if ENABLED_TESTS["downside_information_ratio"]:
        horizon_label = horizon_week_label()
        plot_downside_information_ratio(
            results["downside_information_ratio"]["analysis"],
            output_dir,
            horizon_label,
        )
        plot_downside_information_ratio_buckets(
            results["downside_information_ratio"]["benchmark_return_buckets"],
            output_dir,
            horizon_label,
        )
    if ENABLED_TESTS["post_entry_score_path"]:
        horizon_label = horizon_week_label()
        for path in results["post_entry_score_path"].values():
            plot_post_entry_score_path(
                path,
                output_dir,
                horizon_label,
            )
    if ENABLED_TESTS["ticker_percentile_history"]:
        plot_ticker_percentile_history(
            results["ticker_percentile_history"],
            output_dir,
        )


def plot_weekly_information_coefficient_for_all_timeframes(
    score_observations,
    output_dir,
):
    if not ENABLED_TESTS["A1_A2_weekly_top_n_and_correlation"]:
        return

    all_ranges = all_timeframe_horizon_week_ranges()
    if not all_ranges:
        return

    all_timeframes_df = score_observations[
        score_observations["timeframe"].isin(all_ranges.keys())
    ].copy()
    if all_timeframes_df.empty:
        return

    return_panel = build_return_panel(
        all_timeframes_df,
        horizon_weeks_from_ranges(all_ranges),
    )
    if return_panel.empty:
        return

    analysis = calculate_weekly_cross_section(
        ScoreTestContext(
            return_panel=return_panel,
            score_observations=all_timeframes_df,
        ),
        horizon_week_ranges=all_ranges,
    )
    plot_weekly_information_coefficient(analysis, output_dir)


def main():
    PLOTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    migrate_csv_files_from_plots_directory()
    raw_df = build_dataframe(
        load_json(INPUT_FILE),
        EQUAL_WEIGHT_SCORE_COLUMN,
    )
    if raw_df.empty:
        print("[EMPTY] No observations found.")
        return

    score_df_all_timeframes = build_timeframe_score_observations(
        raw_df,
        EQUAL_WEIGHT_SCORE_COLUMN,
    )
    score_df_all_timeframes = add_weekly_score_metrics(score_df_all_timeframes)
    score_df = filter_enabled_timeframes(score_df_all_timeframes)
    if score_df.empty:
        print("[EMPTY] No weekly score observations found.")
        return

    horizon_weeks = build_horizon_weeks(score_df)
    if not horizon_weeks:
        print("[EMPTY] score_observations.json must contain at least two score dates.")
        return

    return_panel = build_return_panel(score_df, horizon_weeks)
    if return_panel.empty:
        print("[EMPTY] No return panel could be built from market data.")
        return

    # One shared panel and two lazily cached rankings feed every enabled test.
    results = run_configured_score_tests(
        ScoreTestContext(
            return_panel=return_panel,
            score_observations=score_df,
        )
    )

    output_files = save_analysis_outputs(results, DATA_OUTPUT_DIR)
    plot_analysis_outputs(results, PLOTS_OUTPUT_DIR)
    plot_weekly_information_coefficient_for_all_timeframes(
        score_df_all_timeframes,
        PLOTS_OUTPUT_DIR,
    )

    print("[OK] Saved focused weekly/global analysis:")
    print(
        f"Score date range: {score_df['start_timestamp'].min()} "
        f"-> {score_df['start_timestamp'].max()}"
    )
    for output_file in output_files:
        print(output_file)


if __name__ == "__main__":
    main()
