import numpy as np

from app.testy.score_tests.common.plotting import timeframe_label
from app.testy.score_tests.common.output_paths import (
    TICKER_FORWARD_RETURN_REFERENCE_SECTION,
    TICKER_INFORMATION_COEFFICIENT_SECTION,
    TICKER_PEARSON_ZSCORE_SECTION,
    TICKER_RETURN_ATTRIBUTION_SECTION,
    TICKER_SPEARMAN_PERCENTILE_SECTION,
)

from .correlation_plots import _save_score_return_correlation_by_timestamp_plot
from .momentum_plots import (
    _save_anti_momentum_correlation_charts,
    _save_model_vs_momentum_comparison_charts,
)
from .normalization import _normalized_excess_by_timestamp
from .return_comparison_plots import _save_normalized_excess_comparison_plot
from .ticker_heatmap import _save_ticker_date_heatmap


def _save_forward_return_heatmap(
    timeframe_forward_returns,
    timeframe_forward_return_horizons,
    prices,
    timeframe,
    directory,
    output_dir,
):
    required = {
        "ticker",
        "timestamp",
        "score",
        "score_percentile",
        "mean_forward_annualized_return",
        "forward_return_percentile",
    }
    if timeframe_forward_returns.empty or not required.issubset(
        timeframe_forward_returns.columns
    ):
        return

    data = timeframe_forward_returns.dropna(
        subset=[
            "ticker",
            "timestamp",
            "score",
            "score_percentile",
            "mean_forward_annualized_return",
            "forward_return_percentile",
        ]
    ).copy()
    if data.empty:
        return

    score_mean = data.groupby("timestamp")["score"].transform("mean")
    score_std = data.groupby("timestamp")["score"].transform(
        lambda values: values.std(ddof=0)
    )
    return_mean = data.groupby("timestamp")[
        "mean_forward_annualized_return"
    ].transform("mean")
    return_std = data.groupby("timestamp")[
        "mean_forward_annualized_return"
    ].transform(lambda values: values.std(ddof=0))
    data["score_zscore"] = (
        (data["score"] - score_mean) / score_std.replace(0, np.nan)
    ).fillna(0.0)
    data["forward_return_zscore"] = (
        (data["mean_forward_annualized_return"] - return_mean)
        / return_std.replace(0, np.nan)
    ).fillna(0.0)
    data["excess_forward_annualized_return"] = (
        data["mean_forward_annualized_return"] - return_mean
    )
    data["zscore_error"] = data["score_zscore"] - data["forward_return_zscore"]
    data["percentile_error"] = (
        data["score_percentile"] - data["forward_return_percentile"]
    )
    data["long_short_weight"] = data["score_percentile"] - 0.5
    data["long_only_weight"] = data["long_short_weight"].clip(lower=0.0)
    data["return_attribution"] = (
        data["long_short_weight"] * data["excess_forward_annualized_return"]
    )
    data["long_only_return_attribution"] = (
        data["long_only_weight"] * data["excess_forward_annualized_return"]
    )

    long_short_normalized_excess = _normalized_excess_by_timestamp(
        data,
        weight_column="long_short_weight",
        attribution_column="return_attribution",
    )
    long_only_normalized_excess = _normalized_excess_by_timestamp(
        data,
        weight_column="long_only_weight",
        attribution_column="long_only_return_attribution",
    )
    ticker_order = list(
        data.groupby("ticker")["mean_forward_annualized_return"]
        .mean()
        .sort_values(ascending=False)
        .index
    )

    horizon_start = data["horizon_week_start"].dropna()
    horizon_end = data["horizon_week_end"].dropna()
    horizon_label = (
        f"{int(horizon_start.min())}-{int(horizon_end.max())} tygodni"
        if not horizon_start.empty and not horizon_end.empty
        else "skonfigurowany horyzont"
    )
    forward_return_reference_directory = (
        directory / TICKER_FORWARD_RETURN_REFERENCE_SECTION
    )
    pearson_directory = directory / TICKER_PEARSON_ZSCORE_SECTION
    spearman_directory = directory / TICKER_SPEARMAN_PERCENTILE_SECTION
    information_coefficient_directory = (
        directory / TICKER_INFORMATION_COEFFICIENT_SECTION
    )
    return_attribution_directory = directory / TICKER_RETURN_ATTRIBUTION_SECTION

    heatmaps = [
        {
            "directory": pearson_directory,
            "column": "score_zscore",
            "filename": "pearson_01_score_zscore_heatmap.png",
            "title": (
                f"Widok Pearsona: wynik standaryzowany score "
                f"({horizon_label})"
            ),
            "colorbar": "Wynik standaryzowany score",
            "cmap": "RdYlGn",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["score_zscore"].mean(),
            "row_metric_label": "ŚrScoreZ",
        },
        {
            "directory": pearson_directory,
            "column": "forward_return_zscore",
            "filename": "pearson_02_forward_return_zscore_heatmap.png",
            "title": (
                f"Widok Pearsona: wynik standaryzowany przyszłej stopy zwrotu "
                f"({horizon_label})"
            ),
            "colorbar": "Wynik standaryzowany przyszłej stopy zwrotu",
            "cmap": "RdYlGn",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["forward_return_zscore"].mean(),
            "row_metric_label": "ŚrZwrotZ",
        },
        {
            "directory": pearson_directory,
            "column": "zscore_error",
            "filename": "pearson_03_score_minus_return_zscore_heatmap.png",
            "title": (
                f"Widok Pearsona: różnica między wynikiem standaryzowanym score "
                f"a wynikiem standaryzowanym stopy zwrotu {horizon_label})"
            ),
            "colorbar": "Wynik standaryzowany score - wynik standaryzowany przyszłego zwrotu",
            "cmap": "RdYlGn_r",
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["zscore_error"].mean(),
            "row_metric_label": "ŚrRóżnZ",
        },
        {
            "directory": spearman_directory,
            "column": "score_percentile",
            "filename": "spearman_01_score_percentile_heatmap.png",
            "title": (
                f"Widok Spearmana: percentyl score "
                f"({horizon_label})"
            ),
            "colorbar": "Percentyl score",
            "cmap": "RdYlGn",
            "vmin": 0,
            "vmax": 1,
            "percent_format": True,
            "row_metric": data.groupby("ticker")["score_percentile"].mean(),
            "row_metric_label": "ŚrPctScr",
            "row_metric_format": "percent",
        },
        {
            "directory": spearman_directory,
            "column": "forward_return_percentile",
            "filename": "spearman_02_forward_return_percentile_heatmap.png",
            "title": (
                f"Widok Spearmana: percentyl przyszłej stopy zwrotu "
                f"({horizon_label})"
            ),
            "colorbar": "Percentyl przyszłej stopy zwrotu",
            "cmap": "RdYlGn",
            "vmin": 0,
            "vmax": 1,
            "percent_format": True,
            "row_metric": data.groupby("ticker")["forward_return_percentile"].mean(),
            "row_metric_label": "ŚrPctZw",
            "row_metric_format": "percent",
        },
        {
            "directory": spearman_directory,
            "column": "percentile_error",
            "filename": "spearman_03_score_minus_return_percentile_heatmap.png",
            "title": (
                f"Widok Spearmana: różnica między percentylem score "
                f"a percentylem przyszłej stopy zwrotu "
                f"({horizon_label})"
            ),
            "colorbar": "Percentyl score - percentyl przyszłego zwrotu",
            "cmap": "RdYlGn_r",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["percentile_error"].mean(),
            "row_metric_label": "ŚrRóżnPct",
            "row_metric_format": "signed_percent",
        },
        {
            "directory": forward_return_reference_directory,
            "column": "excess_forward_annualized_return",
            "filename": "excess_forward_annualized_return_heatmap.png",
            "title": (
                f"Przyszły roczny nadwyżkowy zwrot ponad benchmark "
                f"z tej samej daty ({horizon_label})"
            ),
            "colorbar": "Przyszły roczny nadwyżkowy zwrot",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")[
                "excess_forward_annualized_return"
            ].mean(),
            "row_metric_label": "ŚrNadZw",
            "row_metric_format": "signed_percent",
        },
        {
            "directory": return_attribution_directory,
            "column": "return_attribution",
            "filename": "return_contribution_attribution_heatmap.png",
            "title": (
                f"Atrybucja zwrotu long-short: (percentyl score - 0.5) "
                f"x przyszły nadwyżkowy zwrot "
                f"({horizon_label})"
            ),
            "colorbar": "Atrybucja zwrotu",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")["return_attribution"].mean(),
            "row_metric_label": "ŚrAtr",
            "row_metric_format": "signed_percent",
            "column_metric": long_short_normalized_excess,
            "column_metric_label": "Znormalizowany nadwyżkowy zwrot long-short",
            "column_metric_format": "signed_percent",
        },
        {
            "directory": return_attribution_directory,
            "column": "long_only_return_attribution",
            "filename": "long_only_return_contribution_attribution_heatmap.png",
            "title": (
                f"Atrybucja zwrotu long-only: max(percentyl score - 0.5, 0) "
                f"x przyszły nadwyżkowy zwrot "
                f"({horizon_label})"
            ),
            "colorbar": "Atrybucja zwrotu long-only",
            "cmap": "RdYlGn",
            "percent_format": True,
            "robust": True,
            "symmetric": True,
            "row_metric": data.groupby("ticker")[
                "long_only_return_attribution"
            ].mean(),
            "row_metric_label": "ŚrAtr",
            "row_metric_format": "signed_percent",
            "column_metric": long_only_normalized_excess,
            "column_metric_label": "Znormalizowany nadwyżkowy zwrot long-only",
            "column_metric_format": "signed_percent",
        },
    ]

    for config in heatmaps:
        _save_ticker_date_heatmap(
            data,
            ticker_order,
            config["column"],
            timeframe,
            output_dir,
            config["directory"],
            config["filename"],
            config["title"],
            config["colorbar"],
            config["cmap"],
            vmin=config.get("vmin"),
            vmax=config.get("vmax"),
            percent_format=config.get("percent_format", False),
            robust=config.get("robust", False),
            symmetric=config.get("symmetric", False),
            row_metric=config.get("row_metric"),
            row_metric_label=config.get("row_metric_label", "ME"),
            row_metric_format=config.get("row_metric_format", "signed"),
            column_metric=config.get("column_metric"),
            column_metric_label=config.get("column_metric_label"),
            column_metric_format=config.get(
                "column_metric_format",
                "signed_percent",
            ),
        )

    _save_normalized_excess_comparison_plot(
        data,
        timeframe,
        return_attribution_directory,
        output_dir,
        long_short_normalized_excess,
        long_only_normalized_excess,
    )
    _save_score_return_correlation_by_timestamp_plot(
        data,
        timeframe_forward_return_horizons,
        timeframe,
        information_coefficient_directory,
        output_dir,
    )
    _save_anti_momentum_correlation_charts(
        data,
        prices,
        ticker_order,
        timeframe,
        directory,
        output_dir,
        horizon_label,
    )
    _save_model_vs_momentum_comparison_charts(
        data,
        prices,
        timeframe,
        directory,
        output_dir,
        horizon_label,
    )
