import os
import json
import re
from collections import defaultdict
from pathlib import Path

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.config import TICKERS

APIKey = os.environ.get("API_KEY")

current_dir = Path(__file__).resolve().parent

project_root = current_dir.parents[2]


SYSTEM_PROMPT = """
You are a financial analyst.
Evaluate each news summary for its importance to the company's valuation and operations.

Return:
importance (0.0 - 10.0)
Scale:
0 = noise
5.0 = relevant development
10.0 = industry changing / existential

Use increments of 0.5 (e.g., 7.0, 7.5, 8.0).
Be consistent across the batch. Use the full scale.

Return ONLY JSON.
"""


class NewsImportanceScorer:
    def __init__(self, batch_size=40):
        genai.configure(api_key=APIKey)
        self.batch_size = batch_size
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            generation_config=GenerationConfig(
                temperature=0.1,
                top_p=0.9,
                top_k=20
            )
        )

    def load_news(self, ticker):
        base_path = project_root / "data" / "company_news_summarized" / ticker
        all_news = []

        # Sortujemy pliki, żeby zachować chronologię
        for file_path in sorted(base_path.glob("summarized_*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                summaries = item.get("daily_summary", [])
                if summaries:
                    summary = summaries[0]
                    all_news.append({
                        "date": item["date"],
                        "summary": summary,
                        "original_file": file_path.name,  # Zapamiętujemy nazwę pliku
                        "original_data": item  # Zachowujemy resztę pól (np. linki itp.)
                    })
                else:
                    print(f"Ostrzeżenie: Brak podsumowania w {file_path.name} dla daty {item.get('date')}")

        return all_news

    def batch_iter(self, items):
        for i in range(0, len(items), self.batch_size):
            yield items[i:i + self.batch_size]

    def score_batch(self, batch):
        news_block = [f"{i}: {item['summary']}" for i, item in enumerate(batch)]

        user_prompt = f"""
        Score the following news summaries based on importance.
        {chr(10).join(news_block)}

        Return JSON list like:
        [
          {{ "id": 0, "importance": 7.5 }},
          ...
        ]
        """
        response = self.model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_prompt]}
        ])

        return extract_json(response.text)

    def process_ticker(self, ticker):
        news = self.load_news(ticker)
        if not news:
            print(f"Brak danych dla {ticker}")
            return

        # Słownik do grupowania wyników z powrotem do plików
        files_to_save = defaultdict(list)

        for batch in self.batch_iter(news):
            print(f"Scoring batch of {len(batch)} items...")
            scored_data = self.score_batch(batch)

            for item in scored_data:
                idx = item["id"]
                importance = item["importance"]

                source_item = batch[idx]
                filename = source_item["original_file"]

                # Budujemy finalny obiekt zachowując oryginalne pola i dodając score
                final_entry = source_item["original_data"].copy()
                final_entry["importance"] = importance

                files_to_save[filename].append(final_entry)

        self.save_results(ticker, files_to_save)

    def save_results(self, ticker, grouped_data):
        output_dir = project_root / "data" / "company_news_scored" / ticker
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, entries in grouped_data.items():
            # Zmieniamy nazwę z summarized_... na scored_...
            new_filename = filename.replace("summarized_", "scored_")
            save_path = output_dir / new_filename

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
            print(f"Saved: {save_path}")


def extract_json(text):
    text = re.sub(r'```json\s*|\s*```', '', text)
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1:
        return json.loads(text[start:end + 1])
    raise json.JSONDecodeError("No JSON found", text, 0)


def process_importance_range(
    start_date,
    end_date,
    ticker,
    scorer,
    base_input_folder=Path("data/company_news_summarized"),
    base_output_folder=Path("data/company_news_scored"),
):
    from datetime import datetime

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    INPUT_FOLDER = base_input_folder / ticker
    OUTPUT_FOLDER = base_output_folder / ticker

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    if not INPUT_FOLDER.exists():
        print(f"Brak danych summarized dla {ticker}")
        return

    files = sorted(INPUT_FOLDER.glob("summarized_*.json"))

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 🔹 filtr po dacie
        filtered = [
            item for item in data
            if "date" in item and start_date <= datetime.fromisoformat(item["date"]).date() <= end_date
        ]

        if not filtered:
            continue

        # 🔹 przygotuj dane do scorera
        news_for_scoring = []
        for item in filtered:
            summaries = item.get("daily_summary", [])
            if summaries:
                news_for_scoring.append({
                    "date": item["date"],
                    "summary": summaries[0],
                    "original_data": item
                })

        # 🔹 batch scoring
        results = []
        for batch in scorer.batch_iter(news_for_scoring):
            scored = scorer.score_batch(batch)

            for s in scored:
                idx = s["id"]
                importance = s["importance"]

                base_item = batch[idx]["original_data"].copy()
                base_item["importance"] = importance

                results.append(base_item)

        # 🔹 merge z istniejącym plikiem
        output_file = OUTPUT_FOLDER / file_path.name.replace("summarized_", "scored_")

        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    existing = []
        else:
            existing = []

        existing_by_date = {item["date"]: item for item in existing}

        for item in results:
            existing_by_date[item["date"]] = item

        merged = sorted(existing_by_date.values(), key=lambda x: x["date"])

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
