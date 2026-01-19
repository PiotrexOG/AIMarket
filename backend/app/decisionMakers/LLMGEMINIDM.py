import google.generativeai as genai
import os

from app.decisionMakers.summaryMakers.FundamentalSummaryBuilder import FundamentalSummaryBuilder
from app.decisionMakers.summaryMakers.TechnicalSummaryBuilder import TechnicalSummaryBuilder
from app.decisionMakers.summaryMakers.AnalystConsensusBuilder import AnalystConsensusBuilder
from app.decisionMakers.summaryMakers.ValuationSummaryBuilder import ValuationSummaryBuilder

APIKey = os.environ.get("API_KEY")


class LLMGEMINIDM:
    def __init__(self, ticker):
        genai.configure(api_key=APIKey)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
        self.ticker = ticker

    def create_prompt(self, analyst_grades, fundamentals, ohlcv, current_valuation):


        analyst_summary = AnalystConsensusBuilder().build(analyst_grades)
        technical_summary = TechnicalSummaryBuilder().build(ohlcv)
        fundamentals_summary = FundamentalSummaryBuilder().build(fundamentals)
        current_valuation_summary = ValuationSummaryBuilder().build(current_valuation)

        results = {
            "analyst": analyst_summary,
            "technical": technical_summary,
            "fundamentals": fundamentals_summary,
            "current_valuation": current_valuation_summary,
        }

        return results



