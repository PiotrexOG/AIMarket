import numpy as np


TRADING_DAYS_PER_YEAR = 252


def annualize_return(
    total_return,
    horizon_days,
    annualization_days=TRADING_DAYS_PER_YEAR,
):
    """Annualize scalar or array-like total returns for a given horizon."""
    try:
        horizon_days = float(horizon_days)
        annualization_days = float(annualization_days)
        returns = np.asarray(total_return, dtype=float)
    except (TypeError, ValueError):
        return None

    is_scalar = returns.ndim == 0
    annualized = np.full(returns.shape, np.nan, dtype=float)

    if horizon_days > 0 and annualization_days > 0:
        valid = np.isfinite(returns) & (returns > -1)
        annualized[valid] = (
            np.power(1 + returns[valid], annualization_days / horizon_days) - 1
        )

    if is_scalar:
        value = float(annualized)
        return value if np.isfinite(value) else None

    return annualized


def add_annualized_return_column(
    df,
    return_column="avg_return",
    horizon_column="horizon_days",
    output_column="annualized_return",
    digits=6,
):
    if df.empty or output_column in df.columns:
        return df

    result = df.copy()
    result[output_column] = [
        (
            None
            if (annualized := annualize_return(total_return, horizon_days)) is None
            else round(annualized, digits)
        )
        for total_return, horizon_days in zip(
            result[return_column],
            result[horizon_column],
        )
    ]
    return result
