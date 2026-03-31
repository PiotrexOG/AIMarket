import json
from pathlib import Path
from typing import Optional, List

# =========================
# Helpers
# =========================

def sum_quarters(
    quarters: List[dict],
    key: str,
    start: int,
    end: int
) -> Optional[float]:
    values = []
    for q in quarters[start:end]:
        val = q.get(key)
        if val is None:
            return None
        values.append(val)
    return sum(values)


def growth(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / abs(previous)

# =========================
# TTM (8Q)
# =========================

def compute_ttm_from_quarters(quarters: List[dict]) -> dict:
    keys = [
        "revenue",
        "grossProfit",
        "operatingIncome",
        "netIncome",
        "eps",
        "freeCashFlow"
    ]

    current = {}
    previous = {}

    for key in keys:
        current[key] = sum_quarters(quarters, key, 0, 4)
        previous[key] = sum_quarters(quarters, key, 4, 8)

    return {
        "current": current,
        "previous": previous
    }

# =========================
# Fundamentals (NO PRICE)
# =========================

def safe_ratio(numerator, denominator, ndigits=6) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(round(numerator / denominator, ndigits))


def compute_fundamentals_from_8q(quarters: List[dict]) -> dict:
    if len(quarters) < 8:
        raise ValueError("Wymagane jest minimum 8 kwartałów")

    latest = quarters[0]

    # shares
    shares = (
        latest.get("weightedAverageShsOutDil")
        or latest.get("weightedAverageShsOut")
    )
    if shares is None:
        raise ValueError("Brak liczby akcji")

    # balance (point-in-time)
    equity = latest.get("totalStockholdersEquity")
    debt = latest.get("totalDebt") or 0
    cash_eq = latest.get("cashAndCashEquivalents") or 0

    date = latest.get("date")

    # TTM
    ttm = compute_ttm_from_quarters(quarters)
    cur = ttm["current"]
    prev = ttm["previous"]

    revenue_ttm = cur["revenue"]

    return {
        "date": date,
        # shares & balance
        "shares_outstanding": shares,
        "equity": equity,
        "total_debt": debt,
        "cash_and_equivalents": cash_eq,

        # TTM fundamentals
        "revenue_ttm": revenue_ttm,
        "eps_ttm": float(round(cur["eps"], 6)),
        "free_cash_flow_ttm": cur["freeCashFlow"],

        "eps": latest.get("eps"),
        "eps_est_from_previous": latest.get("eps_est_from_previous"),
        "eps_est_for_next": latest.get("eps_est_for_next"),

        # profitability (ZAOKRĄGLONE I ZAWSZE FLOAT)
        "gross_margin_ttm": safe_ratio(
            cur["grossProfit"], revenue_ttm
        ),
        "operating_margin_ttm": safe_ratio(
            cur["operatingIncome"], revenue_ttm
        ),
        "net_margin_ttm": safe_ratio(
            cur["netIncome"], revenue_ttm
        ),

        # growth (YoY TTM) – jeśli growth zwraca iloraz, też warto float
        "revenue_growth_ttm_yoy": (
            float(round(growth(cur["revenue"], prev["revenue"]), 6))
            if growth(cur["revenue"], prev["revenue"]) is not None
            else None
        ),
        "eps_growth_ttm_yoy": (
            float(round(growth(cur["eps"], prev["eps"]), 6))
            if growth(cur["eps"], prev["eps"]) is not None
            else None
        ),
    }

# =========================
# Example usage
# =========================

def get_last_8_quarters_simple(current_year, current_quarter):
    quarters = []
    year = current_year
    quarter = current_quarter

    for _ in range(8):
        quarters.append(f"{year}_Q{quarter}.json")

        if quarter == 1:
            quarter = 4
            year -= 1
        else:
            quarter -= 1

    return quarters

def calculate(symbol: str, current_year: int, current_quarter: int):
    files = get_last_8_quarters_simple(current_year, current_quarter)


    base_path =  Path("fundaments") / "quarterly_compact" / symbol

    quarters = []
    for f in files:
        with open(base_path / f) as file:
            quarters.append(json.load(file))

    fundamentals = compute_fundamentals_from_8q(quarters)

    return fundamentals
