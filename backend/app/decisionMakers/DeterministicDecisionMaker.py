import math

import numpy as np


class DeterministicDecisionMaker:
    def __init__(self, valuation_service, start_time):
        self.valuation_service = valuation_service
        self.start_time = start_time

    def benchmark_equal_weight_buy(self, market_scores, portfolio, date_time):

        # zbierz tickery
        all_tickers = set()
        for tf in market_scores:
            all_tickers.update(market_scores[tf].keys())

        if not all_tickers:
            return {}

        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash, portfolio.shares, date_time
        )

        capital = round(valuation.portfolio_value, 2)

        tickers_data = []

        for ticker in sorted(all_tickers):

            price = self.valuation_service.market_data_service.get_price(
                ticker, date_time
            )

            if not price or price <= 0:
                continue

            tickers_data.append({
                "ticker": ticker,
                "price": price
            })

        n = len(tickers_data)

        if n == 0 or capital <= 0:
            return {}

        target_value = capital / n

        total_used = 0.0

        # pierwszy etap -> floor
        for item in tickers_data:
            exact_shares = target_value / item["price"]

            # floor do 2 miejsc
            shares = int(exact_shares * 100) / 100

            cost = round(shares * item["price"], 2)

            item["shares"] = shares
            item["cost"] = cost
            item["remainder"] = exact_shares - shares

            total_used += cost

        remaining_cash = round(capital - total_used, 2)

        # drugi etap -> rozdanie reszty
        # największe remainder dostają dodatkowe 0.01 akcji
        tickers_data.sort(key=lambda x: x["remainder"], reverse=True)

        changed = True

        while remaining_cash > 0 and changed:

            changed = False

            for item in tickers_data:

                extra_cost = round(item["price"] * 0.01, 2)

                if extra_cost <= remaining_cash:
                    item["shares"] += 0.01
                    item["cost"] = round(item["cost"] + extra_cost, 2)

                    remaining_cash = round(
                        remaining_cash - extra_cost,
                        2
                    )

                    changed = True

        decisions = {}

        equal_weight = round(1 / n, 4)

        for item in tickers_data:

            if item["shares"] > 0:
                decisions[item["ticker"]] = {
                    "DECISION": "BUY",
                    "NUMBER": round(item["shares"], 2),
                    "TARGET_WEIGHT": equal_weight
                }

        return decisions

    def calculate_score(self, ticker, market_scores, profile):
        total_score = 0.0

        # 🔒 deterministic order
        for tf in sorted(profile["time_weights"].keys()):
            tf_weight = profile["time_weights"][tf]

            if tf in market_scores and ticker in market_scores[tf]:
                timeframe_data = market_scores[tf][ticker].get("relative_scores", {})

                # 🔒 deterministic + stable sum
                values = []
                for metric_name in sorted(timeframe_data.keys()):
                    score_value = timeframe_data[metric_name]
                    metric_weight = profile["metric_weights"].get(metric_name, 0.0)
                    values.append(score_value * metric_weight)

                weighted_tf_score = math.fsum(values)
                total_score += weighted_tf_score * tf_weight

        # 🔒 optional clamp (usuwa floating noise)
        return round(total_score, 10)

    def make_decision(self, market_scores, portfolio, date_time):
        profile = portfolio.user_profile

        if profile.get("name") == "benchmark":
            if date_time.date() == self.start_time.date():
                decisions = self.benchmark_equal_weight_buy(
                    market_scores,
                    portfolio,
                    date_time
                )
                return decisions
            return {}

        min_score_threshold = profile.get("min_score_threshold", 4.5)
        softmax_temp = max(profile.get("softmax_temp", 1.0), 1e-6)

        # 🔒 deterministic tickers
        all_tickers = sorted({
            ticker
            for tf in market_scores
            for ticker in market_scores[tf].keys()
        })

        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash, portfolio.shares, date_time
        )

        # 🔒 deterministic raw scores
        raw_scores = {}
        for ticker in all_tickers:
            score = self.calculate_score(ticker, market_scores, profile)

            if score < min_score_threshold:
                continue

            raw_scores[ticker] = score

        if not raw_scores:
            return {}

        # 🔒 STABLE SOFTMAX (log-sum-exp trick)
        scores_array = np.array(list(raw_scores.values()), dtype=np.float64)

        scaled = scores_array / softmax_temp
        max_scaled = np.max(scaled)

        exp_scores = np.exp(scaled - max_scaled)  # 🔥 stabilizacja
        total_exp = np.sum(exp_scores)

        tickers_list = list(raw_scores.keys())

        target_weights = {
            t: float((exp_scores[i] / total_exp) * profile["risk_tolerance"])
            for i, t in enumerate(tickers_list)
        }

        # 🔒 deterministic lookup zamiast next(...)
        position_map = {p.ticker: p.value for p in valuation.positions}

        decisions = {}

        portfolio_value = valuation.portfolio_value
        threshold_amount = portfolio_value * profile.get("rebalance_threshold", 0.02)

        for ticker in sorted(target_weights.keys()):
            target_w = target_weights[ticker]

            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            target_val = portfolio_value * target_w
            current_val = position_map.get(ticker, 0.0)

            diff_val = target_val - current_val

            # # 🔒 epsilon zabezpieczenie
            # if abs(diff_val) <= threshold_amount + 1e-12:
            #     continue

            # 🔒 stable rounding
            num = round(diff_val / price, 2)

            #
            # # 🔒 minimal trade size
            # if abs(num) < 2:
            #     continue

            decisions[ticker] = {
                "DECISION": "BUY" if num > 0 else "SELL",
                "NUMBER": abs(num),
                "TARGET_WEIGHT": round(target_w, 6)  # większa precyzja deterministyczna
            }

        return decisions