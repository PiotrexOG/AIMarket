import os
import json
import re

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.decisionMakers.summaryMakers.FundamentalSummaryBuilder import FundamentalSummaryBuilder
from app.decisionMakers.summaryMakers.NewsNarrativeBuilder import NewsNarrativeBuilder
from app.decisionMakers.summaryMakers.TechnicalSummaryBuilder import TechnicalSummaryBuilder
from app.decisionMakers.summaryMakers.AnalystConsensusBuilder import AnalystConsensusBuilder
from app.decisionMakers.summaryMakers.ValuationSummaryBuilder import ValuationSummaryBuilder
from app.decisionMakers.tickerMaster.systemPrompt import SYSTEM_PROMPT


APIKey = os.environ.get("API_KEY")


class GEMINI_MASTER:


    def __init__(self):
        genai.configure(api_key=APIKey)

        self.system_prompt = SYSTEM_PROMPT

        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            generation_config=GenerationConfig(
                temperature=0.2,
                top_p=0.9,
                top_k=20
            )
        )

        # rolling state per ticker
        self.last_state = {}

    def _build_structured_input(self, ticker, analyst_grades, fundamentals, ohlcv, current_valuation, news_narrative):

        analyst_summary = AnalystConsensusBuilder().build(analyst_grades)
        technical_summary = TechnicalSummaryBuilder().build(ohlcv)
        fundamentals_summary = FundamentalSummaryBuilder().build(fundamentals)
        current_valuation_summary = ValuationSummaryBuilder().build(current_valuation)
        news_narrative = NewsNarrativeBuilder().build(news_narrative)

        return {
            "ticker": ticker,
            "analyst": analyst_summary,
            "technical": technical_summary,
            "fundamentals": fundamentals_summary,
            "current_valuation": current_valuation_summary,
            "news_narrative": news_narrative,
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

        response = self.model.generate_content(
            [
                {"role": "user", "parts": [self.system_prompt]},
                {"role": "user", "parts": [user_prompt]}
            ]
        )

        raw_text = response.text.strip()

        try:
            parsed = extract_json(raw_text)

            # zapis rolling state
            self.last_state[ticker] = {
                "input": current_input,
                "output": parsed
            }

            return {
                "input": current_input,
                "output": parsed
            }

        except json.JSONDecodeError:
            return {
                "input": current_input,
                "output": raw_text,
                "error": "Failed to parse JSON"
            }


def extract_json(text):
    # Usuń znaczniki markdown
    text = re.sub(r'```json\s*|\s*```', '', text)

    # Znajdź pierwsze { i ostatnie }
    start = text.find('{')
    end = text.rfind('}')

    if start != -1 and end != -1:
        json_str = text[start:end + 1]
        return json.loads(json_str)
    else:
        raise json.JSONDecodeError("No JSON object found", text, 0)