from pathlib import Path


# Project paths. This file lives in app/testy/score_tests/run_score.
BACKEND_FOLDER = Path(__file__).resolve().parents[4]

CROSS_SECTION_DIR = BACKEND_FOLDER / "data" / "CROSS_SECTION"
INPUT_FILE = CROSS_SECTION_DIR / "score_observations.json"
RESULTS_DIR = BACKEND_FOLDER / "data" / "results"
PLOTS_OUTPUT_DIR = RESULTS_DIR / "plots"
DATA_OUTPUT_DIR = RESULTS_DIR / "data"

EQUAL_WEIGHT_SCORE_COLUMN = "score_equal_weight"


# Each switch corresponds to a named analysis written below results/data and
# results/plots. Analyses which share the same intermediate calculation are
# still configurable independently.
ENABLED_TESTS = {
    "weekly_top_n_selection": True,
    "weekly_information_coefficient": True,
    "weekly_rank_bucket_returns": True,
    "downside_information_ratio": True,
    "capm_alpha_beta": True,
    "post_entry_score_path": True,
    "ticker_percentile_history": True,
    "global_top_percent_selection": True,
    "global_information_coefficient": True,
    "global_score_percentile_buckets": True,
}

WEEKLY_CROSS_SECTION_TESTS = (
    "weekly_top_n_selection",
    "weekly_information_coefficient",
)
GLOBAL_SCORE_CALIBRATION_TESTS = (
    "global_top_percent_selection",
    "global_information_coefficient",
)


# These keys are labels present in score_observations.json. The actual return
# horizons used by every test are configured separately below, in weeks.
ENABLED_TIMEFRAMES = {
    "short_term_14d": False,
    "medium_term_50d": False,
    "long_term_200d": True,
}

HORIZON_WEEK_RANGES = {
    "short_term_14d": (1, 3),
    "medium_term_50d": (4, 10),
    "long_term_200d": (21, 35),
}

WEEKLY_INFORMATION_COEFFICIENT_TIMEFRAMES = (
    "short_term_14d",
    "medium_term_50d",
    "long_term_200d",
)

CAPM_ANNUAL_RISK_FREE_RATE = 0.04

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


def test_enabled(test_name):
    return bool(ENABLED_TESTS.get(test_name, False))


def any_test_enabled(test_names):
    return any(test_enabled(test_name) for test_name in test_names)


def enabled_timeframe_names():
    return tuple(
        timeframe
        for timeframe, is_enabled in ENABLED_TIMEFRAMES.items()
        if is_enabled
    )


def enabled_horizon_week_ranges():
    return {
        timeframe: HORIZON_WEEK_RANGES[timeframe]
        for timeframe in enabled_timeframe_names()
        if timeframe in HORIZON_WEEK_RANGES
    }


def weekly_information_coefficient_timeframe_names():
    return WEEKLY_INFORMATION_COEFFICIENT_TIMEFRAMES


def weekly_information_coefficient_horizon_week_ranges():
    return {
        timeframe: HORIZON_WEEK_RANGES[timeframe]
        for timeframe in weekly_information_coefficient_timeframe_names()
        if timeframe in HORIZON_WEEK_RANGES
    }


def horizon_weeks_from_ranges(horizon_week_ranges):
    return sorted({
        week
        for start_week, end_week in horizon_week_ranges.values()
        for week in range(start_week, end_week + 1)
    })


def enabled_timeframe_label():
    enabled = enabled_timeframe_names()
    if len(enabled) == 1:
        return enabled[0]
    return "_".join(enabled) if enabled else "no_timeframes"


def horizon_week_label():
    ranges = enabled_horizon_week_ranges()
    if len(ranges) == 1:
        start_week, end_week = next(iter(ranges.values()))
        return f"{start_week}-{end_week}w"
    if not ranges:
        return "no_horizons"
    return "_".join(
        f"{timeframe}_{start_week}-{end_week}w"
        for timeframe, (start_week, end_week) in ranges.items()
    )


def validate_config():
    missing_ranges = [
        timeframe
        for timeframe in enabled_timeframe_names()
        if timeframe not in HORIZON_WEEK_RANGES
    ]
    if missing_ranges:
        joined = ", ".join(missing_ranges)
        raise ValueError(
            f"Missing HORIZON_WEEK_RANGES for enabled timeframes: {joined}"
        )

    missing_weekly_ic_ranges = [
        timeframe
        for timeframe in weekly_information_coefficient_timeframe_names()
        if timeframe not in HORIZON_WEEK_RANGES
    ]
    if missing_weekly_ic_ranges:
        joined = ", ".join(missing_weekly_ic_ranges)
        raise ValueError(
            "Missing HORIZON_WEEK_RANGES for weekly IC timeframes: "
            f"{joined}"
        )

    invalid_ranges = {
        timeframe: week_range
        for timeframe, week_range in {
            **enabled_horizon_week_ranges(),
            **weekly_information_coefficient_horizon_week_ranges(),
        }.items()
        if (
            len(week_range) != 2
            or not all(isinstance(value, int) for value in week_range)
            or week_range[0] < 1
            or week_range[0] > week_range[1]
        )
    }
    if invalid_ranges:
        raise ValueError(f"Invalid weekly horizon ranges: {invalid_ranges}")
