import os
import json
import time
from pathlib import Path
from typing import Optional, Tuple

import requests

API_KEY = os.environ.get("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/stable"

BASE_DIR = Path(__file__).resolve().parents[3]
BASE_DATA_PATH = BASE_DIR / "data" / "fundaments"


INPUT_DIR = BASE_DATA_PATH / "financial_data"
INPUT_DIR.mkdir(exist_ok=True, parents=True)


# =========================
# HELPERS
# =========================

def quarter_to_int(quarter: str) -> int:
    q_map = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    return q_map[quarter]

def year_quarter_to_int(year: int, quarter: int) -> int:
    return year * 4 + quarter


def is_future_quarter(q: str, target_q: str) -> bool:
    q_map = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    return q_map[q] > q_map[target_q]


def get_latest_from_file(symbol: str, statement: str, period: str) -> Optional[Tuple[int, int]]:
    file_path = INPUT_DIR / symbol / f"{period}_{statement}.json"

    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        return None

    latest = data[0]
    return int(latest["fiscalYear"]), quarter_to_int(latest["period"])


# =========================
# CORE LOGIC
# =========================

def should_fetch_quarter(symbol: str, period: str, target_year: int, target_q: int) -> bool:
    STATEMENTS = ["income", "balance", "cashflow"]

    target_val = year_quarter_to_int(target_year, target_q)

    for stmt in STATEMENTS:
        latest = get_latest_from_file(symbol, stmt, period)

        # brak pliku → fetch
        if latest is None:
            return True

        latest_year, latest_q = latest
        latest_val = year_quarter_to_int(latest_year+1, latest_q)

        # jeśli choć jeden statement jest nieaktualny → fetch
        if latest_val <= target_val:
            return True

    return False


# =========================
# FETCH
# =========================

def get_with_retry(url, params, max_retries=10, initial_delay=2):
    delay = initial_delay

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params)

            # sukces
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code

            # retry tylko dla 429
            if status_code == 429:
                print(
                    f"[429] Rate limit. "
                    f"Próba {attempt}/{max_retries}. "
                    f"Czekam {delay}s..."
                )

                time.sleep(delay)
                delay *= 2
            else:
                raise

        except requests.exceptions.RequestException as e:
            print(
                f"[REQUEST ERROR] "
                f"Próba {attempt}/{max_retries}. "
                f"Czekam {delay}s..."
            )

            time.sleep(delay)
            delay *= 2

    raise Exception(f"Nie udało się pobrać danych po {max_retries} próbach")


def fetch_and_save(symbol: str, period: str, limit: int = 5):
    urls = {
        "income": f"{BASE_URL}/income-statement",
        "balance": f"{BASE_URL}/balance-sheet-statement",
        "cashflow": f"{BASE_URL}/cash-flow-statement",
    }

    params = {
        "symbol": symbol,
        "period": period,
        "limit": limit,
        "apikey": API_KEY,
    }

    (INPUT_DIR / symbol).mkdir(parents=True, exist_ok=True)

    for name, url in urls.items():
        data = get_with_retry(url, params)

        file_path = INPUT_DIR / symbol / f"{period}_{name}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"FETCHED: {symbol} {period}")


# =========================
# MAIN
# =========================

def create(symbol: str, last_year: int, last_q: int):
    QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

    for q in QUARTERS:

        if should_fetch_quarter(symbol, q, last_year, last_q):
            fetch_and_save(symbol, q)