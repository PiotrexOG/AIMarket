from pathlib import Path


WEEKLY_CROSS_SECTION_DIR = Path("weekly_cross_section")
WEEKLY_TOP_N_SELECTION_DIR = WEEKLY_CROSS_SECTION_DIR / "top_n_selection"
WEEKLY_INFORMATION_COEFFICIENT_DIR = (
    WEEKLY_CROSS_SECTION_DIR / "information_coefficient"
)
WEEKLY_RANK_BUCKET_RETURNS_DIR = WEEKLY_CROSS_SECTION_DIR / "rank_bucket_returns"

GLOBAL_SCORE_CALIBRATION_DIR = Path("global_score_calibration")
GLOBAL_TOP_PERCENT_SELECTION_DIR = (
    GLOBAL_SCORE_CALIBRATION_DIR / "top_percent_selection"
)
GLOBAL_INFORMATION_COEFFICIENT_DIR = (
    GLOBAL_SCORE_CALIBRATION_DIR / "information_coefficient"
)
GLOBAL_SCORE_PERCENTILE_BUCKETS_DIR = (
    GLOBAL_SCORE_CALIBRATION_DIR / "score_percentile_buckets"
)

DOWNSIDE_INFORMATION_RATIO_DIR = Path("downside_information_ratio")
DOWNSIDE_TOP_M_SELECTION_SECTION = Path("top_m_selection")
DOWNSIDE_BENCHMARK_RETURN_BUCKETS_SECTION = Path("benchmark_return_buckets")

CAPM_ALPHA_BETA_DIR = Path("capm_alpha_beta")
CAPM_TOP_M_SELECTION_SECTION = Path("top_m_selection")

POST_ENTRY_SCORE_PATH_DIR = Path("post_entry_score_path")
POST_ENTRY_SCORE_PATH_OBSERVATIONS_SECTION = Path("score_path_observations")
POST_ENTRY_LIVE_PROGRESS_SECTION = Path("live_progress")
POST_ENTRY_SWITCH_TO_BENCHMARK_SECTION = Path("switch_to_benchmark")

TICKER_PERCENTILE_HISTORY_DIR = Path("ticker_percentile_history")
TICKER_SCORE_PATHS_SECTION = Path("ticker_score_paths")
TICKER_FORWARD_RETURN_REFERENCE_SECTION = Path("forward_return_reference")
TICKER_SCORE_RETURN_ALIGNMENT_SECTION = Path("score_return_alignment")
TICKER_PEARSON_ZSCORE_SECTION = (
    TICKER_SCORE_RETURN_ALIGNMENT_SECTION / "pearson_zscore"
)
TICKER_SPEARMAN_PERCENTILE_SECTION = (
    TICKER_SCORE_RETURN_ALIGNMENT_SECTION / "spearman_percentile"
)
TICKER_INFORMATION_COEFFICIENT_SECTION = Path("information_coefficient")
TICKER_RETURN_ATTRIBUTION_SECTION = Path("return_attribution")
TICKER_MOMENTUM_CONTROLS_SECTION = Path("momentum_controls")
TICKER_ANTI_MOMENTUM_SECTION = TICKER_MOMENTUM_CONTROLS_SECTION / "anti_momentum"
TICKER_MODEL_VS_MOMENTUM_SECTION = (
    TICKER_MOMENTUM_CONTROLS_SECTION / "model_vs_momentum"
)


def horizon_dir(test_dir, horizon_label, *sections):
    directory = test_dir / Path(horizon_label)
    for section in sections:
        directory /= section
    return directory
