MOVING_AVERAGE_COLUMN = "moving_average_score_percentile"
DEFAULT_MOVING_AVERAGE_WINDOW = 4
ANTI_MOMENTUM_SKIP_WEEKS = 4
Z_CRITICAL_95 = 1.959963984540054
HAC_DIAGNOSTIC_METRICS = [
    {
        "metric": "pearson",
        "label": "Pearson IC",
        "short_label": "Pearson",
        "color": "#4C78A8",
        "filename_stem": "pearson",
    },
    {
        "metric": "spearman",
        "label": "Spearman IC",
        "short_label": "Spearman",
        "color": "#59A14F",
        "filename_stem": "spearman",
    },
    {
        "metric": "score_percentile_pearson_ic",
        "label": "Pearson IC percentyla score",
        "short_label": "Pearson percentyla score",
        "color": "#F28E2B",
        "filename_stem": "score_percentile_pearson",
    },
]
ANTI_MOMENTUM_WINDOWS = [
    ("jegadeesh_titman", None, None, ANTI_MOMENTUM_SKIP_WEEKS),
]
