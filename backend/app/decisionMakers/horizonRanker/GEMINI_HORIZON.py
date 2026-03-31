import os
import json
import re

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.decisionMakers.horizonRanker.systemPrompt import SYSTEM_PROMPT


API_KEY = os.environ.get("API_KEY")


class GEMINI_HORIZON:

    def __init__(self):

        genai.configure(api_key=API_KEY)

        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            generation_config=GenerationConfig(
                temperature=0.0,
                top_p=0.9,
                top_k=20
            )
        )

        self.system_prompt = SYSTEM_PROMPT

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

        response = self.model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        self.system_prompt,
                        user_prompt
                    ]
                }
            ]
        )

        raw_text = response.text.strip()

        try:

            parsed = extract_json(raw_text)

            return {
                "structured_input": current_input,
                "llm_ranker": parsed
            }

        except Exception:

            return {
                "structured_input": current_input,
                "llm_ranker": raw_text,
                "error": "Failed to parse JSON"
            }


def extract_json(text):

    text = re.sub(r'```json\s*|\s*```', '', text)

    start = text.find('{')
    end = text.rfind('}')

    if start != -1 and end != -1:

        json_str = text[start:end + 1]

        return json.loads(json_str)

    raise ValueError("No JSON object found")