import json
from pathlib import Path

INPUT_DIR = Path("../financial_data")
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("../quarterly_compact")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_json(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def select_record(data: list, year: int, quarter: str) -> dict:
    for record in data:
        if (
                str(record.get("fiscalYear")) == str(year)
                and record.get("period") == quarter
        ):
            return record

    raise ValueError(f"Brak danych dla {year} {quarter}")


def build_quarter_file(symbol: str, year: int, quarter: str):
    income_data = load_json(INPUT_DIR / f"{symbol}" / f"{quarter}_income.json")
    balance_data = load_json(INPUT_DIR / f"{symbol}" /f"{quarter}_balance.json")
    cash_data = load_json(INPUT_DIR / f"{symbol}" /f"{quarter}_cashflow.json")

    income = select_record(income_data, year, quarter)
    balance = select_record(balance_data, year, quarter)
    cash = select_record(cash_data, year, quarter)

    result = {
        "date": income.get("filingDate"),

        # INCOME
        "eps": income.get("eps"),
        "revenue": income.get("revenue"),
        "grossProfit": income.get("grossProfit"),
        "operatingIncome": income.get("operatingIncome"),
        "netIncome": income.get("netIncome"),
        "weightedAverageShsOut": income.get("weightedAverageShsOut"),
        "weightedAverageShsOutDil": income.get("weightedAverageShsOutDil"),

        # BALANCE
        "totalStockholdersEquity": balance.get("totalStockholdersEquity"),
        "totalDebt": balance.get("totalDebt"),
        "cashAndCashEquivalents": balance.get("cashAndCashEquivalents"),

        # CASH FLOW
        "freeCashFlow": cash.get("freeCashFlow"),
    }

    (OUTPUT_DIR/symbol).mkdir(exist_ok=True)

    output_path = OUTPUT_DIR / f"{symbol}" / f"{year}_{quarter}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✔ Utworzono {output_path}")

# przykład użycia
def create(symbol: str):
    QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
    YEARS = [2023, 2024, 2025]

    for y in YEARS:
        for q in QUARTERS:
            build_quarter_file(symbol, y, q)
