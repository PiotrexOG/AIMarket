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
    build_horizon_days,
    build_return_panel,
    build_timeframe_score_observations,
)
from score_tests.common.io import save_csv_for_excel
from score_tests.downside_information_ratio.calculation import (
    calculate as calculate_downside_information_ratio,
)
from score_tests.downside_information_ratio.plotting import (
    plot as plot_downside_information_ratio,
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
OUTPUT_DIR = CROSS_SECTION_DIR / "score_tests"

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

DOWNSIDE_INFORMATION_RATIO_HORIZON_RANGE = (100, 300)
POST_ENTRY_SCORE_PATH_HORIZON_RANGE = (100, 300)


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


def run_configured_score_tests(context):
    results = {
        "a1_a2": pd.DataFrame(),
        "a3": pd.DataFrame(),
        "downside_information_ratio": {
            "analysis": pd.DataFrame(),
            "by_horizon": pd.DataFrame(),
            "observations": pd.DataFrame(),
        },
        "post_entry_score_path": {
            "observations": pd.DataFrame(),
            "path_points": pd.DataFrame(),
            "correlations_by_horizon": pd.DataFrame(),
            "horizon_average": pd.DataFrame(),
            "live_progress_observations": pd.DataFrame(),
            "live_progress_correlations_by_horizon": pd.DataFrame(),
            "live_progress_average": pd.DataFrame(),
            "drop_regressions_by_horizon": pd.DataFrame(),
            "drop_regression_average": pd.DataFrame(),
        },
        "ticker_percentile_history": {
            "metrics": pd.DataFrame(),
            "prices": pd.DataFrame(),
        },
        "b1_b2": pd.DataFrame(),
        "b3": pd.DataFrame(),
    }

    if ENABLED_TESTS["A1_A2_weekly_top_n_and_correlation"]:
        results["a1_a2"] = calculate_a1_a2(context)
    if ENABLED_TESTS["A3_weekly_rank_buckets"]:
        results["a3"] = calculate_a3(context)
    if ENABLED_TESTS["downside_information_ratio"]:
        horizon_start, horizon_end = DOWNSIDE_INFORMATION_RATIO_HORIZON_RANGE
        results["downside_information_ratio"] = (
            calculate_downside_information_ratio(
                context,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
            )
        )
    if ENABLED_TESTS["post_entry_score_path"]:
        horizon_start, horizon_end = POST_ENTRY_SCORE_PATH_HORIZON_RANGE
        results["post_entry_score_path"] = calculate_post_entry_score_path(
            context,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )
    if ENABLED_TESTS["ticker_percentile_history"]:
        results["ticker_percentile_history"] = (
            calculate_ticker_percentile_history(context)
        )
    if ENABLED_TESTS["B1_B2_global_top_percent_and_correlation"]:
        results["b1_b2"] = calculate_b1_b2(context)
    if ENABLED_TESTS["B3_global_score_buckets"]:
        results["b3"] = calculate_b3(context)

    return results


def save_analysis_outputs(results, output_dir):
    ratio = results["downside_information_ratio"]
    path = results["post_entry_score_path"]
    outputs = {
        "weekly_correlation_analysis.csv": build_weekly_correlation_output(
            results["a1_a2"]
        ),
        "weekly_top_n_return_analysis.csv": build_top_n_output(
            results["a1_a2"]
        ),
        "weekly_rank_bucket_return_analysis.csv": build_weekly_bucket_output(
            results["a3"]
        ),
        "downside_information_ratio_analysis.csv": ratio["analysis"],
        "downside_information_ratio_by_horizon.csv": ratio["by_horizon"],
        "downside_information_ratio_observations.csv": ratio["observations"],
        "post_entry_score_path_observations.csv": path["observations"],
        "post_entry_score_path_points.csv": path["path_points"],
        "post_entry_score_path_correlations_by_horizon.csv": (
            path["correlations_by_horizon"]
        ),
        "post_entry_score_path_horizon_average.csv": path["horizon_average"],
        "post_entry_score_path_live_progress_observations.csv": (
            path["live_progress_observations"]
        ),
        "post_entry_score_path_live_progress_correlations_by_horizon.csv": (
            path["live_progress_correlations_by_horizon"]
        ),
        "post_entry_score_path_live_progress_average.csv": (
            path["live_progress_average"]
        ),
        "post_entry_score_path_drop_regressions_by_horizon.csv": (
            path["drop_regressions_by_horizon"]
        ),
        "post_entry_score_path_drop_regression_average.csv": (
            path["drop_regression_average"]
        ),
        "ticker_percentile_history_metrics.csv": (
            results["ticker_percentile_history"]["metrics"]
        ),
        "ticker_percentile_history_prices.csv": (
            results["ticker_percentile_history"]["prices"]
        ),
        "global_correlation_analysis.csv": build_global_correlation_output(
            results["b1_b2"]
        ),
        "global_top_percent_return_analysis.csv": build_top_percent_output(
            results["b1_b2"]
        ),
        "global_score_bucket_return_analysis.csv": build_global_bucket_output(
            results["b3"]
        ),
    }

    output_files = []
    for filename, dataframe in outputs.items():
        path = output_dir / filename
        save_csv_for_excel(dataframe, path)
        output_files.append(path)
    return output_files


def plot_analysis_outputs(results, output_dir):
    plot_a1_a2(results["a1_a2"], output_dir)
    plot_a3(results["a3"], output_dir)
    plot_b1_b2(results["b1_b2"], output_dir)
    plot_b3(results["b3"], output_dir)

    horizon_start, horizon_end = DOWNSIDE_INFORMATION_RATIO_HORIZON_RANGE
    plot_downside_information_ratio(
        results["downside_information_ratio"]["analysis"],
        output_dir,
        f"{horizon_start}-{horizon_end}",
    )
    horizon_start, horizon_end = POST_ENTRY_SCORE_PATH_HORIZON_RANGE
    plot_post_entry_score_path(
        results["post_entry_score_path"],
        output_dir,
        f"{horizon_start}-{horizon_end}",
    )
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

    horizon_days = build_horizon_days(score_df)
    if not horizon_days:
        print("[EMPTY] score_observations.json must contain at least two score dates.")
        return

    return_panel = build_return_panel(score_df, horizon_days)
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
