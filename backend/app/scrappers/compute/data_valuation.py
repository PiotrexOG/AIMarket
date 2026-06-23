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
    growth = fundamentals.eps_growth_ttm_yoy * 100

    revenue_ttm = fundamentals.revenue_ttm
    eps_ttm = fundamentals.eps_ttm

    market_cap = price * shares
    enterprise_value = market_cap + debt - cash

    pe = None
    if eps_ttm and eps_ttm > 0:
        pe = price / eps_ttm

    ps = market_cap / revenue_ttm if revenue_ttm else None
    pb = market_cap / equity if equity else None

    # --- PEG ---
    peg = None
    if pe and growth and growth > 0:
        peg = pe / growth

    return {
        "price": price,
        "market_cap": market_cap,
        "enterprise_value": enterprise_value,

        # multiples
        "pe_ratio_ttm": pe,
        "ps_ratio_ttm": ps,
        "pb_ratio": pb,

        # growth
        "eps_growth_ttm_yoy": growth,

        # growth-adjusted valuation
        "peg_ratio": peg,
    }


def calculate(fundamentals: FundamentalSnapshotCreate, price: float) -> dict:
    valuation = compute_valuation_metrics(
        fundamentals=fundamentals,
        price=price
    )

    return valuation
