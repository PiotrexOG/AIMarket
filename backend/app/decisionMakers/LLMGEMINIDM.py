import google.generativeai as genai
from datetime import datetime
import os

APIKey = os.environ.get("API_KEY")


class LLMGEMINIDM:
    def __init__(self):
        genai.configure(api_key=APIKey)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")

    # ============================================================
    # PUBLIC METHOD
    # ============================================================
    def make_decision(self, tickers_data, portfolio, with_explanation=False):

        prompt = self._create_prompt(tickers_data, portfolio, with_explanation)

        print("=== PROMPT ===")
        print(prompt)
        print("==============")

        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()

            print("=== RAW RESPONSE ===")
            print(raw_text)
            print("====================")

            decisions = self._parse_multi_ticker_response(raw_text)

            return decisions


        except Exception as e:
            print("Gemini error:", e)

            fallback = {
                ticker: {
                    "DECISION": "HOLD",
                    "NUMBER": 0,
                    "REASON": "error"
                }
                for ticker in tickers_data
            }

            return fallback

    # ============================================================
    # PROMPT GENERATION
    # ============================================================
    def _create_prompt(self, tickers_data, portfolio, with_explanation):

        # ----------------------------------------------------------
        # BUILD FULL TECHNICAL ANALYSIS BLOCK
        # ----------------------------------------------------------
        analysis_lines = []

        for ticker, latest in tickers_data.items():
            if not latest:
                continue

            # SIGNALS
            rsi = latest.get("RSI_14", 50)
            rsi_signal = (
                "OVERSOLD" if rsi < 30 else
                "OVERBOUGHT" if rsi > 70 else
                "NEUTRAL"
            )

            macd = latest.get("MACD", 0)
            macd_sig = latest.get("MACD_signal", 0)
            macd_signal = "BULLISH" if macd > macd_sig else "BEARISH"

            sma = latest.get("Price_vs_SMA_20", 0)
            price_vs_sma = "ABOVE_20MA" if sma > 0 else "BELOW_20MA"

            support = latest.get("Support_20", "N/A")
            resistance = latest.get("Resistance_20", "N/A")

            roc = latest.get("ROC_10", "N/A")
            vol = latest.get("Vol_Ratio_20", "N/A")
            price = latest.get("Close", "N/A")
            position = portfolio.shares.get(ticker, 0)

            # MULTILINE STRUCTURED BLOCK
            analysis_lines.append(
                f"=== {ticker} ===\n"
                f"Price: {price}\n"
                f"RSI: {rsi} ({rsi_signal})\n"
                f"MACD: {macd} vs {macd_sig} ({macd_signal})\n"
                f"Trend vs SMA20: {sma} ({price_vs_sma})\n"
                f"Support: {support}, Resistance: {resistance}\n"
                f"Momentum ROC_10: {roc}\n"
                f"Volume Ratio: {vol}\n"
                f"Current Position: {position}\n"
            )

        analysis_block = "\n".join(analysis_lines)

        # ----------------------------------------------------------
        # PORTFOLIO SUMMARY
        # ----------------------------------------------------------
        portfolio_summary = "\n".join(
            f"{ticker}: {shares} shares"
            for ticker, shares in portfolio.shares.items()
        )

        # ----------------------------------------------------------
        # FIXED HEADER + INSTRUCTIONS
        # ----------------------------------------------------------
        header = (
            "Your task is to generate EXACT trading actions for ALL tickers.\n"
            "Your analysis must ALWAYS aim to MAXIMIZE total portfolio profit over the next 1 year.\n"
            "Decisions MUST strictly follow the technical indicators and current portfolio positions.\n"
            "\n"
            "TECHNICAL INDICATORS GUIDE:\n"
            "- RSI_14: >70 = overbought (sell), <30 = oversold (buy)\n"
            "- MACD: Above signal = bullish, below signal = bearish\n"
            "- Price_vs_SMA_20: >0 = bullish trend, <0 = bearish trend\n"
            "- ROC_10: positive = upward momentum, negative = downward momentum\n"
            "- Support/Resistance: key turning levels for price action\n"
            "- Volume Ratio (Vol_Ratio_20): >1 confirms the strength of market moves\n"
            "\n"
            "PRIORITIZE:\n"
            "1) Strong bullish setups → BUY\n"
            "2) Overbought, weakening, or bearish setups → SELL\n"
            "3) No strong signal → HOLD\n"
            "4) Allocate capital effectively\n"
            "5) Protect the downside to maximize long-term 1-year performance\n"
            "\n"
            "RISK & PORTFOLIO CONSTRAINTS (MANDATORY):\n"
            "- You may SELL a stock only up to the number of shares currently held.\n"
            "- You may NEVER SELL more shares than the portfolio owns.\n"
            "- BUY decisions must consider available cash.\n"
            "\n"
            "OUTPUT FORMAT RULES (STRICT):\n"
            "- One line *per ticker*\n"
            "- Format:\n"
            "  DECISION TICKER NUMBER REASON\n"
            "- DECISION ∈ {BUY, SELL, HOLD}\n"
            "- NUMBER = integer\n"
            "- For HOLD: NUMBER must be 0\n"
            "- TICKER must always appear\n"
            "- REASON = short phrase (no markdown, no lists)\n"
            "- DO NOT output anything besides the list of decision lines\n"
            "\n"
            "EXAMPLE:\n"
            "BUY AAPL 20 strong bullish setup\n"
            "HOLD TSLA 0 neutral indicators\n"
            "SELL NVDA 15 overbought\n"
            "\n"
            "NOW ANALYZE THE DATA BELOW AND OUTPUT DECISIONS:\n"
        )

        return (
            f"{header}\n"
            f"AVAILABLE CASH: {portfolio.cash}\n\n"
            f"PORTFOLIO:\n{portfolio_summary}\n\n"
            f"TECHNICAL ANALYSIS:\n{analysis_block}"
        )

    # ============================================================
    # RESPONSE PARSER
    # ============================================================
    def _parse_multi_ticker_response(self, text):

        decisions = {}
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(" ")
            if len(parts) < 4:
                continue

            decision = parts[0].upper()
            ticker = parts[1].upper()

            try:
                qty = int(parts[2])
            except:
                qty = 0

            reason = " ".join(parts[3:])

            decisions[ticker] = {
                "DECISION": decision,
                "NUMBER": qty,
                "REASON": reason,
            }

        return decisions
