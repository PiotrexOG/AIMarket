import sys
from pathlib import Path


# Make the `app` package importable when this file is executed directly.
_BACKEND_FOLDER = Path(__file__).resolve().parents[4]
if str(_BACKEND_FOLDER) not in sys.path:
    sys.path.insert(0, str(_BACKEND_FOLDER))

from app.testy.score_tests.run_score.config_run import (
    CAPM_ANNUAL_RISK_FREE_RATE,
    DATA_OUTPUT_DIR,
    ENABLED_TESTS,
    EQUAL_WEIGHT_SCORE_COLUMN,
    GLOBAL_SCORE_CALIBRATION_TESTS,
    INPUT_FILE,
    PLOTS_OUTPUT_DIR,
    POST_ENTRY_SCORE_PATH_VARIANTS,
    any_test_enabled,
    enabled_horizon_week_ranges,
    enabled_timeframe_label,
    enabled_timeframe_names,
    horizon_week_label,
    horizon_weeks_from_ranges,
    test_enabled,
    validate_config,
    weekly_information_coefficient_horizon_week_ranges,
    weekly_information_coefficient_timeframe_names,
)

from app.testy.score_observations import build_dataframe, load_json
from app.testy.score_tests.capm_alpha_beta.calculation import (
    calculate as calculate_capm_alpha_beta,
)
from app.testy.score_tests.capm_alpha_beta.plotting import (
    plot as plot_capm_alpha_beta,
)
from app.testy.score_tests.global_score_calibration.analysis import (
    calculate as calculate_global_score_calibration,
)
from app.testy.score_tests.global_score_calibration.information_coefficient import (
    build_correlation_output as build_global_correlation_output,
    plot as plot_global_information_coefficient,
)
from app.testy.score_tests.global_score_calibration.score_percentile_buckets import (
    build_output as build_global_bucket_output,
    calculate as calculate_global_score_buckets,
    plot as plot_global_score_buckets,
)
from app.testy.score_tests.global_score_calibration.top_percent_selection import (
    build_top_percent_output,
    plot as plot_global_top_percent_selection,
)
from app.testy.score_tests.common.context import ScoreTestContext
from app.testy.score_tests.common.data import (
    add_weekly_score_metrics,
    build_return_panel,
    build_timeframe_score_observations,
    filter_horizon_week_ranges,
)
from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.output_paths import (
    CAPM_ALPHA_BETA_DIR,
    CAPM_TOP_M_SELECTION_SECTION,
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
from app.testy.score_tests.downside_information_ratio.calculation import (
    calculate as calculate_downside_information_ratio,
)
from app.testy.score_tests.downside_information_ratio.plotting import (
    plot as plot_downside_information_ratio,
    plot_benchmark_return_buckets as plot_downside_information_ratio_buckets,
)
from app.testy.score_tests.post_entry_score_path.calculation import (
    calculate as calculate_post_entry_score_path,
)
from app.testy.score_tests.post_entry_score_path.plotting import (
    plot as plot_post_entry_score_path,
)
from app.testy.score_tests.ticker_percentile_history.calculation import (
    calculate as calculate_ticker_percentile_history,
)
from app.testy.score_tests.ticker_percentile_history.plotting import (
    plot as plot_ticker_percentile_history,
)
from app.testy.score_tests.weekly_cross_section.analysis import (
    calculate as calculate_weekly_cross_section,
)
from app.testy.score_tests.weekly_cross_section.information_coefficient import (
    build_correlation_output as build_weekly_correlation_output,
    plot as plot_weekly_information_coefficient,
)
from app.testy.score_tests.weekly_cross_section.rank_bucket_returns import (
    build_output as build_weekly_bucket_output,
    calculate as calculate_weekly_rank_buckets,
    plot as plot_weekly_rank_buckets,
)
from app.testy.score_tests.weekly_cross_section.top_n_selection import (
    build_top_n_output,
    plot as plot_weekly_top_n_selection,
)

def filter_timeframes(df, timeframes):
    timeframes = tuple(timeframes)
    return (
        df[df["timeframe"].isin(timeframes)].copy()
        if timeframes
        else df.iloc[0:0].copy()
    )


def filter_enabled_timeframes(df):
    return filter_timeframes(df, enabled_timeframe_names())


def filter_weekly_information_coefficient_timeframes(df):
    return filter_timeframes(
        df,
        weekly_information_coefficient_timeframe_names(),
    )


def filter_return_panel_horizon_week_ranges(return_panel, horizon_week_ranges):
    if not horizon_week_ranges:
        return return_panel.iloc[0:0].copy()
    return filter_horizon_week_ranges(
        return_panel,
        horizon_week_ranges=horizon_week_ranges,
    )


def required_horizon_week_ranges():
    ranges = dict(enabled_horizon_week_ranges())
    if test_enabled("weekly_information_coefficient"):
        ranges.update(weekly_information_coefficient_horizon_week_ranges())
    return ranges


def run_configured_score_tests(
    context,
    weekly_information_coefficient_context=None,
):
    results = {}
    horizon_week_ranges = enabled_horizon_week_ranges()
    has_enabled_context = (
        bool(horizon_week_ranges) and not context.return_panel.empty
    )
    weekly_information_coefficient_context = (
        weekly_information_coefficient_context
        if weekly_information_coefficient_context is not None
        else context
    )

    if has_enabled_context and test_enabled("weekly_top_n_selection"):
        results["weekly_cross_section"] = calculate_weekly_cross_section(
            context,
            horizon_week_ranges=horizon_week_ranges,
        )
    if test_enabled("weekly_information_coefficient"):
        results["weekly_information_coefficient"] = (
            calculate_weekly_cross_section(
                weekly_information_coefficient_context,
                horizon_week_ranges=(
                    weekly_information_coefficient_horizon_week_ranges()
                ),
            )
        )
    if has_enabled_context and test_enabled("weekly_rank_bucket_returns"):
        results["weekly_rank_bucket_returns"] = calculate_weekly_rank_buckets(
            context,
            horizon_week_ranges=horizon_week_ranges,
        )
    if has_enabled_context and test_enabled("downside_information_ratio"):
        results["downside_information_ratio"] = (
            calculate_downside_information_ratio(
                context,
                horizon_week_ranges=horizon_week_ranges,
            )
        )
    if has_enabled_context and test_enabled("capm_alpha_beta"):
        results["capm_alpha_beta"] = calculate_capm_alpha_beta(
            context,
            horizon_week_ranges=horizon_week_ranges,
            annual_risk_free_rate=CAPM_ANNUAL_RISK_FREE_RATE,
        )
    if has_enabled_context and test_enabled("post_entry_score_path"):
        results["post_entry_score_path"] = {
            variant["slug"]: calculate_post_entry_score_path(
                context,
                horizon_week_ranges=horizon_week_ranges,
                entry_min_score_percentile=variant[
                    "entry_min_score_percentile"
                ],
            )
            for variant in POST_ENTRY_SCORE_PATH_VARIANTS
        }
    if has_enabled_context and test_enabled("ticker_percentile_history"):
        results["ticker_percentile_history"] = (
            calculate_ticker_percentile_history(
                context,
                horizon_week_ranges=horizon_week_ranges,
            )
        )
    if has_enabled_context and any_test_enabled(GLOBAL_SCORE_CALIBRATION_TESTS):
        results["global_score_calibration"] = calculate_global_score_calibration(
            context,
            horizon_week_ranges=horizon_week_ranges,
        )
    if has_enabled_context and test_enabled("global_score_percentile_buckets"):
        results["global_score_percentile_buckets"] = (
            calculate_global_score_buckets(
                context,
                horizon_week_ranges=horizon_week_ranges,
            )
        )

    return results


def save_analysis_outputs(results, output_dir):
    outputs = {}
    horizon_label = horizon_week_label()

    if (
        test_enabled("weekly_information_coefficient")
        and "weekly_information_coefficient" in results
    ):
        outputs[
            WEEKLY_INFORMATION_COEFFICIENT_DIR
            / "weekly_information_coefficient_analysis.csv"
        ] = build_weekly_correlation_output(
            results["weekly_information_coefficient"]
        )

    if test_enabled("weekly_top_n_selection") and "weekly_cross_section" in results:
        outputs[
            WEEKLY_TOP_N_SELECTION_DIR / "weekly_top_n_return_analysis.csv"
        ] = build_top_n_output(results["weekly_cross_section"])

    if (
        test_enabled("weekly_rank_bucket_returns")
        and "weekly_rank_bucket_returns" in results
    ):
        outputs[
            WEEKLY_RANK_BUCKET_RETURNS_DIR
            / "weekly_rank_bucket_return_analysis.csv"
        ] = (
            build_weekly_bucket_output(results["weekly_rank_bucket_returns"])
        )

    if (
        test_enabled("downside_information_ratio")
        and "downside_information_ratio" in results
    ):
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

    if test_enabled("capm_alpha_beta") and "capm_alpha_beta" in results:
        capm = results["capm_alpha_beta"]
        capm_top_m_dir = horizon_dir(
            CAPM_ALPHA_BETA_DIR,
            horizon_label,
            CAPM_TOP_M_SELECTION_SECTION,
        )
        outputs.update({
            capm_top_m_dir / "capm_alpha_beta_analysis.csv": (
                capm["analysis"].round(6)
            ),
            capm_top_m_dir / "capm_alpha_beta_by_horizon.csv": (
                capm["by_horizon"].round(6)
            ),
        })

    if (
        test_enabled("post_entry_score_path")
        and "post_entry_score_path" in results
    ):
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

    if (
        test_enabled("ticker_percentile_history")
        and "ticker_percentile_history" in results
    ):
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

    if (
        test_enabled("global_information_coefficient")
        and "global_score_calibration" in results
    ):
        outputs[
            GLOBAL_INFORMATION_COEFFICIENT_DIR
            / "global_information_coefficient_analysis.csv"
        ] = build_global_correlation_output(results["global_score_calibration"])

    if (
        test_enabled("global_top_percent_selection")
        and "global_score_calibration" in results
    ):
        outputs[
            GLOBAL_TOP_PERCENT_SELECTION_DIR
            / "global_top_percent_return_analysis.csv"
        ] = build_top_percent_output(results["global_score_calibration"])

    if (
        test_enabled("global_score_percentile_buckets")
        and "global_score_percentile_buckets" in results
    ):
        outputs[
            GLOBAL_SCORE_PERCENTILE_BUCKETS_DIR
            / "global_score_bucket_return_analysis.csv"
        ] = (
            build_global_bucket_output(
                results["global_score_percentile_buckets"]
            )
        )

    output_files = []
    for filename, dataframe in outputs.items():
        path = output_dir / filename
        save_csv_for_excel(dataframe, path)
        output_files.append(path)
    return output_files


def plot_analysis_outputs(results, output_dir):
    horizon_label = horizon_week_label()

    if test_enabled("weekly_top_n_selection") and "weekly_cross_section" in results:
        plot_weekly_top_n_selection(results["weekly_cross_section"], output_dir)
    if (
        test_enabled("weekly_information_coefficient")
        and "weekly_information_coefficient" in results
    ):
        plot_weekly_information_coefficient(
            results["weekly_information_coefficient"],
            output_dir,
        )
    if (
        test_enabled("weekly_rank_bucket_returns")
        and "weekly_rank_bucket_returns" in results
    ):
        plot_weekly_rank_buckets(
            results["weekly_rank_bucket_returns"],
            output_dir,
        )
    if (
        test_enabled("global_top_percent_selection")
        and "global_score_calibration" in results
    ):
        plot_global_top_percent_selection(
            results["global_score_calibration"],
            output_dir,
        )
    if (
        test_enabled("global_information_coefficient")
        and "global_score_calibration" in results
    ):
        plot_global_information_coefficient(
            results["global_score_calibration"],
            output_dir,
        )
    if (
        test_enabled("global_score_percentile_buckets")
        and "global_score_percentile_buckets" in results
    ):
        plot_global_score_buckets(
            results["global_score_percentile_buckets"],
            output_dir,
        )

    if (
        test_enabled("downside_information_ratio")
        and "downside_information_ratio" in results
    ):
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
    if test_enabled("capm_alpha_beta") and "capm_alpha_beta" in results:
        plot_capm_alpha_beta(
            results["capm_alpha_beta"],
            output_dir,
            horizon_label,
        )
    if (
        test_enabled("post_entry_score_path")
        and "post_entry_score_path" in results
    ):
        for path in results["post_entry_score_path"].values():
            plot_post_entry_score_path(
                path,
                output_dir,
                horizon_label,
            )
    if (
        test_enabled("ticker_percentile_history")
        and "ticker_percentile_history" in results
    ):
        plot_ticker_percentile_history(
            results["ticker_percentile_history"],
            output_dir,
        )


def main():
    validate_config()
    if not any(ENABLED_TESTS.values()):
        print("[EMPTY] No score tests are enabled in config_run.py.")
        return
    if not INPUT_FILE.is_file():
        print(f"[MISSING] Score observations file not found: {INPUT_FILE}")
        return

    PLOTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
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
    score_df = filter_timeframes(
        score_df_all_timeframes,
        required_horizon_week_ranges().keys(),
    )
    if score_df.empty:
        print("[EMPTY] No weekly score observations found.")
        return

    horizon_weeks = horizon_weeks_from_ranges(required_horizon_week_ranges())
    if not horizon_weeks:
        print("[EMPTY] No weekly return horizons are configured.")
        return

    return_panel = build_return_panel(score_df, horizon_weeks)
    if return_panel.empty:
        print("[EMPTY] No return panel could be built from market data.")
        return

    enabled_ranges = enabled_horizon_week_ranges()
    weekly_ic_ranges = weekly_information_coefficient_horizon_week_ranges()
    enabled_score_df = filter_enabled_timeframes(score_df_all_timeframes)
    weekly_ic_score_df = filter_weekly_information_coefficient_timeframes(
        score_df_all_timeframes
    )

    # Contexts stay split so the weekly IC exception does not affect other tests.
    results = run_configured_score_tests(
        ScoreTestContext(
            return_panel=filter_return_panel_horizon_week_ranges(
                return_panel,
                enabled_ranges,
            ),
            score_observations=enabled_score_df,
        ),
        weekly_information_coefficient_context=ScoreTestContext(
            return_panel=filter_return_panel_horizon_week_ranges(
                return_panel,
                weekly_ic_ranges,
            ),
            score_observations=weekly_ic_score_df,
        ),
    )

    output_files = save_analysis_outputs(results, DATA_OUTPUT_DIR)
    plot_analysis_outputs(results, PLOTS_OUTPUT_DIR)

    print("[OK] Saved configured score-test analysis:")
    print(
        f"Score date range: {score_df['start_timestamp'].min()} "
        f"-> {score_df['start_timestamp'].max()}"
    )
    for output_file in output_files:
        print(output_file)


if __name__ == "__main__":
    main()
