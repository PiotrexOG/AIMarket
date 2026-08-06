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
from score_tests.a1_a2_weekly.calculation import (
    build_correlation_output as build_weekly_correlation_output,
    build_top_n_output,
    calculate as calculate_a1_a2,
)
from score_tests.a1_a2_weekly.plotting import plot as plot_a1_a2
from score_tests.a3_weekly_buckets.calculation import (
    build_output as build_weekly_bucket_output,
    calculate as calculate_a3,
)
from score_tests.a3_weekly_buckets.plotting import plot as plot_a3
from score_tests.b1_b2_global.calculation import (
    build_correlation_output as build_global_correlation_output,
    build_top_percent_output,
    calculate as calculate_b1_b2,
)
from score_tests.b1_b2_global.plotting import plot as plot_b1_b2
from score_tests.b3_global_buckets.calculation import (
    build_output as build_global_bucket_output,
    calculate as calculate_b3,
)
from score_tests.b3_global_buckets.plotting import plot as plot_b3
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


CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"
INPUT_FILE = CROSS_SECTION_DIR / "score_observations.json"
OUTPUT_DIR = ROOT_FOLDER / "data" / "results"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"

ENABLED_TESTS = {
    "A1_A2_weekly_top_n_and_correlation": False,
    "A3_weekly_rank_buckets": False,
    "downside_information_ratio": False,
    "post_entry_score_path": False,
    "ticker_percentile_history": True,
    "B1_B2_global_top_percent_and_correlation": False,
    "B3_global_score_buckets": False,
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
            "observations": pd.DataFrame(),
            "horizon_alpha_average": pd.DataFrame(),
            "live_progress_observations": pd.DataFrame(),
            "live_progress_alpha_average": pd.DataFrame(),
            "switch_to_benchmark_thresholds": pd.DataFrame(),
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
        results["a1_a2"] = calculate_a1_a2(
            context,
            horizon_week_ranges=enabled_horizon_week_ranges(),
        )
    if ENABLED_TESTS["A3_weekly_rank_buckets"]:
        results["a3"] = calculate_a3(
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
        results["post_entry_score_path"] = calculate_post_entry_score_path(
            context,
            horizon_week_ranges=enabled_horizon_week_ranges(),
        )
    if ENABLED_TESTS["ticker_percentile_history"]:
        results["ticker_percentile_history"] = (
            calculate_ticker_percentile_history(
                context,
                horizon_week_ranges=enabled_horizon_week_ranges(),
            )
        )
    if ENABLED_TESTS["B1_B2_global_top_percent_and_correlation"]:
        results["b1_b2"] = calculate_b1_b2(
            context,
            horizon_week_ranges=enabled_horizon_week_ranges(),
        )
    if ENABLED_TESTS["B3_global_score_buckets"]:
        results["b3"] = calculate_b3(
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
        path = results["post_entry_score_path"]
        path_observations_dir = horizon_dir(
            POST_ENTRY_SCORE_PATH_DIR,
            horizon_label,
            POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION,
        )
        path_live_progress_dir = horizon_dir(
            POST_ENTRY_SCORE_PATH_DIR,
            horizon_label,
            POST_ENTRY_LIVE_PROGRESS_SECTION,
        )
        path_switch_dir = horizon_dir(
            POST_ENTRY_SCORE_PATH_DIR,
            horizon_label,
            POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION,
        )
        outputs.update({
            path_observations_dir / "post_entry_score_path_observations.csv": (
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
        plot_a1_a2(results["a1_a2"], output_dir)
    if ENABLED_TESTS["A3_weekly_rank_buckets"]:
        plot_a3(results["a3"], output_dir)
    if ENABLED_TESTS["B1_B2_global_top_percent_and_correlation"]:
        plot_b1_b2(results["b1_b2"], output_dir)
    if ENABLED_TESTS["B3_global_score_buckets"]:
        plot_b3(results["b3"], output_dir)

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
        plot_post_entry_score_path(
            results["post_entry_score_path"],
            output_dir,
            horizon_label,
        )
    if ENABLED_TESTS["ticker_percentile_history"]:
        plot_ticker_percentile_history(
            results["ticker_percentile_history"],
            output_dir,
        )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_df = build_dataframe(
        load_json(INPUT_FILE),
        EQUAL_WEIGHT_SCORE_COLUMN,
    )
    if raw_df.empty:
        print("[EMPTY] No observations found.")
        return

    score_df = build_timeframe_score_observations(
        raw_df,
        EQUAL_WEIGHT_SCORE_COLUMN,
    )
    score_df = add_weekly_score_metrics(filter_enabled_timeframes(score_df))
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

    output_files = save_analysis_outputs(results, OUTPUT_DIR)
    plot_analysis_outputs(results, OUTPUT_DIR)

    print("[OK] Saved focused weekly/global analysis:")
    print(
        f"Score date range: {score_df['start_timestamp'].min()} "
        f"-> {score_df['start_timestamp'].max()}"
    )
    for output_file in output_files:
        print(output_file)


if __name__ == "__main__":
    main()
