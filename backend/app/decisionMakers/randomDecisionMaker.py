import random


class RandomDecisionMaker:
    def make_decision(self, tickers_data, portfolio, with_explanation=False):
        results = {}

        for ticker, market_data in tickers_data.items():
            possible_actions = ["BUY", "SELL", "HOLD"]
            weights = [1, 1, 11]
            decision = random.choices(possible_actions, weights=weights, k=1)[0]

            if market_data:
                close = float(market_data.get("Close"))
            else:
                close = 0
                decision = "HOLD"  # brak danych, więc HOLD

            if decision == "BUY":
                max_affordable = int(portfolio.cash // close) if close > 0 else 0
                num = random.randint(1, max(1, max_affordable)) if max_affordable > 0 else 0
                if num == 0:
                    decision = "HOLD"

            elif decision == "SELL":
                num = random.randint(1, portfolio.shares.get(ticker, 0)) \
                    if portfolio.shares.get(ticker, 0) > 0 else 0
                if num == 0:
                    decision = "HOLD"
            else:
                num = 0

            results[ticker] = {
                "DECISION": decision,
                "NUMBER": num,
                "REASON": "Brak uzasadnienia"
            }

        return results