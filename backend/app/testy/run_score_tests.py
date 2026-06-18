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
    build_weekly_fractional_top_sortino_examples,
    build_weekly_fractional_top_analysis,
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

ENABLED_TESTS = {
    "A1_A2_weekly_top_n_and_correlation": False,
    "A3_weekly_rank_buckets": False,
    "A4_weekly_fractional_top_percent_ttest": True,
    "B1_B2_global_top_percent_and_correlation": False,
    "B3_global_score_buckets": False,
}

ENABLED_TIMEFRAMES = {
    "short_term_14d": False,
    "medium_term_50d": False,
    "long_term_200d": True,
}


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
    if "annualized_return" in result.columns:
        return result

    result["annualized_return"] = [
        annualize_return(row.avg_return, row.horizon_days)
        for row in result.itertuples(index=False)
    ]
    return result


def filter_enabled_timeframes(df):
    enabled_timeframes = [
        timeframe
        for timeframe, is_enabled in ENABLED_TIMEFRAMES.items()
        if is_enabled
    ]

    if not enabled_timeframes:
        return df.iloc[0:0].copy()

    return df[df["timeframe"].isin(enabled_timeframes)].copy()


def build_correlation_output(analysis_df, metric):
    output_columns = [
        "timeframe",
        "horizon_days",
        "metric",
        "observation_count",
        "pearson",
    ]

    if analysis_df.empty or not set([*output_columns, "test"]).issubset(analysis_df.columns):
        return pd.DataFrame(columns=output_columns)

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

    required_columns = set(output_columns) - {"annualized_return"}
    if weekly_analysis.empty or not set([*required_columns, "test"]).issubset(weekly_analysis.columns):
        return pd.DataFrame(columns=output_columns)

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

    required_columns = set(output_columns) - {"annualized_return"}
    if global_analysis.empty or not set([*required_columns, "test"]).issubset(global_analysis.columns):
        return pd.DataFrame(columns=output_columns)

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


def build_weekly_fractional_top_output(weekly_fractional_top_analysis):
    output_columns = [
        "timeframe",
        "horizon_days",
        "bucket",
        "top_share",
        "top_percent",
        "avg_effective_selected_count",
        "observation_count",
        "avg_return",
        "annualized_return",
        "market_annualized_return",
        "avg_annualized_excess_return",
        "std_return",
        "t_stat",
        "p_value",
        "downside_deviation",
        "sortino_stat",
        "avg_excess_return",
        "std_excess_return",
        "excess_t_stat",
        "excess_p_value",
        "excess_downside_deviation",
        "excess_sortino_stat",
        "is_best_t_stat",
        "is_best_excess_t_stat",
        "is_best_sortino_stat",
        "is_best_excess_sortino_stat",
    ]

    if weekly_fractional_top_analysis.empty:
        return pd.DataFrame(columns=output_columns)

    result = add_annualized_return_column(weekly_fractional_top_analysis)
    result["is_best_t_stat"] = False
    result["is_best_excess_t_stat"] = False
    result["is_best_sortino_stat"] = False
    result["is_best_excess_sortino_stat"] = False

    for _, group in result.groupby(["timeframe", "horizon_days"]):
        t_stat = pd.to_numeric(group["t_stat"], errors="coerce")
        excess_t_stat = pd.to_numeric(group["excess_t_stat"], errors="coerce")
        sortino_stat = pd.to_numeric(group["sortino_stat"], errors="coerce")
        excess_sortino_stat = pd.to_numeric(group["excess_sortino_stat"], errors="coerce")

        if not t_stat.dropna().empty:
            result.loc[t_stat.idxmax(), "is_best_t_stat"] = True

        if not excess_t_stat.dropna().empty:
            result.loc[excess_t_stat.idxmax(), "is_best_excess_t_stat"] = True

        if not sortino_stat.dropna().empty:
            result.loc[sortino_stat.idxmax(), "is_best_sortino_stat"] = True

        if not excess_sortino_stat.dropna().empty:
            result.loc[excess_sortino_stat.idxmax(), "is_best_excess_sortino_stat"] = True

    return (
        result[output_columns]
        .sort_values(["timeframe", "horizon_days", "top_share"])
        .reset_index(drop=True)
    )


def build_weekly_fractional_top_t_stat_examples(weekly_fractional_top_analysis):
    output_columns = [
        "timeframe",
        "horizon_days",
        "top_percent",
        "observation_count",
        "avg_return",
        "std_return",
        "standard_error",
        "t_stat",
        "calculation",
    ]

    if weekly_fractional_top_analysis.empty:
        return pd.DataFrame(columns=output_columns)

    required_columns = {
        "timeframe",
        "horizon_days",
        "top_percent",
        "observation_count",
        "avg_return",
        "std_return",
        "t_stat",
    }
    if not required_columns.issubset(weekly_fractional_top_analysis.columns):
        return pd.DataFrame(columns=output_columns)

    examples = weekly_fractional_top_analysis.copy()
    examples["top_percent_distance"] = examples["top_percent"].apply(
        lambda value: min(abs(value - target) for target in [5, 20, 50, 100])
    )
    examples = (
        examples.sort_values(
            ["timeframe", "horizon_days", "top_percent_distance", "top_percent"]
        )
        .groupby(["timeframe", "horizon_days"], as_index=False)
        .head(4)
    )

    rows = []
    for row in examples.itertuples(index=False):
        observation_count = int(row.observation_count)
        avg_return = float(row.avg_return)
        std_return = None if pd.isna(row.std_return) else float(row.std_return)
        standard_error = (
            None
            if std_return is None or observation_count <= 0
            else std_return / (observation_count ** 0.5)
        )
        calculation = (
            "not enough data"
            if standard_error in [None, 0]
            else f"{avg_return:.6f} / ({std_return:.6f} / sqrt({observation_count})) = {row.t_stat:.6f}"
        )
        rows.append({
            "timeframe": row.timeframe,
            "horizon_days": int(row.horizon_days),
            "top_percent": row.top_percent,
            "observation_count": observation_count,
            "avg_return": row.avg_return,
            "std_return": row.std_return,
            "standard_error": None if standard_error is None else round(standard_error, 6),
            "t_stat": row.t_stat,
            "calculation": calculation,
        })

    return pd.DataFrame(rows, columns=output_columns)


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
    weekly_fractional_top_analysis,
    weekly_fractional_top_sortino_examples,
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
    weekly_fractional_top_path = output_dir / "weekly_fractional_top_ttest_analysis.csv"
    weekly_fractional_top_examples_path = output_dir / "weekly_fractional_top_tstat_examples.csv"
    weekly_fractional_top_sortino_examples_path = output_dir / "weekly_fractional_top_sortino_examples.csv"
    global_top_percent_path = output_dir / "global_top_percent_return_analysis.csv"
    weekly_bucket_path = output_dir / "weekly_rank_bucket_return_analysis.csv"
    global_score_bucket_path = output_dir / "global_score_bucket_return_analysis.csv"

    save_csv_for_excel(build_weekly_top_n_output(weekly_analysis), weekly_top_n_path)
    save_csv_for_excel(
        build_weekly_fractional_top_output(weekly_fractional_top_analysis),
        weekly_fractional_top_path,
    )
    save_csv_for_excel(
        build_weekly_fractional_top_t_stat_examples(weekly_fractional_top_analysis),
        weekly_fractional_top_examples_path,
    )
    save_csv_for_excel(
        weekly_fractional_top_sortino_examples,
        weekly_fractional_top_sortino_examples_path,
    )
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
        weekly_fractional_top_path,
        weekly_fractional_top_examples_path,
        weekly_fractional_top_sortino_examples_path,
        global_top_percent_path,
        weekly_bucket_path,
        global_score_bucket_path,
    ])
    return output_files


def run_configured_score_tests(return_panel):
    weekly_analysis = pd.DataFrame()
    weekly_bucket_analysis = pd.DataFrame()
    weekly_fractional_top_analysis = pd.DataFrame()
    global_analysis = pd.DataFrame()
    global_score_bucket_analysis = pd.DataFrame()

    if ENABLED_TESTS["A1_A2_weekly_top_n_and_correlation"]:
        weekly_analysis = build_weekly_analysis(return_panel)

    if ENABLED_TESTS["A3_weekly_rank_buckets"]:
        weekly_bucket_analysis = build_weekly_bucket_analysis(return_panel)

    if ENABLED_TESTS["A4_weekly_fractional_top_percent_ttest"]:
        weekly_fractional_top_analysis = build_weekly_fractional_top_analysis(return_panel)

    if ENABLED_TESTS["B1_B2_global_top_percent_and_correlation"]:
        global_analysis = build_global_analysis(return_panel)

    if ENABLED_TESTS["B3_global_score_buckets"]:
        global_score_bucket_analysis = build_global_score_bucket_analysis(return_panel)

    return {
        "weekly_analysis": weekly_analysis,
        "weekly_bucket_analysis": weekly_bucket_analysis,
        "weekly_fractional_top_analysis": weekly_fractional_top_analysis,
        "global_analysis": global_analysis,
        "global_score_bucket_analysis": global_score_bucket_analysis,
    }


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
    weekly_score_df = filter_enabled_timeframes(weekly_score_df)
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

    score_tests = run_configured_score_tests(return_panel)
    weekly_analysis = score_tests["weekly_analysis"]
    weekly_bucket_analysis = score_tests["weekly_bucket_analysis"]
    weekly_fractional_top_analysis = score_tests["weekly_fractional_top_analysis"]
    global_analysis = score_tests["global_analysis"]
    global_score_bucket_analysis = score_tests["global_score_bucket_analysis"]
    weekly_fractional_top_sortino_examples = (
        build_weekly_fractional_top_sortino_examples(return_panel)
        if ENABLED_TESTS["A4_weekly_fractional_top_percent_ttest"]
        else pd.DataFrame()
    )

    print(5)

    clean_csv_outputs(OUTPUT_DIR)
    output_files = save_analysis_outputs(
        weekly_analysis,
        global_analysis,
        weekly_bucket_analysis,
        weekly_fractional_top_analysis,
        weekly_fractional_top_sortino_examples,
        global_score_bucket_analysis,
        OUTPUT_DIR,
    )
    clean_plot_outputs(OUTPUT_DIR)
    plot_weekly_analysis(
        weekly_analysis,
        OUTPUT_DIR,
        weekly_bucket_analysis=weekly_bucket_analysis,
        weekly_fractional_top_analysis=weekly_fractional_top_analysis,
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
