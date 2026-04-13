import os
import json
import re
from google import genai
from google.genai import types  # Import typów dla konfiguracji

from app.decisionMakers.summaryMakers.FundamentalSummaryBuilder import FundamentalSummaryBuilder
from app.decisionMakers.summaryMakers.NewsNarrativeBuilder import NewsNarrativeBuilder
from app.decisionMakers.summaryMakers.TechnicalSummaryBuilder import TechnicalSummaryBuilder
from app.decisionMakers.summaryMakers.AnalystConsensusBuilder import AnalystConsensusBuilder
from app.decisionMakers.summaryMakers.ValuationSummaryBuilder import ValuationSummaryBuilder
from app.decisionMakers.tickerMaster.systemPrompt import SYSTEM_PROMPT

API_KEY = os.environ.get("API_KEY")


class GEMINI_MASTER:
    def __init__(self):
        # Inicjalizacja klienta
        self.client = genai.Client(api_key=API_KEY)
        self.model_id = "gemini-2.5-flash-lite"

        # Konfiguracja raz w init: system prompt, temperatura i format JSON
        self.config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.9,
            top_k=20,
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json"
        )

        # rolling state per ticker
        self.last_state = {}

    def _build_structured_input(self, ticker, analyst_grades, fundamentals, ohlcv, current_valuation, news_narrative):
        analyst_summary = AnalystConsensusBuilder().build(analyst_grades)
        technical_summary = TechnicalSummaryBuilder().build(ohlcv)
        fundamentals_summary = FundamentalSummaryBuilder().build(fundamentals)
        current_valuation_summary = ValuationSummaryBuilder().build(current_valuation)
        news_narrative_summary = NewsNarrativeBuilder().build(news_narrative)

        return {
            "ticker": ticker,
            "analyst": analyst_summary,
            "technical": technical_summary,
            "fundamentals": fundamentals_summary,
            "current_valuation": current_valuation_summary,
            "news_narrative": news_narrative_summary,
        }

    def analyze(self, ticker, analyst_grades, fundamentals, ohlcv, current_valuation, news_narrative):
        current_input = self._build_structured_input(
            ticker,
            analyst_grades,
            fundamentals,
            ohlcv,
            current_valuation,
            news_narrative
        )

        previous_block = ""
        if ticker in self.last_state:
            prev_input = self.last_state[ticker]["input"]
            prev_output = self.last_state[ticker]["output"]

            previous_block = f"""
            PREVIOUS_INPUT:
            {json.dumps(prev_input, indent=2)}

            PREVIOUS_OUTPUT:
            {json.dumps(prev_output, indent=2)}
            """

        user_prompt = f"""
        {previous_block}

        CURRENT_INPUT:
        {json.dumps(current_input, indent=2)}

        Update the scoring according to the system rules.
        Return valid JSON only.
        """

        try:
            # Wywołanie modelu
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=self.config
            )

            raw_text = response.text.strip()
            parsed = extract_json(raw_text)

            # Aktualizacja rolling state
            self.last_state[ticker] = {
                "input": current_input,
                "output": parsed
            }

            return {
                "input": current_input,
                "output": parsed
            }

        except Exception as e:
            return {
                "input": current_input,
                "output": getattr(response, 'text', "No response text") if 'response' in locals() else "Request failed",
                "error": f"Failed to process or parse JSON: {str(e)}"
            }


def extract_json(text):
    # Czyścimy tagi markdown
    text = re.sub(r'```json\s*|\s*```', '', text)

    start = text.find('{')
    end = text.rfind('}')

    if start != -1 and end != -1:
        json_str = text[start:end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON content")

    raise ValueError("No JSON object found in response")