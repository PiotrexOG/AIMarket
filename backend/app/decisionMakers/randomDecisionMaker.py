import random

class RandomDecisionMaker:
    def make_decision(self, ticker, market_data, portfolio, with_explanation=False):
        possible_actions = ["BUY", "SELL", "HOLD"]
        weights = [1, 1, 11]
        decision = random.choices(possible_actions, weights=weights, k=1)[0]
        close = float(market_data[0].close)

        if decision == "BUY":
            max_affordable = int(portfolio.cash // close)
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

        return decision, num, "Brak uzasadnienia"
