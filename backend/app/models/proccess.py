import os
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from app.models.generator import generate_summary
from app.models.prompt_builder import build_summary_prompt
from app.models.summarizer_utils import group_news_by_date


def get_needed_filenames(start_date, end_date):
    """Generuje listę nazw plików w formacie MM_YYYY.json dla zakresu dat."""
    needed_files = []
    current = start_date.replace(day=1)  # Zacznij od 1-go dnia miesiąca startowego

    while current <= end_date.replace(day=1):
        filename = current.strftime("%m_%Y.json")
        needed_files.append(filename)

        # Przejdź do kolejnego miesiąca
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return needed_files

def process_news_range(
    start_date,
    end_date,
    TICKER,
    base_input_folder=Path("data/company_news"),
    base_output_folder=Path("data/company_news_summarized"),
):
    """
    start_date, end_date: 'YYYY-MM-DD' lub datetime
    tickers: lista tickerów lub None (wszystkie)
    """

    # konwersja dat
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    os.makedirs(base_output_folder, exist_ok=True)

    INPUT_FOLDER = os.path.join(base_input_folder, TICKER)
    OUTPUT_FOLDER = os.path.join(base_output_folder, TICKER)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # 1. Wyliczamy jakie pliki nas w ogóle interesują
    required_files = get_needed_filenames(start_date, end_date)

    # 2. Sprawdzamy, które z tych plików faktycznie istnieją w folderze wejściowym
    files_in_dir = os.listdir(INPUT_FOLDER)
    files_to_process = [f for f in required_files if f in files_in_dir]

    for file_name in sorted(files_to_process):
        # ... reszta logiki bez zmian, ale przetworzy tylko to co trzeba ...

        file_path = os.path.join(INPUT_FOLDER, file_name)

        with open(file_path, "r", encoding="utf-8") as f:
            raw_news = json.load(f)

        daily_data = group_news_by_date(raw_news)
        all_days_summarized = []

        for date_str in tqdm(sorted(daily_data.keys()), desc=f"{TICKER} Days"):

            current_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # 🔥 KLUCZOWY FILTR DAT
            if current_date < start_date or current_date > end_date:
                continue

            news_batch = daily_data[date_str]

            if len(news_batch) > 50:
                news_batch = news_batch[:50]

            prompt = build_summary_prompt(TICKER, date_str, news_batch)
            summary = generate_summary(prompt)

            all_days_summarized.append({
                "date": date_str,
                "daily_summary": summary
            })

        # zapis tylko jeśli coś jest
        if all_days_summarized:
            output_path = os.path.join(OUTPUT_FOLDER, f"summarized_{file_name}")

            # 🔹 1. Wczytaj istniejące dane (jeśli plik już istnieje)
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []
            else:
                existing_data = []

            # 🔹 2. Zamień na dict po dacie (żeby uniknąć duplikatów)
            existing_by_date = {item["date"]: item for item in existing_data}

            # 🔹 3. Dodaj / nadpisz nowe dni
            for item in all_days_summarized:
                existing_by_date[item["date"]] = item

            # 🔹 4. Posortuj po dacie
            merged_data = sorted(existing_by_date.values(), key=lambda x: x["date"])

            # 🔹 5. Zapisz całość
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)
