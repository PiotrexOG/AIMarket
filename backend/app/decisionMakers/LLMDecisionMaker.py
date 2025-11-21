import time

from openai import OpenAI
import re


class LLMDecisionMaker:
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY)
        self.history = []
        self.rpm_limit = rpm_limit
        self.min_delay = 60 / rpm_limit
        self.last_call = 0

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self.last_call

        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            print(f"[LLM] Waiting {wait_time:.2f}s to respect RPM limit…")
            time.sleep(wait_time)

        self.last_call = time.time()

    def make_decision(self, ticker, market_data, portfolio, with_explanation):
        prompt = self._create_prompt(ticker, market_data, portfolio, with_explanation)

        print(prompt)

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=self.history + [{"role": "user", "content": prompt}],
            temperature=0.2
        )

        reply = response.choices[0].message.content.strip()

        print(reply)
        return self._parse_response(reply, with_explanation)

    def _create_prompt(self, ticker, market_data, portfolio, with_explanation):
        formatted_data = "\n".join([
            f"{d.datetime.strftime('%d-%m-%Y %H:%M')} o={d.open} h={d.high} l={d.low} c={d.close} v={d.volume}"
            for d in market_data
        ])

        header = "Maximize 3-month profit. Decide investment action."

        if with_explanation:
            instruction = (
                "Return:\n"
                "BUY X or SELL X or HOLD 0\n"
                "Reason: <1 short sentence>"
            )
        else:
            instruction = "Return ONLY: BUY X or SELL X or HOLD 0"

        prompt = (
            f"{header}\n\n"
            f"{ticker}:\n"
            f"{formatted_data}\n"
            f"pos={portfolio.shares.get(ticker, 0)}, cash={portfolio.cash:.2f}\n"
            f"{instruction}"
        )

        return prompt

    def _parse_response(self, reply, with_explanation):
        lines = reply.strip().splitlines()
        if not lines:
            return "HOLD", 0, "Brak uzasadnienia"

        first_line = lines[0].upper()

        # domyślne wartości
        decision = "HOLD"
        num = 0
        explanation = "Brak uzasadnienia"

        if first_line.startswith("BUY"):
            decision = "BUY"
        elif first_line.startswith("SELL"):
            decision = "SELL"
        elif first_line.startswith("HOLD"):
            decision = "HOLD"

        # wyciąganie liczby
        match = re.search(r"(\d+)", first_line)
        if match:
            num = int(match.group(1))

        # uzasadnienie tylko jeśli oczekiwane
        if with_explanation and len(lines) > 1:
            explanation = lines[1].strip()

        return decision, num, explanation
