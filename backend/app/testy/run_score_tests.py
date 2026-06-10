import argparse
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

from score_test_calculations import (
    add_weekly_score_metrics,
    build_horizon_days,
    build_global_score_thresholds,
    build_timeframe_score_observations,
    build_global_analysis,
    build_return_panel,
    build_weekly_analysis,
)
from score_observations import build_dataframe, load_json
from score_test_plotting import plot_global_analysis, plot_weekly_analysis


CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"

INPUT_FILE = CROSS_SECTION_DIR / "score_observations.json"
OUTPUT_DIR = CROSS_SECTION_DIR / "score_tests"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"
# Extra market-data margin used for smoothed future prices around end_time.
PRICE_SMOOTHING_BUFFER_DAYS = 90


def annualize_return(total_return, horizon_days):
    if total_return is None or horizon_days <= 0:
        return None

    try:
        total_return = float(total_return)
    except (TypeError, ValueError):
        return None

    if total_return <= -1:
        return None

    return round(float((1 + total_return) ** (365 / horizon_days) - 1), 6)


def save_csv_for_excel(df, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write("sep=,\n")
        df.to_csv(f, index=False)


def clean_plot_outputs(output_dir):
    for plot_dir in [
        output_dir / "weekly_analysis",
        output_dir / "global_analysis",
    ]:
        if not plot_dir.exists():
            continue

        for plot_file in plot_dir.glob("*.png"):
            plot_file.unlink()


def clean_csv_outputs(output_dir):
    for csv_file in output_dir.glob("*analysis.csv"):
        try:
            csv_file.unlink()
        except PermissionError:
            print(f"[SKIP] Could not delete open file: {csv_file}")


def add_excess_return_columns(selection_df):
    if selection_df.empty:
        return selection_df

    result = selection_df.copy()
    benchmark = (
        result[result["bucket"].isin(["All 18", "All"])]
        [["timeframe", "horizon_days", "avg_return"]]
        .rename(columns={"avg_return": "benchmark_avg_return"})
    )
    result = result.merge(
        benchmark,
        on=["timeframe", "horizon_days"],
        how="left",
    )
    result["excess_avg_return"] = (
        result["avg_return"] - result["benchmark_avg_return"]
    ).round(6)
    result["annualized_return"] = [
        annualize_return(row.avg_return, row.horizon_days)
        for row in result.itertuples(index=False)
    ]
    result["benchmark_annualized_return"] = [
        annualize_return(row.benchmark_avg_return, row.horizon_days)
        for row in result.itertuples(index=False)
    ]
    result["annualized_excess_return"] = (
        result["annualized_return"] - result["benchmark_annualized_return"]
    ).round(6)
    return result


def build_correlation_output(analysis_df, metric):
    output_columns = [
        "timeframe",
        "horizon_days",
        "metric",
        "observation_count",
        "pearson",
    ]
    return (
        analysis_df[
            (analysis_df["metric"] == metric)
            & (analysis_df["test"].str.contains("pearson"))
        ][output_columns]
        .sort_values(["timeframe", "horizon_days"])
        .reset_index(drop=True)
    )


def build_combined_correlation_output(analysis_df):
    metric_frames = [
        build_correlation_output(analysis_df, metric)
        for metric in ["score", "percentile", "z_score"]
    ]
    return pd.concat(metric_frames, ignore_index=True)


def build_weekly_top_n_output(weekly_analysis):
    output_columns = [
        "analysis_group",
        "test",
        "timeframe",
        "horizon_days",
        "bucket",
        "top_n",
        "observation_count",
        "avg_return",
        "benchmark_avg_return",
        "excess_avg_return",
        "annualized_return",
        "benchmark_annualized_return",
        "annualized_excess_return",
    ]
    selection = weekly_analysis[weekly_analysis["test"] == "A1_top_n"]
    return (
        add_excess_return_columns(selection)[output_columns]
        .sort_values(["timeframe", "horizon_days", "top_n"])
        .reset_index(drop=True)
    )


def build_global_top_percent_output(global_analysis):
    output_columns = [
        "analysis_group",
        "test",
        "timeframe",
        "horizon_days",
        "bucket",
        "top_percent",
        "min_score",
        "observation_count",
        "avg_return",
        "benchmark_avg_return",
        "excess_avg_return",
        "annualized_return",
        "benchmark_annualized_return",
        "annualized_excess_return",
    ]
    selection = global_analysis[global_analysis["test"] == "B1_top_percent"]
    return (
        add_excess_return_columns(selection)[output_columns]
        .sort_values(["timeframe", "horizon_days", "top_percent"])
        .reset_index(drop=True)
    )


def save_analysis_outputs(weekly_analysis, global_analysis, output_dir):
    output_files = []

    weekly_correlation_path = output_dir / "weekly_correlation_analysis.csv"
    global_correlation_path = output_dir / "global_correlation_analysis.csv"

    save_csv_for_excel(
        build_combined_correlation_output(weekly_analysis),
        weekly_correlation_path,
    )
    save_csv_for_excel(
        build_combined_correlation_output(global_analysis),
        global_correlation_path,
    )

    weekly_top_n_path = output_dir / "weekly_top_n_return_analysis.csv"
    global_top_percent_path = output_dir / "global_top_percent_return_analysis.csv"

    save_csv_for_excel(build_weekly_top_n_output(weekly_analysis), weekly_top_n_path)
    save_csv_for_excel(
        build_global_top_percent_output(global_analysis),
        global_top_percent_path,
    )

    output_files.extend([
        weekly_correlation_path,
        global_correlation_path,
        weekly_top_n_path,
        global_top_percent_path,
    ])
    return output_files


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate focused score tests into data/CROSS_SECTION/score_tests."
    )
    parser.add_argument(
        "--end-time",
        required=True,
        help="Last date included in return calculations, for example 2026-06-10.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = load_json(INPUT_FILE)
    raw_df = build_dataframe(data, EQUAL_WEIGHT_SCORE_COLUMN)

    if raw_df.empty:
        print("[EMPTY] No observations found.")
        return

    weekly_score_df = build_timeframe_score_observations(
        raw_df,
        EQUAL_WEIGHT_SCORE_COLUMN,
    )
    weekly_score_df = add_weekly_score_metrics(weekly_score_df)

    if weekly_score_df.empty:
        print("[EMPTY] No weekly score observations found.")
        return

    horizon_days = build_horizon_days(weekly_score_df, args.end_time)

    if not horizon_days:
        print("[EMPTY] end_time must be after the first score date.")
        return

    return_panel = build_return_panel(
        weekly_score_df,
        horizon_days_values=horizon_days,
        end_time=args.end_time,
        market_data_buffer_days=PRICE_SMOOTHING_BUFFER_DAYS,
    )

    if return_panel.empty:
        print("[EMPTY] No return panel could be built from market data.")
        return

    score_thresholds = build_global_score_thresholds(weekly_score_df)
    weekly_analysis = build_weekly_analysis(return_panel)
    global_analysis = build_global_analysis(return_panel, score_thresholds)

    clean_csv_outputs(OUTPUT_DIR)
    output_files = save_analysis_outputs(
        weekly_analysis,
        global_analysis,
        OUTPUT_DIR,
    )
    clean_plot_outputs(OUTPUT_DIR)
    plot_weekly_analysis(weekly_analysis, OUTPUT_DIR)
    plot_global_analysis(global_analysis, OUTPUT_DIR)

    print("[OK] Saved focused weekly/global analysis:")
    for output_file in output_files:
        print(output_file)


if __name__ == "__main__":
    main()
