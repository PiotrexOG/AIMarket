import os
import json
import re
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
        """
        cross_section_data format:
        {
            "AAPL": {
                "short_term_14d": {...},
                "medium_term_50d": {...},
                "long_term_200d": {...}
            },
            "NVDA": {...}
        }
        """
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

        # Wywołanie zgodne z nowym SDK
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=self.config
            )

            raw_text = response.text.strip()

            # Próba wyciągnięcia JSONa (twój pomocnik extract_json nadal się przyda jako fallback)
            parsed = extract_json(raw_text)

            return {
                "structured_input": current_input,
                "llm_ranker": parsed
            }

        except Exception as e:
            return {
                "structured_input": current_input,
                "llm_ranker": getattr(response, 'text', "No response text"),
                "error": f"Failed to process or parse JSON: {str(e)}"
            }


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