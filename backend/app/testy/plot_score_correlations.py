import sys
from pathlib import Path

from horizon_quantile_analysis import (
    calculate_horizon_daily_top_n_summaries,
    calculate_horizon_quantile_summaries,
)
from score_correlation_plotting import (
    plot_horizon_daily_top_n_pearson,
    plot_horizon_quantile_pearson
)
from score_dataset import (
    build_dataframe,
    get_score_columns,
    load_json,
)
from top_bucket_performance import (
    add_benchmark_columns,
    build_score_distribution_summaries,
    build_timeframe_score_thresholds,
)
from top_bucket_performance_plotting import (
    plot_daily_top_n_performance,
    plot_score_distributions,
    plot_top_bucket_performance,
)


ROOT_FOLDER = Path(__file__).resolve().parents[2]

if str(ROOT_FOLDER) not in sys.path:
    sys.path.append(str(ROOT_FOLDER))

CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"

INPUT_FILE = CROSS_SECTION_DIR / "score_observations.json"
OUTPUT_DIR = CROSS_SECTION_DIR / "correlation_plots"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"

# Same smoothing windows as in cross_section_pipeline.py. The horizon analysis
# changes only the end-date distance, not the left/right price smoothing window.
TIMEFRAME_PRICE_WINDOW_MAP = {
    "short_term_14d": 6,
    "medium_term_50d": 21,
    "long_term_200d": 84,
}

HORIZON_DAY_RANGE_MAP = {
    "short_term_14d": range(1, 420),
    "medium_term_50d": range(1, 420),
    "long_term_200d": range(1, 420),
}

TOP_SCORE_SHARES = [0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 1.00]
TOP_DAILY_COUNTS = [1, 2, 3, 5, 10, "all"]

MARKET_DATA_BUFFER_DAYS = 420


def save_csv_for_excel(df, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write("sep=,\n")
        df.to_csv(f, index=False)


def save_horizon_summaries(df, timeframe_score_thresholds):
    horizon_summary, quantile_summary = calculate_horizon_quantile_summaries(
        df,
        score_column=EQUAL_WEIGHT_SCORE_COLUMN,
        horizon_day_range_map=HORIZON_DAY_RANGE_MAP,
        smoothing_window_map=TIMEFRAME_PRICE_WINDOW_MAP,
        top_score_shares=TOP_SCORE_SHARES,
        market_data_buffer_days=MARKET_DATA_BUFFER_DAYS,
        timeframe_score_thresholds=timeframe_score_thresholds,
    )
    quantile_summary = add_benchmark_columns(horizon_summary, quantile_summary)

    if not quantile_summary.empty:
        save_csv_for_excel(
            quantile_summary,
            OUTPUT_DIR / "horizon_quantile_pearson_summary.csv",
        )

    return quantile_summary


def save_daily_top_n_summaries(df):
    benchmark_summary, daily_top_n_summary = calculate_horizon_daily_top_n_summaries(
        df,
        score_column=EQUAL_WEIGHT_SCORE_COLUMN,
        horizon_day_range_map=HORIZON_DAY_RANGE_MAP,
        smoothing_window_map=TIMEFRAME_PRICE_WINDOW_MAP,
        top_n_values=TOP_DAILY_COUNTS,
        market_data_buffer_days=MARKET_DATA_BUFFER_DAYS,
    )
    daily_top_n_summary = add_benchmark_columns(
        benchmark_summary,
        daily_top_n_summary,
    )

    if not daily_top_n_summary.empty:
        save_csv_for_excel(
            daily_top_n_summary,
            OUTPUT_DIR / "horizon_daily_top_n_summary.csv",
        )

    return daily_top_n_summary


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = load_json(INPUT_FILE)
    df = build_dataframe(data, EQUAL_WEIGHT_SCORE_COLUMN)

    if df.empty:
        print("[EMPTY] No observations found.")
        return

    score_columns = get_score_columns(df, EQUAL_WEIGHT_SCORE_COLUMN)

    if not score_columns:
        print("[EMPTY] No score columns found.")
        return

    score_distribution, score_threshold_mapping = build_score_distribution_summaries(
        df,
        EQUAL_WEIGHT_SCORE_COLUMN,
        TOP_SCORE_SHARES,
    )
    timeframe_score_thresholds = build_timeframe_score_thresholds(
        df,
        EQUAL_WEIGHT_SCORE_COLUMN,
        TOP_SCORE_SHARES,
    )
    save_csv_for_excel(
        score_distribution,
        OUTPUT_DIR / "score_distribution_summary.csv",
    )
    save_csv_for_excel(
        score_threshold_mapping,
        OUTPUT_DIR / "score_quantile_threshold_mapping.csv",
    )
    quantile_summary = save_horizon_summaries(df, timeframe_score_thresholds)
    daily_top_n_summary = save_daily_top_n_summaries(df)

    plot_horizon_quantile_pearson(quantile_summary, OUTPUT_DIR)
    plot_horizon_daily_top_n_pearson(daily_top_n_summary, OUTPUT_DIR)
    plot_score_distributions(
        df,
        EQUAL_WEIGHT_SCORE_COLUMN,
        score_threshold_mapping,
        OUTPUT_DIR,
    )
    plot_top_bucket_performance(quantile_summary, OUTPUT_DIR)
    plot_daily_top_n_performance(daily_top_n_summary, OUTPUT_DIR)

    print("[OK] Saved plots and summary:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
