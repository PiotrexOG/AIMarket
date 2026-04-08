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

BASE_DATA_PATH = Path("data")
COMPANY_NEWS_PATH = BASE_DATA_PATH / "company_news"


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

    results: Dict[int, Dict] = {}
    current_to = to_date

    print("zaczynam pobieranie company news od " + from_date.isoformat() + " to " + to_date.isoformat())

    last_request_url = None
    same_request_count = 0

    while True:

        params = {
            "symbol": symbol,
            "from": from_date.date().isoformat(),
            "to": current_to.date().isoformat(),
            "token": API_KEY,
        }

        while True:
            try:
                resp = requests.get(FINNHUB_URL, params=params)

                print(f"Wysyłanie zapytania pod adres: {resp.url}")

                resp.raise_for_status()
                break

            except requests.exceptions.HTTPError:

                if resp.status_code == 429:
                    print("Finnhub rate limit (429). Sleep 2s...")
                    time.sleep(2)
                    continue

                raise

        batch = resp.json()

        if not batch:
            break

        # liczymy tylko requesty które zwróciły dane
        if resp.url == last_request_url:
            same_request_count += 1
        else:
            same_request_count = 0
            last_request_url = resp.url

        if same_request_count >= 3:
            print("Ten sam request z wynikami wykonany 3 razy – przerywam pobieranie.")
            break

        batch = sorted(batch, key=lambda x: x["datetime"], reverse=True)

        newest_ts = batch[0]["datetime"]

        batch = [
            item for item in batch
            if newest_ts - item["datetime"] <= 30 * 24 * 3600
        ]

        if not batch:
            break

        for item in batch:
            ts = item["datetime"]

            results[ts] = {
                "category": item.get("category", ""),
                "datetime": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
            }

        oldest_ts = batch[-1]["datetime"]
        oldest_dt = datetime.fromtimestamp(oldest_ts, tz=timezone.utc)

        if oldest_dt <= from_date:
            break

        current_to = oldest_dt

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
