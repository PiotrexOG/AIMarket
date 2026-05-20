import json
from pathlib import Path
from datetime import datetime

from app.db.database import SessionLocal
from app.services.layers.market_data_service import MarketDataService

# =========================================================
# KONFIG
# =========================================================

# <- podaj tutaj folder startowy
ROOT_FOLDER = Path(__file__).resolve().parents[2]

CROSS_SECTION_DIR = ROOT_FOLDER / "data" / "CROSS_SECTION"
INPUT_FILENAME = "llm_ranker_norm.json"

OUTPUT_FILE = CROSS_SECTION_DIR / "score_vs_returns.json"

# ile kolejnych cross-sections do przodu
TIMEFRAME_FORWARD_MAP = {
    "short_term_14d": 2,
    "medium_term_50d": 7,
    "long_term_200d": 28,
}


# =========================================================
# LOAD
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_timestamp_from_folder(folder_name):
    """
    20250326_133000 -> datetime
    """
    return datetime.strptime(folder_name, "%Y%m%d_%H%M%S")


def get_sorted_cross_sections(base_dir):

    folders = [p for p in base_dir.iterdir() if p.is_dir()]

    folders.sort(key=lambda x: x.name)

    return folders


# =========================================================
# MAIN
# =========================================================

def build_score_return_dataset():

    with SessionLocal() as session:

        market_data_service = MarketDataService(session)

        folders = get_sorted_cross_sections(CROSS_SECTION_DIR)

        # ---------------------------------------------
        # timestamps
        # ---------------------------------------------
        timestamps = [
            extract_timestamp_from_folder(folder.name)
            for folder in folders
        ]

        print(f"Cross sections: {len(timestamps)}")

        # ---------------------------------------------
        # ceny dla wszystkich timestampów
        # ---------------------------------------------
        prices = market_data_service.get_prices_for_timestamps(
            timestamps
        )

        result = {}

        # =============================================
        # iteracja po wszystkich cross sections
        # =============================================
        for current_idx, folder in enumerate(folders):

            json_path = folder / INPUT_FILENAME

            if not json_path.exists():
                print(f"[BRAK] {json_path}")
                continue

            current_timestamp = timestamps[current_idx]

            print(f"[PROCESS] {folder.name}")

            data = load_json(json_path)

            # =============================================
            # ticker
            # =============================================
            for ticker, ticker_data in data.items():

                if ticker not in result:
                    result[ticker] = {}

                # =============================================
                # timeframe
                # =============================================
                for timeframe, timeframe_data in ticker_data.items():

                    forward_steps = TIMEFRAME_FORWARD_MAP.get(timeframe)

                    if forward_steps is None:
                        continue

                    future_idx = current_idx + forward_steps

                    # brak przyszłych danych
                    if future_idx >= len(timestamps):
                        continue

                    future_timestamp = timestamps[future_idx]

                    current_price = (
                        prices
                        .get(current_timestamp, {})
                        .get(ticker)
                    )

                    future_price = (
                        prices
                        .get(future_timestamp, {})
                        .get(ticker)
                    )

                    if current_price is None or future_price is None:
                        continue

                    # =============================================
                    # return
                    # =============================================
                    future_return = (
                        (future_price - current_price)
                        / current_price
                    )

                    score = timeframe_data.get("score")

                    if score is None:
                        continue

                    if timeframe not in result[ticker]:
                        result[ticker][timeframe] = []

                    result[ticker][timeframe].append({
                        "timestamp": current_timestamp.isoformat(),
                        "score": score,
                        "future_return": round(future_return, 6),
                        "current_price": current_price,
                        "future_price": future_price,
                    })

        return result


# =========================================================
# SAVE
# =========================================================

def save_json(data, output_path):

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved:")
    print(output_path)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    dataset = build_score_return_dataset()

    save_json(dataset, OUTPUT_FILE)