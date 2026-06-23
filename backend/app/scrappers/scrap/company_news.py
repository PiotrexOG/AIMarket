import os
import time

import requests
from datetime import timezone, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

import json
from pathlib import Path
from datetime import datetime


API_KEY = os.environ.get("FIN_API_KEY")
FINNHUB_URL = "https://finnhub.io/api/v1/company-news"

BASE_DIR = Path(__file__).resolve().parents[3]
BASE_DATA_PATH = BASE_DIR / "data"
COMPANY_NEWS_PATH = BASE_DATA_PATH / "news" / "company_news"


def get_latest_datetime(
    base_path: Path,
    symbol: str,
    regex: str,
    date_key: str = "date",
    add_day: bool = False,
) -> Optional[datetime]:

    ticker_path = base_path / symbol

    if not ticker_path.exists():
        return None

    files = list(ticker_path.glob(regex))
    if not files:
        return None

    def parse_file_name(path):
        parts = path.stem.split("_")
        return int(parts[-1]), int(parts[-2])  # year, month

    latest_file = max(files, key=parse_file_name)

    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    if not data:
        return None

    dates = [
        datetime.fromisoformat(item[date_key])
        for item in data
        if date_key in item
    ]

    if not dates:
        return None

    latest_dt = max(dates)

    return latest_dt + timedelta(days=1) if add_day else latest_dt


def fetch_all_company_news(
        symbol: str,
        from_date: datetime,
        to_date: datetime,
) -> List[Dict]:
    assert from_date.tzinfo is not None
    assert to_date.tzinfo is not None

    if from_date > to_date:
        return []

    print(f"Zaczynam pobieranie newsów dla {symbol} od {from_date.isoformat()} do {to_date.isoformat()}")

    results: Dict[int, Dict] = {}
    current_to = to_date
    last_to_date = None  # Przechowuje wartość current_to z poprzedniej iteracji

    while True:
        # --- MECHANIZM UNIKANIA PĘTLI ---
        # Jeśli po poprzedniej iteracji data current_to nie uległa zmianie (lub jest późniejsza),
        # wymuszamy cofnięcie o 1 dzień, aby "przeskoczyć" martwy punkt w API.
        if last_to_date is not None and current_to.date() >= last_to_date.date():
            current_to = last_to_date - timedelta(days=1)
            print(f"Brak postępu w datach. Ręczne cofnięcie okna do: {current_to.date().isoformat()}")

        # Jeśli po korekcie wyszliśmy przed datę początkową, kończymy
        if current_to < from_date:
            break

        # Zapisujemy obecną datę przed wykonaniem zapytania
        last_to_date = current_to

        params = {
            "symbol": symbol,
            "from": from_date.date().isoformat(),
            "to": current_to.date().isoformat(),
            "token": API_KEY,
        }

        # --- OBSŁUGA ZAPYTANIA HTTP ---
        while True:
            try:
                resp = requests.get(FINNHUB_URL, params=params)
                print(f"Wysyłanie zapytania: {resp.url}")

                if resp.status_code == 429:
                    print("Finnhub rate limit (429). Sleep 2s...")
                    time.sleep(2)
                    continue

                resp.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                print(f"Błąd połączenia: {e}")
                raise

        batch = resp.json()

        if not batch:
            break

        # --- SORTOWANIE I FILTROWANIE (CLEAN BATCH) ---
        batch = sorted(batch, key=lambda x: x["datetime"], reverse=True)

        clean_batch = []
        if batch:
            clean_batch.append(batch[0])
            for i in range(1, len(batch)):
                gap = batch[i - 1]["datetime"] - batch[i]["datetime"]
                # Jeśli dziura między newsami jest większa niż 5 dni, przerywamy spójną paczkę
                if gap > (5 * 24 * 3600):
                    break
                clean_batch.append(batch[i])

        if not clean_batch:
            break

        # --- ZAPISYWANIE WYNIKÓW ---
        for item in clean_batch:
            ts = item["datetime"]
            results[ts] = {
                "category": item.get("category", ""),
                "datetime": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
            }

        # Pobieramy datę najstarszego newsa z przetworzonej paczki
        oldest_ts = clean_batch[-1]["datetime"]
        current_to = datetime.fromtimestamp(oldest_ts, tz=timezone.utc)

        # Jeśli dotarliśmy do (lub za) from_date, kończymy
        if current_to <= from_date:
            break

    # Zwracamy posortowane wyniki chronologicznie
    return sorted(results.values(), key=lambda x: x["datetime"])


def save_company_news_incremental(symbol: str, news: List[Dict]):

    ticker_path = COMPANY_NEWS_PATH / symbol
    ticker_path.mkdir(parents=True, exist_ok=True)

    monthly_news = defaultdict(list)

    for item in news:
        dt = datetime.fromisoformat(item["datetime"])
        key = (dt.year, dt.month)
        monthly_news[key].append(item)

    for (year, month), new_items in monthly_news.items():

        file_name = f"{month:02d}_{year}.json"
        file_path = ticker_path / file_name

        existing_items = []

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                existing_items = json.load(f)

        #  deduplikacja po timestamp
        existing_map = {item["datetime"]: item for item in existing_items}

        for item in new_items:
            existing_map[item["datetime"]] = item

        merged = sorted(existing_map.values(), key=lambda x: x["datetime"])

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
