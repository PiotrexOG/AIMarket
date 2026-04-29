import json
from datetime import date, datetime
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent
file_path = BASE_PATH / "config.json"

def save_last_fetch_date(fetch_date: date):
    data = {
        "last_fetch_date": fetch_date.isoformat()  # -> "2026-04-29"
    }
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_last_fetch_date():
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return datetime.strptime(
                data["last_fetch_date"], "%Y-%m-%d"
            ).date()
    except (FileNotFoundError, KeyError):
        return None