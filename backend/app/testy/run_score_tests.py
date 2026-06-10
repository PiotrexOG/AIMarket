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
    build_global_score_bucket_analysis,
    build_timeframe_score_observations,
    build_global_analysis,
    build_return_panel,
    build_weekly_analysis,
    build_weekly_bucket_analysis,
)
from score_observations import build_dataframe, load_json
from score_test_plotting import plot_global_analysis, plot_weekly_analysis


CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"

INPUT_FILE = CROSS_SECTION_DIR / "score_observations.json"
OUTPUT_DIR = CROSS_SECTION_DIR / "score_tests"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"


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


def add_annualized_return_column(selection_df):
    if selection_df.empty:
        return selection_df

    result = selection_df.copy()
    result["annualized_return"] = [
        annualize_return(row.avg_return, row.horizon_days)
        for row in result.itertuples(index=False)
    ]
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
        "timeframe",
        "horizon_days",
        "bucket",
        "top_n",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    selection = weekly_analysis[
        (weekly_analysis["test"] == "A1_top_n")
        & (weekly_analysis["bucket"] != "All 18")
    ]
    return (
        add_annualized_return_column(selection)[output_columns]
        .sort_values(["timeframe", "horizon_days", "top_n"])
        .reset_index(drop=True)
    )


def build_global_top_percent_output(global_analysis):
    output_columns = [
        "timeframe",
        "horizon_days",
        "bucket",
        "top_percent",
        "min_score",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]
    selection = global_analysis[
        (global_analysis["test"] == "B1_top_percent")
        & (global_analysis["bucket"] != "All")
    ]
    return (
        add_annualized_return_column(selection)[output_columns]
        .sort_values(["timeframe", "horizon_days", "top_percent"])
        .reset_index(drop=True)
    )


def build_weekly_bucket_output(weekly_bucket_analysis):
    output_columns = [
        "timeframe",
        "horizon_days",
        "bucket",
        "bucket_start_rank",
        "bucket_end_rank",
        "avg_score_min",
        "avg_score_max",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]

    if weekly_bucket_analysis.empty:
        return pd.DataFrame(columns=output_columns)

    return (
        add_annualized_return_column(weekly_bucket_analysis)[output_columns]
        .sort_values(["timeframe", "horizon_days", "bucket_start_rank"])
        .reset_index(drop=True)
    )


def build_global_score_bucket_output(global_score_bucket_analysis):
    output_columns = [
        "timeframe",
        "horizon_days",
        "bucket",
        "bucket_start_percent",
        "bucket_end_percent",
        "min_score",
        "max_score",
        "observation_count",
        "avg_return",
        "annualized_return",
    ]

    if global_score_bucket_analysis.empty:
        return pd.DataFrame(columns=output_columns)

    return (
        add_annualized_return_column(global_score_bucket_analysis)[output_columns]
        .sort_values(["timeframe", "horizon_days", "bucket_start_percent"])
        .reset_index(drop=True)
    )


def save_analysis_outputs(
    weekly_analysis,
    global_analysis,
    weekly_bucket_analysis,
    global_score_bucket_analysis,
    output_dir,
):
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
    weekly_bucket_path = output_dir / "weekly_rank_bucket_return_analysis.csv"
    global_score_bucket_path = output_dir / "global_score_bucket_return_analysis.csv"

    save_csv_for_excel(build_weekly_top_n_output(weekly_analysis), weekly_top_n_path)
    save_csv_for_excel(
        build_global_top_percent_output(global_analysis),
        global_top_percent_path,
    )
    save_csv_for_excel(
        build_weekly_bucket_output(weekly_bucket_analysis),
        weekly_bucket_path,
    )
    save_csv_for_excel(
        build_global_score_bucket_output(global_score_bucket_analysis),
        global_score_bucket_path,
    )

    output_files.extend([
        weekly_correlation_path,
        global_correlation_path,
        weekly_top_n_path,
        global_top_percent_path,
        weekly_bucket_path,
        global_score_bucket_path,
    ])
    return output_files


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = load_json(INPUT_FILE)
    raw_df = build_dataframe(data, EQUAL_WEIGHT_SCORE_COLUMN)

    print(1)

    if raw_df.empty:
        print("[EMPTY] No observations found.")
        return

    weekly_score_df = build_timeframe_score_observations(
        raw_df,
        EQUAL_WEIGHT_SCORE_COLUMN,
    )
    weekly_score_df = add_weekly_score_metrics(weekly_score_df)

    print(2)

    if weekly_score_df.empty:
        print("[EMPTY] No weekly score observations found.")
        return

    score_start_time = weekly_score_df["start_timestamp"].min()
    score_end_time = weekly_score_df["start_timestamp"].max()
    horizon_days = build_horizon_days(weekly_score_df)

    print(3)

    if not horizon_days:
        print("[EMPTY] score_observations.json must contain at least two score dates.")
        return

    return_panel = build_return_panel(
        weekly_score_df,
        horizon_days_values=horizon_days,
    )

    print(4)

    if return_panel.empty:
        print("[EMPTY] No return panel could be built from market data.")
        return

    weekly_analysis = build_weekly_analysis(return_panel)
    global_analysis = build_global_analysis(return_panel)
    weekly_bucket_analysis = build_weekly_bucket_analysis(return_panel)
    global_score_bucket_analysis = build_global_score_bucket_analysis(return_panel)

    print(5)

    clean_csv_outputs(OUTPUT_DIR)
    output_files = save_analysis_outputs(
        weekly_analysis,
        global_analysis,
        weekly_bucket_analysis,
        global_score_bucket_analysis,
        OUTPUT_DIR,
    )
    clean_plot_outputs(OUTPUT_DIR)
    plot_weekly_analysis(
        weekly_analysis,
        OUTPUT_DIR,
        weekly_bucket_analysis=weekly_bucket_analysis,
    )
    plot_global_analysis(
        global_analysis,
        OUTPUT_DIR,
        global_score_bucket_analysis=global_score_bucket_analysis,
    )

    print("[OK] Saved focused weekly/global analysis:")
    print(f"Score date range: {score_start_time} -> {score_end_time}")
    for output_file in output_files:
        print(output_file)


if __name__ == "__main__":
    main()
