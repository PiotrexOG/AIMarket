import json
from pathlib import Path


# ============================================
# KONFIGURACJA
# ============================================

# <- podaj tutaj folder startowy
ROOT_FOLDER = Path(__file__).resolve().parents[2]

CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"
OUTPUT_FILE = CROSS_SECTION_DIR / "merged_scores.json"

INPUT_FILENAME = "llm_ranker_norm.json"


# ============================================
# POMOCNICZE
# ============================================

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_sorted_folders(base_dir):
    """
    Sortowanie po nazwie folderu:
    np.
    20250326_133000
    20250326_140000
    """
    folders = [p for p in base_dir.iterdir() if p.is_dir()]
    folders.sort(key=lambda x: x.name)
    return folders


# ============================================
# GŁÓWNE ŁĄCZENIE
# ============================================

def merge_all_scores(base_dir):

    result = {}

    folders = get_sorted_folders(base_dir)

    print(f"Znaleziono folderów: {len(folders)}")

    for folder in folders:

        json_path = folder / INPUT_FILENAME

        if not json_path.exists():
            print(f"[POMINIĘTO] Brak pliku: {json_path}")
            continue

        print(f"[WCZYTYWANIE] {json_path}")

        data = load_json(json_path)

        # ----------------------------------------
        # ticker
        # ----------------------------------------
        for ticker, ticker_data in data.items():

            if ticker not in result:
                result[ticker] = {}

            # ----------------------------------------
            # timeframe
            # ----------------------------------------
            for timeframe, timeframe_data in ticker_data.items():

                score = timeframe_data.get("score")

                if timeframe not in result[ticker]:
                    result[ticker][timeframe] = {
                        "scores": []
                    }

                result[ticker][timeframe]["scores"].append(score)

    return result


# ============================================
# ZAPIS
# ============================================

def save_json(data, output_path):

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Zapisano wynik:")
    print(output_path)


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    merged_data = merge_all_scores(CROSS_SECTION_DIR)

    save_json(merged_data, OUTPUT_FILE)