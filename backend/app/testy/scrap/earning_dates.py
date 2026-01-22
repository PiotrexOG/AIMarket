import json
from pathlib import Path
import yfinance as yf
import pandas as pd

# Konfiguracja katalogu wyjściowego
CURRENT_FILE_PATH = Path(__file__).resolve().parent.parent

OUTPUT_DIR = CURRENT_FILE_PATH / "quarterly_compact"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def get_fiscal_info(date_obj):
    """
    Zwraca krotkę (rok, kwartał_str, kwartał_int).
    Np. dla daty z maja 2025 zwróci: (2025, "Q1", 1)
    """
    month = date_obj.month
    year = date_obj.year

    if 1 <= month <= 3:
        return year - 1, "Q4", 4
    elif 4 <= month <= 6:
        return year, "Q1", 1
    elif 7 <= month <= 9:
        return year, "Q2", 2
    else:
        return year, "Q3", 3


def get_period_score(year, q_num):
    """
    Tworzy liczbę do łatwego porównywania okresów.
    Np. 2025 Q1 -> 20251
    """
    return year * 10 + q_num


def save_earnings_fiscal(symbol, start_year, start_q, end_year, end_q):
    """
    Pobiera dane i filtruje je po kwartałach fiskalnych.
    """
    print(f"Pobieranie danych dla: {symbol}...")

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.earnings_dates
    except Exception as e:
        print(f"Błąd podczas pobierania {symbol}: {e}")
        return

    if df is None or df.empty:
        print(f"Brak danych earnings dla {symbol}")
        return

    # 1. Standaryzacja danych
    df = df.reset_index()
    if 'Earnings Date' in df.columns:
        df.rename(columns={'Earnings Date': 'Date'}, inplace=True)

    df['Date'] = pd.to_datetime(df['Date'])

    # 2. Obsługa stref czasowych
    if df['Date'].dt.tz is not None:
        df['Date'] = df['Date'].dt.tz_convert('UTC')
    else:
        df['Date'] = df['Date'].dt.tz_localize('UTC')

    # 3. Sortowanie (Najnowsze na górze - KLUCZOWE)
    df = df.sort_values(by='Date', ascending=False)

    # 4. PRZESUNIĘCIE DANYCH (SHIFT) - Estymacja na NASTĘPNY kwartał
    # shift(1) przy sortowaniu malejącym (najnowsze na górze) pobiera wartość
    # z wiersza "wyżej" (czyli nowszego) i wstawia do wiersza bieżącego.
    # Oznacza to: "Jaka jest estymacja dla okresu, który nastąpi po tym raporcie".
    df['Next_EPS_Estimate'] = df['EPS Estimate'].shift(1)

    # 5. Wyliczanie kolumn pomocniczych (Rok i Kwartał raportowy)
    fiscal_data = []
    for idx, row in df.iterrows():
        f_year, f_q_str, f_q_int = get_fiscal_info(row['Date'])
        fiscal_data.append({
            'original_index': idx,
            'Fiscal_Year': f_year,
            'Fiscal_Q_Str': f_q_str,
            'Period_Score': get_period_score(f_year, f_q_int)
        })

    # Dołączamy dane fiskalne do głównego DataFrame
    fiscal_df = pd.DataFrame(fiscal_data)
    df = df.reset_index(drop=True)
    df = pd.concat([df, fiscal_df], axis=1)

    # 6. Przygotowanie parametrów filtrowania
    start_q_int = int(start_q.replace("Q", ""))
    end_q_int = int(end_q.replace("Q", ""))

    start_score = get_period_score(start_year, start_q_int)
    end_score = get_period_score(end_year, end_q_int)

    # 7. Filtrowanie właściwe
    mask = (df['Period_Score'] >= start_score) & (df['Period_Score'] <= end_score)
    filtered_df = df.loc[mask].copy()

    # 8. Budowanie wyniku JSON
    result = []

    for _, row in filtered_df.iterrows():
        def clean_val(val):
            if pd.isna(val) or val is None:
                return None
            return float(val)

        entry = {
            "date": row['Date'].isoformat(),
            "year": int(row['Fiscal_Year']),
            "quarter": row['Fiscal_Q_Str'],

            # --- ZMIANY TUTAJ ---

            # 1. Estymacja, która była dla TEGO raportu (z danych bieżącego wiersza)
            "eps_est_from_previous": clean_val(row['EPS Estimate']),

            # 2. Estymacja dla NASTĘPNEGO kwartału (z danych przesuniętych/przyszłych)
            "eps_est_for_next": clean_val(row['Next_EPS_Estimate']),

            # 3. Raportowany wynik
            "eps_reported": clean_val(row['Reported EPS'])
        }
        result.append(entry)

    if not result:
        print(f"Brak wyników dla {symbol} w okresie {start_year} {start_q} - {end_year} {end_q}.")
        return

    # 9. Zapis do pliku
    target_dir = OUTPUT_DIR / symbol
    target_dir.mkdir(parents=True, exist_ok=True)

    output_path = target_dir / "earning_date.json"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Sukces: Zapisano {len(result)} wpisów dla {symbol} ({start_year} {start_q} -> {end_year} {end_q})")
    except Exception as e:
        print(f"❌ Błąd zapisu pliku: {e}")
