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

        # 1. Benchmark: kup równe wagi tylko w dniu startowym
        if profile.get("name") == "benchmark":
            if date_time.date() == self.start_time.date():
                return self.benchmark_equal_weight_buy(market_scores, portfolio, date_time)
            return {}

        # 2. Parametry profilu
        params = self._extract_profile_params(profile)

        # 3. Wszystkie dostępne tickery
        all_tickers = self._collect_tickers(market_scores)
        if not all_tickers:
            return {}

        # 4. Surowe wyniki i docelowe wagi
        raw_scores = self._compute_raw_scores(all_tickers, market_scores, profile)
        final_weights = self._compute_final_weights(raw_scores, params)

        # 5. Wycena bieżącego portfela
        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash, portfolio.shares, date_time
        )
        portfolio_value = valuation.portfolio_value
        position_info = {p.ticker: (p.value, p.shares) for p in valuation.positions}

        # 6. Oblicz odchylenia od celu (per ticker)
        deviations = self._compute_deviations(
            all_tickers, final_weights, position_info, portfolio_value
        )

        # 7. Podziel tickery na "must act" i "lazy" wg progu
        rebalance_threshold = params["rebalance_threshold"]
        must_sell, must_buy, lazy = self._classify_deviations(deviations, rebalance_threshold)

        # 8. Jeśli brakuje gotówki na zaplanowane kupna, aktywuj część lazy sells
        must_sell, lazy = self._fill_cash_gap(
            must_sell, must_buy, lazy, portfolio.cash, portfolio_value
        )

        # 9. Przelicz decyzje na liczby akcji i zwróć
        active = {**must_sell, **must_buy}
        decisions = self._build_decisions(active, portfolio_value, date_time)

        return decisions

    # -----------------------------------------------------------------------
    # Krok 2: Parametry profilu
    # -----------------------------------------------------------------------

    def _extract_profile_params(self, profile: dict) -> dict:
        return {
            "softmax_temp": max(profile.get("softmax_temp", 1.0), 1e-6),
            "min_exposure": profile.get("min_exposure", 0.5),
            "aggression_slope": profile.get("aggression_slope", 0.2),
            "exposure_baseline": profile.get("exposure_baseline", 5.0),
            # Próg poniżej którego NIE rebalansujemy (w jednostkach wagi, np. 0.02 = 2 pp)
            # Wartość 0.0 oznacza stare zachowanie – rebalansuj zawsze
            "rebalance_threshold": profile.get("rebalance_threshold", 0.0),
        }

    # -----------------------------------------------------------------------
    # Krok 3: Zbierz tickery
    # -----------------------------------------------------------------------

    def _collect_tickers(self, market_scores: dict) -> list[str]:
        return sorted({
            ticker
            for tf in market_scores
            for ticker in market_scores[tf].keys()
        })

    # -----------------------------------------------------------------------
    # Krok 4a: Surowe wyniki
    # -----------------------------------------------------------------------

    def _compute_raw_scores(self, tickers: list[str], market_scores: dict, profile: dict) -> dict:
        return {
            ticker: self.calculate_score(ticker, market_scores, profile)
            for ticker in tickers
        }

    # -----------------------------------------------------------------------
    # Krok 4b: Docelowe wagi (softmax + ekspozycja + filtr 1%)
    # -----------------------------------------------------------------------

    def _compute_final_weights(self, raw_scores: dict, params: dict) -> dict:
        softmax_temp = params["softmax_temp"]
        min_exp = params["min_exposure"]
        slope = params["aggression_slope"]
        baseline = params["exposure_baseline"]

        # Dynamiczna ekspozycja na podstawie Top-5 wyników
        top_scores = sorted(raw_scores.values(), reverse=True)[:5]
        avg_market_score = np.mean(top_scores) if top_scores else 0.0

        raw_exposure = min_exp + (avg_market_score - baseline) * slope
        total_exposure = 1.0 / (1.0 + np.exp(-raw_exposure))  # sigmoid → (0, 1)

        # Stabilny softmax
        tickers_list = list(raw_scores.keys())
        scores_array = np.array([raw_scores[t] for t in tickers_list], dtype=np.float64)
        scaled = scores_array / softmax_temp
        exp_scores = np.exp(scaled - np.max(scaled))
        total_exp_sum = np.sum(exp_scores)

        initial_weights = {
            tickers_list[i]: (exp_scores[i] / total_exp_sum) * total_exposure
            for i in range(len(tickers_list))
        }

        # Filtr szumu (< 1%) + redystrybucja
        survivors = {t: w for t, w in initial_weights.items() if w >= 0.01}
        final_weights = {t: 0.0 for t in raw_scores}

        if survivors:
            survivor_sum = sum(survivors.values())
            for t, w in survivors.items():
                final_weights[t] = (w / survivor_sum) * total_exposure

        return final_weights

    # -----------------------------------------------------------------------
    # Krok 6: Odchylenia aktualne → docelowe
    # -----------------------------------------------------------------------

    def _compute_deviations(
            self,
            all_tickers: list[str],
            final_weights: dict,
            position_info: dict,
            portfolio_value: float,
    ) -> dict:
        deviations = {}
        for ticker in all_tickers:
            target_w = final_weights.get(ticker, 0.0)
            current_val, shares = position_info.get(ticker, (0.0, 0))
            current_w = (current_val / portfolio_value) if portfolio_value > 0 else 0.0
            deviations[ticker] = {
                "target_w": target_w,
                "current_w": current_w,
                "delta_w": target_w - current_w,  # + za mało, − za dużo
                "shares_held": shares,
                "current_val": current_val,
            }
        return deviations

    # -----------------------------------------------------------------------
    # Krok 7: Klasyfikacja: must_sell / must_buy / lazy
    # -----------------------------------------------------------------------

    def _classify_deviations(
            self,
            deviations: dict,
            threshold: float,
    ) -> tuple[dict, dict, dict]:
        """
        Reguły klasyfikacji:
        - target_w == 0        → zawsze must_sell (zamknij pozycję)
        - |delta_w| >= próg    → must_sell lub must_buy
        - |delta_w| < próg     → lazy (pomijamy, chyba że brakuje cash – zob. krok 8)
        """
        must_sell, must_buy, lazy = {}, {}, {}

        for ticker, d in deviations.items():
            abs_delta = abs(d["delta_w"])

            if d["target_w"] == 0.0:
                # Zamknij pozycję bez względu na próg
                if d["shares_held"] > 0:
                    must_sell[ticker] = d
            elif abs_delta >= threshold:
                if d["delta_w"] < 0:
                    must_sell[ticker] = d
                else:
                    must_buy[ticker] = d
            else:
                lazy[ticker] = d

        return must_sell, must_buy, lazy

    # -----------------------------------------------------------------------
    # Krok 8: Uzupełnij lukę gotówkową przez lazy sells
    # -----------------------------------------------------------------------

    def _fill_cash_gap(
            self,
            must_sell: dict,
            must_buy: dict,
            lazy: dict,
            available_cash: float,
            portfolio_value: float,
    ) -> tuple[dict, dict]:
        """
        Jeśli gotówka (bieżąca + oczekiwana ze sprzedaży) nie pokrywa planowanych kupna,
        aktywujemy lazy sells zaczynając od tych z największym ujemnym odchyleniem
        (czyli spółek najbardziej "za dużych" względem celu).
        """
        expected_sell_proceeds = sum(
            abs(d["delta_w"]) * portfolio_value
            for d in must_sell.values()
            if d["shares_held"] > 0
        )
        expected_buy_need = sum(
            d["delta_w"] * portfolio_value
            for d in must_buy.values()
        )

        cash_gap = expected_buy_need - (available_cash + expected_sell_proceeds)

        if cash_gap <= 0:
            # Mamy wystarczająco gotówki – lazy pozostają pominięte
            return must_sell, lazy

        # Sortuj lazy sells od największego ujemnego delta_w (najbardziej "za duże")
        lazy_sells = sorted(
            [(t, d) for t, d in lazy.items() if d["delta_w"] < 0],
            key=lambda x: x[1]["delta_w"],  # najmniejsza (najbardziej ujemna) wartość pierwsza
        )

        must_sell = dict(must_sell)  # kopia – nie mutujemy oryginału
        lazy = dict(lazy)

        for ticker, d in lazy_sells:
            if cash_gap <= 0:
                break
            must_sell[ticker] = d
            cash_gap -= abs(d["delta_w"]) * portfolio_value
            del lazy[ticker]

        return must_sell, lazy

    # -----------------------------------------------------------------------
    # Krok 9: Buduj słownik decyzji
    # -----------------------------------------------------------------------

    def _build_decisions(
            self,
            active: dict,
            portfolio_value: float,
            date_time,
    ) -> dict:
        decisions = {}

        for ticker, d in active.items():
            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            target_w = d["target_w"]
            shares_held = d["shares_held"]

            # --- SCENARIUSZ A: CAŁKOWITA SPRZEDAŻ (target = 0) ---
            if target_w == 0.0:
                if shares_held > 0:
                    decisions[ticker] = {
                        "DECISION": "SELL",
                        "NUMBER": shares_held,
                        "TARGET_WEIGHT": 0.0,
                    }
                continue

            # --- SCENARIUSZ B: REBALANCING ---
            target_val = portfolio_value * target_w
            diff_val = target_val - d["current_val"]
            num = smart_round(diff_val / price)

            if num > 0:
                decisions[ticker] = {
                    "DECISION": "BUY",
                    "NUMBER": num,
                    "TARGET_WEIGHT": round(target_w, 6),
                }
            elif num < 0:
                abs_num = abs(num)
                actual_to_sell = shares_held if abs_num >= shares_held else abs_num
                if actual_to_sell > 0:
                    decisions[ticker] = {
                        "DECISION": "SELL",
                        "NUMBER": actual_to_sell,
                        "TARGET_WEIGHT": round(target_w, 6),
                    }

        return decisions

def smart_round(num):
    return math.floor(num * 100) / 100