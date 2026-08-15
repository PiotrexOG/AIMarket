from .calculation import (
    ENTRY_MIN_SCORE_PERCENTILE,
    USE_ENTRY_PERCENTILE_BUCKETS,
)



SCORE_CHANGE_SCATTER_PROGRESS_PERCENT = 25
PROGRESS_BUCKET_PERCENTAGE_POINTS = 5
MIN_PROGRESS_BUCKET_PERCENT = 10
MAX_PROGRESS_BUCKET_PERCENT = 80

ALL_SCORES_SLUG = "all_scores"
ENTRY_MIN_SCORE_PERCENTILE_70_SLUG = "entry_min_score_percentile_70"
ALL_SCORES_ONLY_TIMEFRAME = "long_term_200d"
PLOT_MODE_FULL = "full"
PLOT_MODE_ONLY_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE = (
    "only_live_progress_mean_score_percentile"
)
PLOT_MODE_WITHOUT_LIVE_PROGRESS_MEAN_SCORE_PERCENTILE = (
    "without_live_progress_mean_score_percentile"
)


METRIC_LABELS = {
    "mean_score_percentile": "Średni percentyl score",
    "score_percentile_change": (
        "Zmiana percentyla score: średnia w horyzoncie - wejście"
    ),
    "relative_score_percentile_change": (
        "Względna zmiana percentyla score"
    ),
}

SWITCH_TO_BENCHMARK_METRIC_LABELS = {
    "mean_switch_to_benchmark_annualized_gain": (
        "Średni roczny zysk z przełączenia na benchmark gdy względna zmiana percentyla score <= próg"
    ),
    "downside_deviation": "Downside deviation zysku z przełączenia na benchmark gdy względna zmiana percentyla score <= próg",
    "downside_information_ratio": "Wskaźnik DIR z przełączenia na benchmark gdy względna zmiana percentyla score <= próg"
}
