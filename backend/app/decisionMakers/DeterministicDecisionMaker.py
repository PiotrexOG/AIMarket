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

        # 1. Obsługa benchmarku
        if profile.get("name") == "benchmark":
            if date_time.date() == self.start_time.date():
                return self.benchmark_equal_weight_buy(market_scores, portfolio, date_time)
            return {}

        # 2. Pobranie parametrów profilu
        softmax_temp = max(profile.get("softmax_temp", 1.0), 1e-6)
        min_exp = profile.get("min_exposure", 0.5)
        slope = profile.get("aggression_slope", 0.2)
        baseline = profile.get("exposure_baseline", 5.0)

        # 3. Pobranie wszystkich dostępnych tickerów (zazwyczaj 18)
        all_tickers = sorted({
            ticker
            for tf in market_scores
            for ticker in market_scores[tf].keys()
        })

        if not all_tickers:
            return {}

        # 4. Obliczenie surowych punktów (Scores)
        raw_scores = {ticker: self.calculate_score(ticker, market_scores, profile)
                      for ticker in all_tickers}

        # 5. Dynamiczne obliczenie całkowitej ekspozycji (Total Exposure)
        # Patrzymy na średnią Top 5 wyników, by ocenić ogólną kondycję rynku
        top_scores = sorted(raw_scores.values(), reverse=True)[:5]
        avg_market_score = np.mean(top_scores) if top_scores else 0

        # Wzór: $$Exposure = \min(1.0, \max(0.0, min\_exp + (AvgScore - baseline) \times slope))$$
        total_exposure = min_exp + (avg_market_score - baseline) * slope
        total_exposure = float(np.clip(total_exposure, 0.0, 1.0))

        # 6. Stabilny Softmax dla wag względnych
        tickers_list = list(raw_scores.keys())
        scores_array = np.array([raw_scores[t] for t in tickers_list], dtype=np.float64)

        scaled = scores_array / softmax_temp
        max_scaled = np.max(scaled)
        exp_scores = np.exp(scaled - max_scaled)
        total_exp_sum = np.sum(exp_scores)

        # Wstępne wagi (proporcjonalne do punktów i ograniczone przez total_exposure)
        initial_weights = {
            tickers_list[i]: (exp_scores[i] / total_exp_sum) * total_exposure
            for i in range(len(tickers_list))
        }

        # 7. Filtracja "szumu" (1%) i Redystrybucja wag
        # Chcemy, aby suma wag po usunięciu małych pozycji nadal wynosiła total_exposure
        final_weights = {t: 0.0 for t in all_tickers}
        survivors = {t: w for t, w in initial_weights.items() if w >= 0.01}

        if survivors:
            survivor_sum = sum(survivors.values())
            # Redystrybucja: skalujemy pozostałe spółki tak, by ich suma wróciła do poziomu total_exposure
            for t, w in survivors.items():
                final_weights[t] = (w / survivor_sum) * total_exposure
        # Jeśli nikt nie przeżył progu 1%, portfel ucieka do 100% gotówki (final_weights pozostają 0.0)

        # 8. Generowanie decyzji handlowych
        valuation = self.valuation_service.calculate_portfolio_details(
            portfolio.cash, portfolio.shares, date_time
        )
        portfolio_value = valuation.portfolio_value

        # Mapujemy: ticker -> (wartość, liczba_akcji)
        # Zakładam, że valuation.positions to obiekty posiadające .ticker, .value i .shares
        position_info = {p.ticker: (p.value, p.shares) for p in valuation.positions}

        decisions = {}

        for ticker in all_tickers:  # Idziemy po wszystkich, żeby obsłużyć sprzedaż do 0
            target_w = final_weights.get(ticker, 0.0)
            current_val, shares_held = position_info.get(ticker, (0.0, 0))

            price = self.valuation_service.market_data_service.get_price(ticker, date_time)
            if not price or price <= 0:
                continue

            # SCENARIUSZ 1: CAŁKOWITA SPRZEDAŻ (Waga spadła do 0 lub < 1%)
            if target_w == 0:
                if shares_held > 0:
                    decisions[ticker] = {
                        "DECISION": "SELL",
                        "NUMBER": shares_held,  # Sprzedajemy dokładnie tyle, ile mamy
                        "TARGET_WEIGHT": 0.0
                    }
                continue

            # SCENARIUSZ 2: REBALANCING (Kupno lub częściowa sprzedaż)
            target_val = portfolio_value * target_w
            diff_val = target_val - current_val

            # Surowa liczba akcji do handlu
            num = smart_round(diff_val / price)

            if num > 0:
                # KUPNO: Tutaj jedynym ograniczeniem jest gotówka (co obsłuży silnik niżej)
                decisions[ticker] = {
                    "DECISION": "BUY",
                    "NUMBER": num,
                    "TARGET_WEIGHT": round(target_w, 6)
                }
            elif num < 0:
                # SPRZEDAŻ: Nie możemy sprzedać więcej niż mamy!
                abs_num = abs(num)

                # Bezpiecznik: jeśli zaokrąglenie chce sprzedać prawie wszystko,
                # lub więcej niż mamy, zamień to na "SELL ALL"
                if abs_num >= shares_held:
                    actual_num_to_sell = shares_held
                else:
                    actual_num_to_sell = abs_num

                if actual_num_to_sell > 0:
                    decisions[ticker] = {
                        "DECISION": "SELL",
                        "NUMBER": actual_num_to_sell,
                        "TARGET_WEIGHT": round(target_w, 6)
                    }

        return decisions

def smart_round(num):
    return math.floor(num * 100) / 100