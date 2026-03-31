import numpy as np


class DeterministicDecisionMaker:
    def __init__(self, valuation_service):
        self.valuation_service = valuation_service

    def benchmark_equal_weight_buy(self, market_scores, portfolio, date_time, start_time):

        if portfolio.user_profile.get("name") != "benchmark":
            return None

        # tylko pierwszy dzień (ignorujemy godzinę)
        if date_time.date() != start_time.date():
            return None

        # zbierz tickery
        all_tickers = set()
        for tf in market_scores:
            all_tickers.update(market_scores[tf].keys())

        if not all_tickers:
            return {}

        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash, portfolio.shares, date_time
        )

        capital = valuation.portfolio_value
        n = len(all_tickers)

        if n == 0:
            return {}

        equal_weight = 1.0 / n
        target_per_stock_value = capital * equal_weight

        decisions = {}

        for ticker in all_tickers:
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            num_shares = int(target_per_stock_value / price)

            if num_shares > 0:
                decisions[ticker] = {
                    "DECISION": "BUY",
                    "NUMBER": num_shares,
                    "TARGET_WEIGHT": round(equal_weight, 4)
                }

        return decisions

    def calculate_score(self, ticker, market_scores, profile):
        """
        Dopasowane do struktury: market_scores[timeframe][ticker]
        """
        total_score = 0

        for tf, tf_weight in profile["time_weights"].items():
            # Sprawdzamy czy dany horyzont czasowy i ticker istnieją w danych
            if tf in market_scores and ticker in market_scores[tf]:
                timeframe_data = market_scores[tf][ticker].get("relative_scores", {})

                weighted_tf_score = 0
                for metric_name, score_value in timeframe_data.items():
                    metric_weight = profile["metric_weights"].get(metric_name, 0)
                    weighted_tf_score += score_value * metric_weight

                total_score += weighted_tf_score * tf_weight

        return total_score

    def make_decision(self, market_scores, portfolio, date_time):

        profile = portfolio.user_profile

        # 🔥 benchmark - pełne przejęcie kontroli
        if profile.get("name") == "benchmark":
            decisions = self.benchmark_equal_weight_buy(
                market_scores,
                portfolio,
                date_time,
                profile.get("start_time")
            )
            return decisions or {}  # po pierwszym dniu zwróci {}

        # 🔧 parametry z profilu (z fallbackiem)
        min_score_threshold = profile.get("min_score_threshold", 4.5)
        softmax_temp = profile.get("softmax_temp", 1.0)

        # 0. tickery
        all_tickers = set()
        for tf in market_scores:
            all_tickers.update(market_scores[tf].keys())

        # 1. wycena portfela
        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash, portfolio.shares, date_time
        )

        # 2. raw scores + FILTER
        raw_scores = {}
        for ticker in all_tickers:
            score = self.calculate_score(ticker, market_scores, profile)

            # 🔥 per-user threshold
            if score < min_score_threshold:
                continue

            raw_scores[ticker] = score

        # 💰 jeśli nic nie przeszło → brak decyzji (cash)
        if not raw_scores:
            return {}

        # 3. SOFTMAX (per-user temperatura)
        exp_scores = {
            t: np.exp(s / softmax_temp)
            for t, s in raw_scores.items()
        }

        total_exp = sum(exp_scores.values())

        target_weights = {
            t: (v / total_exp) * profile["risk_tolerance"]
            for t, v in exp_scores.items()
        }

        # 4. decyzje
        decisions = {}

        for ticker, target_w in target_weights.items():
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            target_val = valuation.portfolio_value * target_w
            current_val = next((p.value for p in valuation.positions if p.ticker == ticker), 0)

            diff_val = target_val - current_val

            threshold_amount = valuation.portfolio_value * profile.get("rebalance_threshold", 0.02)

            if abs(diff_val) > threshold_amount:
                num = int(diff_val / price)
                if num != 0:
                    decisions[ticker] = {
                        "DECISION": "BUY" if num > 0 else "SELL",
                        "NUMBER": abs(num),
                        "TARGET_WEIGHT": round(target_w, 4)
                    }

        return decisions