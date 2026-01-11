import json
import os

import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict

API_KEY = os.environ.get("FIN_API_KEY")
FINNHUB_URL = "https://finnhub.io/api/v1/company-news"


def fetch_all_company_news(
    symbol: str,
    from_date: datetime,
    to_date: datetime,
) -> List[Dict]:

    assert from_date.tzinfo is not None, "from_date musi być timezone-aware"
    assert to_date.tzinfo is not None, "to_date musi być timezone-aware"

    results: Dict[int, Dict] = {}

    current_to = to_date

    while True:
        params = {
            "symbol": symbol,
            "from": from_date.date().isoformat(),
            "to": current_to.date().isoformat(),
            "token": API_KEY,
        }

        resp = requests.get(FINNHUB_URL, params=params)
        resp.raise_for_status()

        batch = resp.json()

        if not batch:
            break

        for item in batch:
            ts = item["datetime"]
            results[ts] = {
                "datetime": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
            }

        oldest_ts = min(item["datetime"] for item in batch)
        oldest_dt = datetime.fromtimestamp(oldest_ts, tz=timezone.utc)

        if oldest_dt <= from_date:
            break

        current_to = oldest_dt

        # sort od najstarszych

    res = sorted(results.values(), key=lambda x: x["datetime"])

    file_name = "news_apple.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=4, ensure_ascii=False)

    return res
