import json
from pathlib import Path

BASE_DATA_PATH = Path("data") / "fundaments"

INPUT_DIR = BASE_DATA_PATH / "financial_data"
INPUT_DIR.mkdir(exist_ok=True, parents=True)

OUTPUT_DIR = BASE_DATA_PATH / "quarterly_compact"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def load_json(path: Path) -> list:
    """Pomocnicza funkcja do ładowania JSON. Zwraca pustą listę, jeśli plik nie istnieje."""
    if not path.exists():
        print(f"⚠ Ostrzeżenie: Plik nie istnieje: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def select_financial_record(data: list, year: int, quarter: str) -> dict:
    """Szuka rekordu w danych finansowych (struktura z fiscalYear/period)."""
    for record in data:
        # Konwersja na stringi dla bezpieczeństwa porównania
        if (str(record.get("fiscalYear")) == str(year) and
                record.get("period") == quarter):
            return record

    # Jeśli nie znajdzie, zwracamy pusty słownik, żeby .get() nie wyrzucił błędu na None
    print(f"⚠ Brak danych finansowych dla {year} {quarter}")
    return {}


def find_earnings_record(data: list, year: int, quarter: str) -> dict:
    """Szuka rekordu w pliku earning_date.json (struktura z year/quarter)."""
    for record in data:
        # Tutaj klucze to 'year' (int) i 'quarter' (str) zgodnie z Twoim poprzednim kodem
        if record.get("year") == year and record.get("quarter") == quarter:
            return record

    return {}


def build_quarter_file(symbol: str, year: int, quarter: str):
    # 1. Ścieżki do plików źródłowych
    target_dir = OUTPUT_DIR / symbol
    target_dir.mkdir(parents=True, exist_ok=True)

    # Dane finansowe (Income, Balance, Cash)
    income_path = INPUT_DIR / symbol / f"{quarter}_income.json"
    balance_path = INPUT_DIR / symbol / f"{quarter}_balance.json"
    cash_path = INPUT_DIR / symbol / f"{quarter}_cashflow.json"

    # Dane o earnings (utworzone w poprzednim kroku)
    earnings_path = target_dir / "earning_date.json"

    # 2. Ładowanie danych
    income_data = load_json(income_path)
    balance_data = load_json(balance_path)
    cash_data = load_json(cash_path)
    earnings_list = load_json(earnings_path)

    # 3. Wybór odpowiednich rekordów dla danego roku i kwartału
    income = select_financial_record(income_data, year, quarter)
    balance = select_financial_record(balance_data, year, quarter)
    cash = select_financial_record(cash_data, year, quarter)

    # Znalezienie rekordu earnings (tego z eps_est i datą publikacji)
    earnings_rec = find_earnings_record(earnings_list, year, quarter)

    # 4. Budowanie wynikowego słownika

    final_date = earnings_rec.get("date")

    if final_date is None:
        final_date = income.get("filingDate")

    result = {
        "date": final_date,

        "eps_est_from_previous": earnings_rec.get("eps_est_from_previous"),
        "eps_est_for_next": earnings_rec.get("eps_est_for_next"),

        # INCOME STATEMENT
        "eps": income.get("eps"),
        "revenue": income.get("revenue"),
        "grossProfit": income.get("grossProfit"),
        "operatingIncome": income.get("operatingIncome"),
        "netIncome": income.get("netIncome"),
        "weightedAverageShsOut": income.get("weightedAverageShsOut"),
        "weightedAverageShsOutDil": income.get("weightedAverageShsOutDil"),

        # BALANCE SHEET
        "totalStockholdersEquity": balance.get("totalStockholdersEquity"),
        "totalDebt": balance.get("totalDebt"),
        "cashAndCashEquivalents": balance.get("cashAndCashEquivalents"),

        # CASH FLOW
        "freeCashFlow": cash.get("freeCashFlow"),
    }

    # 5. Zapis pojedynczego pliku kwartalnego
    output_path = target_dir / f"{year}_{quarter}.json"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Błąd zapisu {output_path}: {e}")


def create(symbol: str, start_year: int, start_quarter: str, end_year: int, end_quarter: str):
    QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

    try:
        # Indeksy 0-3 odpowiadają Q1-Q4
        start_q_idx = QUARTERS.index(start_quarter)
        end_q_idx = QUARTERS.index(end_quarter)
    except ValueError:
        print("❌ Błąd: Nieprawidłowy format kwartału. Użyj: Q1, Q2, Q3, Q4")
        return

    # 1. Przeliczamy punkt startowy na "absolutną liczbę kwartałów"
    # start_year * 4 + start_q_idx daje nam unikalny numer porządkowy kwartału w czasie
    start_absolute = (start_year * 4) + start_q_idx

    # Odejmowanie 7, aby dostać łącznie 8 kwartałów (bieżący + 7 poprzednich)
    effective_start_abs = start_absolute - 7

    # 2. Przeliczamy punkt końcowy
    end_absolute = (end_year * 4) + end_q_idx

    print(f"Zakres: od {effective_start_abs // 4} Q{(effective_start_abs % 4) + 1} "
          f"do {end_year} {end_quarter} (łącznie {end_absolute - effective_start_abs + 1} kwartałów)")

    # 3. Iterujemy po wszystkich kwartałach w wyliczonym zakresie
    for current_abs in range(effective_start_abs, end_absolute + 1):
        year = current_abs // 4
        q_idx = current_abs % 4
        quarter = QUARTERS[q_idx]

        build_quarter_file(symbol, year, quarter)

