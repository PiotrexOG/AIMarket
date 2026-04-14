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
    Pobiera historyczne analyst grades i filtruje po zakresie dat,
    dołączając 2 ostatnie ratingi sprzed start_date.
    """

    url = f"{BASE_URL}/grades-historical"
    params = {"symbol": symbol, "apikey": API_KEY}

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # 1. Sortujemy od najstarszych do najnowszych
    sorted_data = sorted(data, key=lambda x: x["date"])

    results = []
    # Lista na dwa ostatnie elementy przed zakresem
    before_start_buffer = []

    for row in sorted_data:
        # Konwersja daty z obsługą potencjalnych różnic w formacie ISO
        row_date = datetime.fromisoformat(row["date"]).replace(tzinfo=timezone.utc)

        if row_date < start_date:
            # Dodajemy do bufora i trzymamy tylko 2 ostatnie znalezione
            before_start_buffer.append(row)
            if len(before_start_buffer) > 2:
                before_start_buffer.pop(0)

        elif start_date <= row_date <= end_date:
            results.append(row)

    # 2. Łączymy bufor (2 starsze) z wynikami z zakresu
    # before_start_buffer zawiera teraz [przedostatni, ostatni-przed-startem]
    return before_start_buffer + results
