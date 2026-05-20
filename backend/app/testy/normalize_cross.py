import os
import json
from pathlib import Path


def calculate_average_score(relative_scores):
    """
    Liczy średnią z wartości w relative_scores.
    """
    values = list(relative_scores.values())

    if not values:
        return None

    return round(sum(values) / len(values), 4)


def normalize_json_structure(data):
    """
    Zamienia strukturę:
    timeframe -> ticker -> relative_scores

    na:
    ticker -> timeframe -> average_score
    """

    result = {}

    for timeframe, tickers_data in data.items():

        # np. short_term_14d
        for ticker, ticker_data in tickers_data.items():

            relative_scores = ticker_data.get("relative_scores", {})

            avg_score = calculate_average_score(relative_scores)

            if ticker not in result:
                result[ticker] = {}

            result[ticker][timeframe] = {
                "score": avg_score
            }

    return result


def process_json_file(file_path):
    """
    Wczytuje plik JSON, przetwarza go
    i zapisuje nowy plik z suffixem _norm.json
    """

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        normalized_data = normalize_json_structure(data)

        output_path = file_path.with_name(
            f"{file_path.stem}_norm.json"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(normalized_data, f, indent=2, ensure_ascii=False)

        print(f"[OK] Zapisano: {output_path}")

    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")


def process_directory_recursively(root_folder):
    """
    Rekurencyjnie przechodzi po wszystkich podfolderach
    i przetwarza każdy plik .json
    """

    root_path = Path(root_folder)

    for file_path in root_path.rglob("*.json"):

        # pomijaj już wygenerowane pliki
        if file_path.stem.endswith("_norm"):
            continue

        process_json_file(file_path)


if __name__ == "__main__":

    # <- podaj tutaj folder startowy
    ROOT_FOLDER = Path(__file__).resolve().parents[2]

    PATH = ROOT_FOLDER / "data" / "CROSS_SECTION"

    process_directory_recursively(PATH)