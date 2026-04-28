import os
import json
import random
import re
import time

from google import genai
from google.genai import types  # Importujemy typy dla konfiguracji

from app.decisionMakers.horizonRanker.systemPrompt import SYSTEM_PROMPT

API_KEY = os.environ.get("API_KEY")


class GEMINI_HORIZON:
    def __init__(self):
        # Inicjalizacja klienta
        self.client = genai.Client(api_key=API_KEY)

        # Nazwa modelu (zostawiamy string, którego użyjemy w wywołaniu)
        self.model_id = "gemini-2.5-flash-lite"

        # Definiujemy konfigurację raz - tutaj ląduje system prompt i parametry
        self.config = types.GenerateContentConfig(
            temperature=0.0,
            top_p=0.9,
            top_k=20,
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json"  # Wymuszamy format JSON na poziomie API
        )

    def analyze(self, date_time, cross_section_data: dict):

        if len(cross_section_data) < 3:
            raise ValueError("Cross-sectional analysis requires at least 3 tickers")

        current_input = {
            "date_time": str(date_time),
            "cross_section": cross_section_data
        }

        user_prompt = f"""
    CURRENT_INPUT:
    {json.dumps(current_input, indent=2)}

    Task:
    1. Compare all tickers cross-sectionally.
    2. Produce relative scores for each horizon.
    3. Maintain internal scoring consistency.
    4. Return valid JSON only.
    """

        MAX_RETRIES = 5

        for attempt in range(MAX_RETRIES):
            try:
                print(f"🔁 Attempt {attempt + 1} for {date_time}:")
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=user_prompt,
                    config=self.config
                )

                raw_text = response.text.strip()
                parsed = extract_json(raw_text)

                # dodatkowe zabezpieczenie
                if not isinstance(parsed, dict):
                    raise ValueError("Parsed output is not a dict")

                return {
                    "structured_input": current_input,
                    "llm_ranker": parsed
                }

            except Exception as e:
                print(f"❌ Cross-section attempt {attempt + 1} failed: {e}")

                # ostatnia próba → zwracamy kontrolowany błąd
                if attempt == MAX_RETRIES - 1:
                    return {
                        "structured_input": current_input,
                        "llm_ranker": None,  # 🔴 kluczowe (nie string!)
                        "error": f"Failed after {MAX_RETRIES} attempts: {str(e)}"
                    }

                # exponential backoff + jitter
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
                continue
        return None


def extract_json(text):
    # Czyścimy ewentualne znaczniki markdown, choć przy response_mime_type nie powinno ich być
    text = re.sub(r'```json\s*|\s*```', '', text)

    start = text.find('{')
    end = text.rfind('}')

    if start != -1 and end != -1:
        json_str = text[start:end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

    raise ValueError("No JSON object found")