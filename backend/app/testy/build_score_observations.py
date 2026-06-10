import json
from datetime import datetime
from pathlib import Path


# =========================================================
# KONFIG
# =========================================================

ROOT_FOLDER = Path(__file__).resolve().parents[2]

CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"
INPUT_FILENAME = "llm_ranker.json"
OUTPUT_FILE = CROSS_SECTION_DIR / "score_observations.json"


# =========================================================
# LOAD / SAVE
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\n[OK] Saved final result:")
    print(output_path)


# =========================================================
# CROSS-SECTIONS
# =========================================================

def extract_timestamp_from_folder(folder_name):
    """
    20250326_133000 -> datetime
    """
    return datetime.strptime(folder_name, "%Y%m%d_%H%M%S")


def get_sorted_cross_sections(base_dir):
    folders = []

    for path in base_dir.iterdir():
        if not path.is_dir():
            continue

        try:
            extract_timestamp_from_folder(path.name)
        except ValueError:
            continue

        folders.append(path)

    folders.sort(key=lambda x: x.name)
    return folders

def normalize_json_structure(data):
    """
    Zamienia strukture:
    timeframe -> ticker -> relative_scores

    na:
    ticker -> timeframe -> relative_scores
    """
    result = {}

    for timeframe, tickers_data in data.items():
        for ticker, ticker_data in tickers_data.items():
            relative_scores = ticker_data.get("relative_scores", {})

            if ticker not in result:
                result[ticker] = {}

            result[ticker][timeframe] = {"relative_scores": relative_scores}

    return result


def load_normalized_cross_sections(folders):
    """
    Wczytuje surowe llm_ranker.json i normalizuje je w pamieci.
    Nic nie zapisuje po folderach cross-section.
    """
    normalized_by_folder = {}

    for folder in folders:
        json_path = folder / INPUT_FILENAME

        if not json_path.exists():
            print(f"[SKIP] Missing input: {json_path}")
            continue

        raw_data = load_json(json_path)
        normalized_by_folder[folder] = normalize_json_structure(raw_data)

    return normalized_by_folder


# =========================================================
# SCORE OBSERVATIONS
# =========================================================

def build_score_observation_dataset(folders, normalized_by_folder):
    timestamps = [
        extract_timestamp_from_folder(folder.name)
        for folder in folders
    ]

    print(f"Cross sections: {len(timestamps)}")

    result = {"by_timeframe": {}}

    for current_idx, folder in enumerate(folders):
        data = normalized_by_folder.get(folder)

        if data is None:
            continue

        current_timestamp = timestamps[current_idx]

        print(f"[PROCESS] {folder.name}")

        for ticker, ticker_data in data.items():
            for timeframe, timeframe_data in ticker_data.items():
                relative_scores = timeframe_data.get("relative_scores", {})

                if not relative_scores:
                    continue

                observation = {
                    "ticker": ticker,
                    "start_timestamp": current_timestamp.isoformat(),
                    "relative_scores": relative_scores,
                }

                timeframe_result = result["by_timeframe"].setdefault(
                    timeframe,
                    {
                        "observations": [],
                        "by_ticker": {},
                    },
                )
                timeframe_result["observations"].append(observation)

                if ticker not in timeframe_result["by_ticker"]:
                    timeframe_result["by_ticker"][ticker] = []

                timeframe_result["by_ticker"][ticker].append(observation)

    return result


# =========================================================
# PIPELINE
# =========================================================

def run_pipeline():
    folders = get_sorted_cross_sections(CROSS_SECTION_DIR)

    print(f"Found folders: {len(folders)}")

    normalized_by_folder = load_normalized_cross_sections(folders)
    print(f"Loaded and normalized in memory: {len(normalized_by_folder)}")

    return build_score_observation_dataset(folders, normalized_by_folder)


if __name__ == "__main__":
    final_dataset = run_pipeline()
    save_json(final_dataset, OUTPUT_FILE)
