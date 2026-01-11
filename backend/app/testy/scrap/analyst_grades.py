import os
import requests
from datetime import datetime, timezone
from typing import List

API_KEY = os.environ.get("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/stable"


def fetch_analyst_grades(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
) -> List[dict]:
    """
    Pobiera historyczne analyst grades i filtruje po zakresie dat
    """

    url = f"{BASE_URL}/grades-historical"
    params = {
        "symbol": symbol,
        "apikey": API_KEY,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    results = []
    for row in data:
        row_date = datetime.fromisoformat(row["date"]).replace(tzinfo=timezone.utc)

        if start_date <= row_date <= end_date:
            results.append(row)

    return results
