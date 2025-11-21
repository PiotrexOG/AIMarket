import google.generativeai as genai
import re
from datetime import datetime

genai.configure(api_key=API_KEY)


class LLMGEMINIDM:
    def __init__(self):
        # Konfiguracja Gemini
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.history = []

    def make_decision(self, tickers_data, portfolio, with_explanation):
        """
        tickers_data: słownik {ticker: market_data} dla wszystkich analizowanych spółek
        portfolio: aktualny portfel
        """
        prompt = self._create_prompt(tickers_data, portfolio, with_explanation)

        print("=== PROMPT ===")
        print(prompt)
        print("==============")

        try:
            # Wysyłanie wiadomości do Gemini
            response = self.model.generate_content(prompt)

            reply = response.text.strip()

            print("=== RESPONSE ===")
            print(reply)
            print("================")

            # Zwracamy również prompt i response dla endpointu
            decision, quantity, ticker, explanation = self._parse_response(reply, with_explanation)

            return {
                "decision": decision,
                "quantity": quantity,
                "ticker": ticker,
                "explanation": explanation,
                "prompt": prompt,
                "response": reply,
                "timestamp": datetime.now()
            }

        except Exception as e:
            print(f"Błąd Gemini: {e}")
            return {
                "decision": "HOLD",
                "quantity": 0,
                "ticker": "",
                "explanation": f"Error: {str(e)}",
                "prompt": prompt,
                "response": "",
                "timestamp": datetime.now()
            }

    def _create_prompt(self, tickers_data, portfolio, with_explanation):
        # Formatowanie danych dla wszystkich spółek
        all_tickers_analysis = []

        for ticker, market_data in tickers_data.items():
            if market_data:
                latest = market_data  # Najnowsze dane

                # Obliczanie sygnałów technicznych
                rsi_signal = "OVERSOLD" if latest.get('RSI_14', 50) < 30 else "OVERBOUGHT" if latest.get('RSI_14',
                                                                                                         50) > 70 else "NEUTRAL"
                macd_signal = "BULLISH" if latest.get('MACD', 0) > latest.get('MACD_signal', 0) else "BEARISH"
                price_vs_sma = "ABOVE_20MA" if latest.get('Price_vs_SMA_20', 0) > 0 else "BELOW_20MA"

                ticker_analysis = [
                    f"=== {ticker} ===",
                    f"Price: {latest.get('Close', 'N/A')}",
                    f"RSI: {latest.get('RSI_14', 'N/A')} ({rsi_signal})",
                    f"MACD: {latest.get('MACD', 'N/A')} vs Signal: {latest.get('MACD_signal', 'N/A')} ({macd_signal})",
                    f"Trend vs SMA20: {latest.get('Price_vs_SMA_20', 'N/A')} ({price_vs_sma})",
                    f"Support: {latest.get('Support_20', 'N/A')}, Resistance: {latest.get('Resistance_20', 'N/A')}",
                    f"Momentum (ROC_10): {latest.get('ROC_10', 'N/A')}",
                    f"Volume Ratio: {latest.get('Vol_Ratio_20', 'N/A')}",
                    f"Current Position: {portfolio.shares.get(ticker, 0)} shares",
                    ""
                ]
                all_tickers_analysis.extend(ticker_analysis)

        analysis_text = "\n".join(all_tickers_analysis)

        # Informacje o portfelu
        total_value = portfolio.cash
        portfolio_details = []

        for ticker_name, shares in portfolio.shares.items():
            if shares > 0 and ticker_name in tickers_data:
                market_data = tickers_data[ticker_name]
                if market_data:
                    current_price = market_data[-1].get('Close', 0)
                    position_value = shares * current_price
                    total_value += position_value
                    portfolio_details.append(
                        f"{ticker_name}: {shares} shares, Current Value: {position_value:.2f}"
                    )

        portfolio_summary = "\n".join(portfolio_details) if portfolio_details else "No positions"
        portfolio_summary += f"\nCash: {portfolio.cash:.2f}"
        portfolio_summary += f"\nTotal Portfolio Value: {total_value:.2f}"

        header = (
            "Maximize 1-year profit. Compare all available stocks and make the BEST investment decision.\n\n"
            "TECHNICAL INDICATORS GUIDE:\n"
            "- RSI_14: >70 = overbought (consider sell), <30 = oversold (consider buy)\n"
            "- MACD: Above signal line = bullish, Below = bearish\n"
            "- Price_vs_SMA_20: >0 = above 20-day average (bullish), <0 = below (bearish)\n"
            "- ROC_10: Positive = upward momentum, Negative = downward momentum\n"
            "- Support/Resistance: Key price levels for entry/exit\n"
            "- Vol_Ratio_20: >1 = higher volume than average (confirms moves)\n\n"
            "PRIORITIZE:\n"
            "1. Stocks with strong technical signals (RSI oversold + MACD bullish + above SMA20)\n"
            "2. Risk management and position sizing\n"
            "3. Portfolio diversification\n"
            "4. Profit-taking on overbought positions\n"
        )

        if with_explanation:
            instruction = (
                "Return EXACTLY in this format:\n"
                "DECISION: BUY [TICKER] [QUANTITY] or SELL [TICKER] [QUANTITY] or HOLD 0\n"
                "REASON: <brief comparison explaining why this is the best decision>"
            )
        else:
            instruction = "Return ONLY: BUY [TICKER] [QUANTITY] or SELL [TICKER] [QUANTITY] or HOLD 0"

        prompt = (
            f"{header}\n\n"
            f"CURRENT PORTFOLIO:\n{portfolio_summary}\n\n"
            f"TECHNICAL ANALYSIS OF AVAILABLE STOCKS:\n"
            f"{analysis_text}\n"
            f"AVAILABLE CASH: {portfolio.cash:.2f}\n\n"
            f"BEST DECISION (considering all stocks):\n"
            f"{instruction}"
        )

        return prompt

    def _parse_response(self, reply, with_explanation):
        lines = reply.strip().splitlines()
        if not lines:
            return "HOLD", 0, "", "No response"

        # Szukaj linii z decyzją
        decision_line = None
        for line in lines:
            if any(keyword in line.upper() for keyword in ["BUY", "SELL", "HOLD", "DECISION:"]):
                decision_line = line.upper()
                break

        if not decision_line:
            decision_line = lines[0].upper()

        # domyślne wartości
        decision = "HOLD"
        ticker = ""
        quantity = 0
        explanation = "No explanation"

        # Parsowanie decyzji z tickerem
        if "BUY" in decision_line:
            decision = "BUY"
            # Szukaj tickera i quantity
            parts = decision_line.split()
            for i, part in enumerate(parts):
                if part == "BUY" and i + 2 < len(parts):
                    ticker = parts[i + 1]
                    try:
                        quantity = int(parts[i + 2])
                    except ValueError:
                        quantity = 0
                    break
        elif "SELL" in decision_line:
            decision = "SELL"
            parts = decision_line.split()
            for i, part in enumerate(parts):
                if part == "SELL" and i + 2 < len(parts):
                    ticker = parts[i + 1]
                    try:
                        quantity = int(parts[i + 2])
                    except ValueError:
                        quantity = 0
                    break
        elif "HOLD" in decision_line:
            decision = "HOLD"

        # uzasadnienie
        if with_explanation:
            for line in lines:
                if line.upper().startswith("REASON:") or line.upper().startswith("EXPLANATION:"):
                    explanation = line.strip()
                    break
                elif "REASON:" in line.upper():
                    explanation = line.strip()
                    break

            # Jeśli nie znaleziono reason, weź drugą linię (jeśli istnieje)
            if explanation == "No explanation" and len(lines) > 1:
                for line in lines[1:]:
                    if line.strip() and not any(x in line.upper() for x in ["BUY", "SELL", "HOLD", "DECISION:"]):
                        explanation = line.strip()
                        break

        return decision, quantity, ticker, explanation