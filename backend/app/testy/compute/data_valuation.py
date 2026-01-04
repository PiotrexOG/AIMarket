# =========================
# Valuation (REQUIRES PRICE)
# =========================
from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotCreate


def compute_valuation_metrics(
    fundamentals: FundamentalSnapshotCreate,
    price: float
) -> dict:

    shares = fundamentals.shares_outstanding
    equity = fundamentals.equity
    debt = fundamentals.total_debt
    cash = fundamentals.cash_and_equivalents

    revenue_ttm = fundamentals.revenue_ttm
    eps_ttm = fundamentals.eps_ttm

    market_cap = price * shares
    enterprise_value = market_cap + debt - cash

    return {
        "price": price,
        "market_cap": market_cap,
        "enterprise_value": enterprise_value,

        # multiples
        "pe_ratio_ttm": price / eps_ttm if eps_ttm else None,
        "ps_ratio_ttm": market_cap / revenue_ttm if revenue_ttm else None,
        "pb_ratio": market_cap / equity if equity else None,
    }


def calculate(fundamentals: FundamentalSnapshotCreate, price: float) -> dict:
    valuation = compute_valuation_metrics(
        fundamentals=fundamentals,
        price=price
    )

    return valuation
