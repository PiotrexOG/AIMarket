import os

import requests
import json
from pathlib import Path

API_KEY = os.environ.get("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/stable"

BASE_DATA_PATH = Path("fundaments")

INPUT_DIR = BASE_DATA_PATH / "financial_data"
INPUT_DIR.mkdir(exist_ok=True, parents=True)

OUTPUT_DIR = BASE_DATA_PATH / "quarterly_compact"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def fetch_and_save(symbol: str, period: str, limit: int = 5):
    if period not in {"Q1", "Q2", "Q3", "Q4"}:
        raise ValueError("period musi być jednym z: Q1, Q2, Q3, Q4")

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


    for name, url in urls.items():
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        (INPUT_DIR/symbol).mkdir(exist_ok=True)

        file_path = INPUT_DIR / f"{symbol}" / f"{period}_{name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Zapisano: {file_path}")



def create(symbol: str):
    QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

    for q in QUARTERS:
        fetch_and_save(symbol, q)
