import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Stałe konfiguracyjne
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
CROSS_SECTION_DIR = DATA_DIR / "CROSS_SECTION"

VALID_MODES = {'structured_input', 'llm_output', 'llm_ranker'}


def load_json_file(file_path: Path) -> Any:
    """Generyczna funkcja do bezpiecznego wczytywania JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError:
        raise


def deserialize(sub_path: str, date_time: datetime, mode: str) -> Dict:
    if mode not in VALID_MODES:
        raise ValueError(f"Nieprawidłowy tryb: {mode}. Dostępne: {VALID_MODES}")

    date_str = date_time.strftime("%Y%m%d_%H%M%S")
    file_path = DATA_DIR / sub_path / date_str / f"{mode}.json"

    return load_json_file(file_path)


def get_available_timestamps() -> List[datetime]:
    """Pobiera listę posortowanych timestampów z nazw folderów."""
    if not CROSS_SECTION_DIR.exists():
        return []

    timestamps = []
    for folder in CROSS_SECTION_DIR.iterdir():
        if folder.is_dir():
            try:
                # Używamy formatu folderu jako nazwy
                dt = datetime.strptime(folder.name, "%Y%m%d_%H%M%S")
                timestamps.append(dt)
            except ValueError:
                continue

    return sorted(timestamps)

def fetch_cross_section(timestamps: List[datetime]) -> dict[datetime, dict]:
    return {
        ts: deserialize("CROSS_SECTION", ts, "llm_ranker")
        for ts in timestamps
    }