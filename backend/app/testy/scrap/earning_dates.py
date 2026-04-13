import json
from pathlib import Path
import yfinance as yf
import pandas as pd

# Konfiguracja katalogu wyjściowego
BASE_DATA_PATH = Path("data") / "fundaments"

OUTPUT_DIR = BASE_DATA_PATH / "quarterly_compact"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def get_fiscal_info(date_obj):
    """Zwraca krotkę (rok, kwartał_str)."""
    month = date_obj.month
    year = date_obj.year
    if 1 <= month <= 3:
        return year - 1, "Q4"
    elif 4 <= month <= 6:
        return year, "Q1"
    elif 7 <= month <= 9:
        return year, "Q2"
    else:
        return year, "Q3"


def save_earnings_by_date(symbol, start_date, end_date):
    """
    Pobiera dane i filtruje je na podstawie zakresu dat (datetime).
    """
    print(f"Pobieranie danych dla: {symbol} w zakresie {start_date.date()} do {end_date.date()}...")

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.earnings_dates
    except Exception as e:
        print(f"Błąd podczas pobierania {symbol}: {e}")
        return

    if df is None or df.empty:
        print(f"Brak danych earnings dla {symbol}")
        return

    # 1. Standaryzacja i obsługa stref czasowych
    df = df.reset_index()
    if 'Earnings Date' in df.columns:
        df.rename(columns={'Earnings Date': 'Date'}, inplace=True)

    df['Date'] = pd.to_datetime(df['Date'])

    # Konwersja dat wejściowych na UTC, aby pasowały do danych z yfinance
    start_dt = pd.to_datetime(start_date).tz_localize('UTC') if start_date.tzinfo is None else pd.to_datetime(
        start_date)
    end_dt = pd.to_datetime(end_date).tz_localize('UTC') if end_date.tzinfo is None else pd.to_datetime(end_date)

    if df['Date'].dt.tz is None:
        df['Date'] = df['Date'].dt.tz_localize('UTC')
    else:
        df['Date'] = df['Date'].dt.tz_convert('UTC')

    # 2. Sortowanie (Najnowsze na górze)
    df = df.sort_values(by='Date', ascending=False).reset_index(drop=True)

    # 3. PRZESUNIĘCIE DANYCH (Estymacja na NASTĘPNY raport)
    df['Next_EPS_Estimate'] = df['EPS Estimate'].shift(1)

    # 4. Filtrowanie z uwzględnieniem jednego dodatkowego rekordu wstecz
    # Szukamy wszystkich indeksów, które spełniają warunek daty
    in_range_indices = df.index[df['Date'] >= start_dt]

    if not in_range_indices.empty:
        # Pobieramy ostatni indeks z zakresu (najstarszy z pasujących)
        last_idx = in_range_indices.max()

        # Sprawdzamy, czy istnieje jeszcze starszy rekord (index + 1)
        if last_idx + 1 < len(df):
            end_idx = last_idx + 1
        else:
            end_idx = last_idx

        # Wycinamy od góry (najnowsze) do wyznaczonego końca
        # Skupiamy się na dacie końcowej (end_dt) i naszym rozszerzonym początku
        filtered_df = df.loc[(df['Date'] <= end_dt) & (df.index <= end_idx)].copy()
    else:
        filtered_df = pd.DataFrame()

    # 5. Budowanie wyniku JSON
    result = []
    for _, row in filtered_df.iterrows():
        f_year, f_q_str = get_fiscal_info(row['Date'])

        def clean_val(val):
            return float(val) if pd.notna(val) else None

        result.append({
            "date": row['Date'].isoformat(),
            "year": int(f_year),
            "quarter": f_q_str,
            "eps_est_from_previous": clean_val(row['EPS Estimate']),
            "eps_est_for_next": clean_val(row['Next_EPS_Estimate']),
            "eps_reported": clean_val(row['Reported EPS'])
        })

    if not result:
        print(f"Brak wyników dla {symbol} w podanym zakresie dat.")
        return

    # 6. Zapis
    target_dir = OUTPUT_DIR / symbol
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "earning_date.json"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Sukces: Zapisano {len(result)} wpisów dla {symbol}")
    except Exception as e:
        print(f"❌ Błąd zapisu: {e}")


def get_years_and_quarters_from_json(symbol: str) -> list[tuple[int, int]]:
    """
    Wczytuje plik earning_date.json dla danego symbolu i zwraca
    posortowaną listę krotek (rok, kwartał_int).
    """
    file_path = OUTPUT_DIR / symbol / "earning_date.json"

    if not file_path.exists():
        print(f"Plik dla {symbol} nie istnieje.")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        periods = set()
        for entry in data:
            year = entry.get("year")
            # Konwersja "Q1" -> 1, "Q2" -> 2 itd.
            q_str = entry.get("quarter", "Q0")
            q_int = int(q_str.replace("Q", ""))

            if year and q_int:
                periods.add((year, q_int))

        # Sortowanie wyników chronologicznie
        return sorted(list(periods))

    except Exception as e:
        print(f"Błąd podczas czytania pliku: {e}")
        return []