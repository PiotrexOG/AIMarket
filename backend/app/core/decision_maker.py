import random
from openai import OpenAI

API_KEY = "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"
WYNIK_FILE = "wyniki.csv"
MODEL = "gpt-4o-mini"

client = OpenAI(api_key=API_KEY)


class DecisionMaker:
    def __init__(self, use_model=True):
        self.use_model = use_model
        self.history = []

    def make_decision(self, ticker, market_data, portfolio, with_explanation):
        if self.use_model:
            return self._model_decision(ticker, market_data, portfolio, with_explanation)
        return self._random_decision(ticker, market_data, portfolio)

    def _model_decision(self, ticker,  market_data, portfolio, with_explanation):
        prompt = self._create_prompt(ticker, market_data, portfolio)
        response = client.chat.completions.create(
            model=MODEL,
            messages=self.history + [{"role": "user", "content": prompt}],
            temperature=0.3
        )
        reply = response.choices[0].message.content.strip()
        return self._parse_response(reply, with_explanation)

    def _random_decision(self, ticker, market_data, portfolio):
        possible_actions = ["KUPUJ", "SPRZEDAJ", "TRZYMAJ", "TRZYMAJ", "TRZYMAJ", "TRZYMAJ", "TRZYMAJ", "TRZYMAJ", "TRZYMAJ", "TRZYMAJ"]
        decision = random.choice(possible_actions)
        close = float(market_data[0].close)

        if decision == "KUPUJ":
            max_affordable = int(portfolio.cash // close)
            num = random.randint(1, max(1, max_affordable)) if max_affordable > 0 else 0
            if num == 0:
                decision = "TRZYMAJ"
        elif decision == "SPRZEDAJ":
            num = random.randint(1, portfolio.shares[ticker]) if portfolio.shares.get(ticker, 0) > 0 else 0
            if num == 0:
                decision = "TRZYMAJ"
        else:
            num = 0

        return decision, num, "Brak uzasadnienia"

    def _create_prompt(self, ticker, market_data, portfolio):
        return (
            f"Dane dnia ({ticker}): {market_data}. "
            f"Masz {portfolio.shares.get(ticker, 0)} akcji tej spółki i {portfolio.cash:.2f} USD. Co robisz?"
        )


    def _parse_response(self, reply, with_explanation):
        lines = reply.strip().splitlines()
        decision = "NIEZNANE"
        num = 0
        explanation = "Brak uzasadnienia"

        if len(lines) >= 1:
            decision_line = lines[0].strip().upper()
            if decision_line.startswith("KUPUJ"):
                decision = "KUPUJ"
                num = self._extract_number(decision_line)
            elif decision_line.startswith("SPRZEDAJ"):
                decision = "SPRZEDAJ"
                num = self._extract_number(decision_line)
            elif decision_line.startswith("TRZYMAJ"):
                decision = "TRZYMAJ"
                num = 0

            if with_explanation and len(lines) >= 2:
                if lines[1].upper().startswith("UZASADNIENIE"):
                    explanation = lines[1].strip()

        return decision, num, explanation

    def _extract_number(self, text):
        import re
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0