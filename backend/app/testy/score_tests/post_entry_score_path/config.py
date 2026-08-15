import numpy as np



ENTRY_MIN_SCORE_PERCENTILE = 0.7
USE_ENTRY_PERCENTILE_BUCKETS = False
ENTRY_PERCENTILE_BUCKET_SIZE = 2
ENTRY_PERCENTILE_BUCKET_COUNT = 9
PROGRESS_WEEK_STEP = 1
PROGRESS_BUCKET_PERCENTAGE_POINTS = 5
MIN_PROGRESS_BUCKET_PERCENT = 0
MAX_PROGRESS_BUCKET_PERCENT = 100
SWITCH_SCORE_CHANGE_THRESHOLDS = tuple(
    round(value, 2) for value in np.arange(-0.80, 0.4, 0.05)
)

CORRELATION_METRICS = [
    "mean_score_percentile",
]

LIVE_CORRELATION_METRICS = [
    "mean_score_percentile",
    "relative_score_percentile_change",
]


ENTRY_BUCKET_COLUMNS = [
    "entry_percentile_bucket_id",
    "entry_min_score_percentile",
    "entry_percentile_bucket_slug",
    "entry_percentile_bucket_label",
    "entry_percentile_bucket_rank_start",
    "entry_percentile_bucket_rank_end",
]
