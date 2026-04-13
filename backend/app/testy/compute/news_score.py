import os
import json
import re
from pathlib import Path

from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parents[3]  # backend/

class NewsImportanceScorer:
    def __init__(self, batch_size: int = 20):
        self.batch_size = batch_size

        # Konfiguracja nowego klienta
        self.client = genai.Client(api_key=os.environ.get("API_KEY"))

        self.model = "gemini-2.5-flash-lite"

        self.config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            system_instruction="""
                        You are a financial analyst. Evaluate news importance (0.0-10.0).
                        Return ONLY a JSON list of objects: [{"date": "YYYY-MM-DD", "importance": float}]
                    """
        )

    def _extract_json(self, text: str) -> dict:
        """Wyciąga dane JSON z odpowiedzi modelu."""
        try:
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                results = json.loads(match.group())
                return {res['date']: res['importance'] for res in results if 'date' in res}
        except Exception as e:
            print(f"❌ Błąd parsowania JSON: {e}")
        return {}

    def _load_ticker_data(self, input_dir: Path) -> list:
        """Wczytuje i sortuje wszystkie dostępne podsumowania dla tickera."""
        all_data = []
        files = sorted(input_dir.glob("summarized_*.json"))
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data.extend(data)
        return sorted(all_data, key=lambda x: x["date"])

    def _get_existing_scores(self, output_dir: Path) -> dict:
        """Sprawdza, które daty mają już przypisane oceny w folderze wynikowym."""
        existing = {}
        if not output_dir.exists():
            return existing
        for f_path in output_dir.glob("scored_*.json"):
            with open(f_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    if "importance" in item:
                        existing[item["date"]] = item["importance"]
        return existing

    def _score_batch(self, batch: list) -> dict:
        """Komunikuje się z API Gemini w celu oceny paczki newsów."""
        news_block = [f"Date: {i['date']} | Summary: {i['summary']}" for i in batch]
        user_prompt = "Score these summaries:\n" + "\n".join(news_block)

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=self.config
        )

        return self._extract_json(response.text)

    def _save_merged_results(self, input_dir: Path, output_dir: Path, new_scores: dict, existing_scores: dict):
        """Łączy nowe oceny ze starymi i zapisuje do odpowiednich plików."""
        output_dir.mkdir(parents=True, exist_ok=True)

        for input_file in input_dir.glob("summarized_*.json"):
            with open(input_file, "r", encoding="utf-8") as f:
                items = json.load(f)

            for item in items:
                d = item["date"]
                # KLUCZOWA LOGIKA:
                # 1. Jeśli data była już oceniona wcześniej - zachowaj starą ocenę (PRIORYTET)
                if d in existing_scores:
                    item["importance"] = existing_scores[d]
                # 2. Jeśli data jest nowo oceniona w tym przebiegu - dodaj nową
                elif d in new_scores:
                    item["importance"] = new_scores[d]

            output_path = output_dir / input_file.name.replace("summarized_", "scored_")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)

    def process_ticker(self, ticker: str, start_date: str, end_date: str):
        """Główna orkiestracja procesu dla danego tickera."""
        input_dir = BASE_DIR / "data" / "news" / "company_news_summarized" / ticker
        output_dir = BASE_DIR / "data"  / "news" / "company_news_scored" / ticker

        # 1. Dane i status
        all_data = self._load_ticker_data(input_dir)
        if not all_data:
            print(f"Brak danych dla {ticker}")
            return

        existing_scores = self._get_existing_scores(output_dir)
        all_dates = [d["date"] for d in all_data]

        # 2. Znalezienie punktu startu (od końca)
        try:
            current_idx = next(i for i, d in enumerate(reversed(all_dates)) if d <= end_date)
            current_idx = len(all_dates) - 1 - current_idx
        except StopIteration:
            return

        # 3. Iteracja wsteczna (Tworzenie batchy)
        new_scores = {}
        processed_until = all_dates[current_idx]

        while processed_until >= start_date:
            start_idx = max(0, current_idx - self.batch_size + 1)
            window_dates = all_dates[start_idx: current_idx + 1]

            # Budujemy batch
            batch = []
            needs_scoring = False
            for d in window_dates:
                item = next((item for item in all_data if item["date"] == d), None)

                if not item or not item.get("daily_summary"):
                    continue

                summary = item["daily_summary"][0]
                batch.append({"date": d, "summary": summary})
                if d not in existing_scores:
                    needs_scoring = True

            # 4. Scoring jeśli potrzeba
            if needs_scoring:
                print(f"🚀 {ticker} | Scoring: {window_dates[0]} - {window_dates[-1]}")
                batch_results = self._score_batch(batch)
                new_scores.update(batch_results)
            else:
                print(f"⏭️ {ticker} | Skipping: {window_dates[0]} - {window_dates[-1]}")

            current_idx = start_idx - 1
            if current_idx < 0: break
            processed_until = all_dates[current_idx]

        # 5. Zapis
        self._save_merged_results(input_dir, output_dir, new_scores, existing_scores)
        print(f"✅ Gotowe: {ticker}")