import math
import numpy as np


class DeterministicDecisionMaker:
    def __init__(self, valuation_service, start_time):
        self.valuation_service = valuation_service
        self.start_time = start_time

    def buy_and_hold_equal_weight_buy(self, market_scores, portfolio, date_time):
        all_tickers = sorted({t for tf in market_scores for t in market_scores[tf].keys()})
        if not all_tickers:
            return {}

        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash, portfolio.shares, date_time
        )

        n = len(all_tickers)
        target_per_ticker = valuation.portfolio_value / n
        decisions = {}

        for ticker in all_tickers:
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            # Bezpośrednie wyliczenie ilości akcji (floor do 0.01)
            shares = math.floor((target_per_ticker / price) * 100) / 100

            if shares > 0:
                decisions[ticker] = {
                    "DECISION": "BUY",
                    "NUMBER": shares,
                    "TARGET_WEIGHT": round(1.0 / n, 4)
                }
        return decisions

    def calculate_score(self, ticker, market_scores, profile):
        total_score = 0.0
        for tf in sorted(profile["time_weights"].keys()):
            tf_weight = profile["time_weights"][tf]
            if tf in market_scores and ticker in market_scores[tf]:
                timeframe_data = market_scores[tf][ticker].get("relative_scores", {})

                # Ważona suma metryk
                values = [
                    timeframe_data[m] * profile["metric_weights"].get(m, 0.0)
                    for m in sorted(timeframe_data.keys())
                ]
                total_score += math.fsum(values) * tf_weight
        return round(total_score, 10)

    def _compute_final_weights(self, raw_scores, params):
        # 1. Ekspozycja rynkowa (Sigmoid z Top-5)
        top_scores = sorted(raw_scores.values(), reverse=True)[:5]
        avg_market_score = np.mean(top_scores) if top_scores else 0.0

        raw_exp = params["min_exposure"] + (avg_market_score - params["exposure_baseline"]) * params["aggression_slope"]
        total_exposure = 1.0 / (1.0 + np.exp(-raw_exp))

        # 2. Softmax dla wag (bez filtra 1%)
        tickers = list(raw_scores.keys())
        scores_arr = np.array([raw_scores[t] for t in tickers])

        # Stabilny softmax
        scaled = scores_arr / params["softmax_temp"]
        exp_s = np.exp(scaled - np.max(scaled))
        weights_arr = (exp_s / np.sum(exp_s)) * total_exposure

        return {tickers[i]: weights_arr[i] for i in range(len(tickers))}

    def make_decision(self, market_scores, portfolio, date_time):
        profile = portfolio.user_profile

        # Obsługa buy_and_holdu
        if profile.get("name") == "buy_and_hold":
            if date_time.date() == self.start_time.date():
                return self.buy_and_hold_equal_weight_buy(market_scores, portfolio, date_time)
            return {}

        # 1. Przygotowanie danych
        params = self._extract_profile_params(profile)
        all_tickers = sorted({t for tf in market_scores for t in market_scores[tf].keys()})
        if not all_tickers: return {}

        # 2. Obliczanie wag i wycena
        raw_scores = {t: self.calculate_score(t, market_scores, profile) for t in all_tickers}

        if profile.get("name") == "benchmark":
            total = sum(max(v, 0.0) for v in raw_scores.values())

            if total > 0:
                raw_scores = {
                    t: max(v, 0.0) / total
                    for t, v in raw_scores.items()
                }
            else:
                raw_scores = {t: 0.0 for t in raw_scores}
        else:
            raw_scores = self._compute_final_weights(raw_scores, params)

        valuation = self.valuation_service.calculate_portfolio_details(portfolio.cash, portfolio.shares, date_time)
        pos_info = {p.ticker: (p.value, p.shares) for p in valuation.positions}

        # 3. Klasyfikacja wg rebalance_threshold
        must_sell, must_buy, lazy = {}, {}, {}

        for ticker in all_tickers:
            target_w = raw_scores.get(ticker, 0.0)
            cur_val, cur_shares = pos_info.get(ticker, (0.0, 0))
            cur_w = cur_val / valuation.portfolio_value if valuation.portfolio_value > 0 else 0.0

            delta_w = target_w - cur_w
            data = {"target_w": target_w, "current_val": cur_val, "shares_held": cur_shares, "delta_w": delta_w}

            if target_w == 0:
                if cur_shares > 0: must_sell[ticker] = data
            elif abs(delta_w) >= params["rebalance_threshold"]:
                if delta_w < 0:
                    must_sell[ticker] = data
                else:
                    must_buy[ticker] = data
            else:
                lazy[ticker] = data

        # 4. Pokrycie luki gotówkowej (wykorzystanie lazy sells jeśli trzeba)
        must_sell, _ = self._fill_cash_gap(must_sell, must_buy, lazy, portfolio.cash, valuation.portfolio_value)

        # 5. Budowa decyzji
        decisions = self._build_decisions({**must_sell, **must_buy}, valuation.portfolio_value, date_time)

        return dict(sorted(decisions.items(), key=lambda x: 0 if x[1]["DECISION"] == "SELL" else 1))

    # --- Metody pomocnicze (logika bez zmian, tylko dla kompletności) ---

    def _extract_profile_params(self, profile):
        return {
            "softmax_temp": max(profile.get("softmax_temp", 1.0), 1e-6),
            "min_exposure": profile.get("min_exposure", 0.5),
            "aggression_slope": profile.get("aggression_slope", 0.2),
            "exposure_baseline": profile.get("exposure_baseline", 5.0),
            "rebalance_threshold": profile.get("rebalance_threshold", 0.0),
        }

    def _fill_cash_gap(self, must_sell, must_buy, lazy, cash, total_val):
        needed = sum(d["delta_w"] * total_val for d in must_buy.values())
        available = cash + sum(abs(d["delta_w"]) * total_val for d in must_sell.values() if d["shares_held"] > 0)

        gap = needed - available
        if gap <= 0: return must_sell, lazy

        lazy_sells = sorted([(t, d) for t, d in lazy.items() if d["delta_w"] < 0], key=lambda x: x[1]["delta_w"])
        for t, d in lazy_sells:
            if gap <= 0: break
            must_sell[t] = d
            gap -= abs(d["delta_w"]) * total_val
        return must_sell, lazy

    def _build_decisions(self, active, total_val, date_time):
        res = {}
        for ticker, d in active.items():
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0: continue

            if d["target_w"] == 0:
                res[ticker] = {"DECISION": "SELL", "NUMBER": d["shares_held"], "TARGET_WEIGHT": 0.0}
            else:
                diff_shares = (total_val * d["target_w"] - d["current_val"]) / price
                num = math.floor(diff_shares * 100) / 100

                if num > 0:
                    res[ticker] = {"DECISION": "BUY", "NUMBER": num, "TARGET_WEIGHT": round(d["target_w"], 6)}
                elif num < 0:
                    to_sell = min(d["shares_held"], abs(num))
                    if to_sell > 0:
                        res[ticker] = {"DECISION": "SELL", "NUMBER": to_sell, "TARGET_WEIGHT": round(d["target_w"], 6)}
        return res