class ValuationSummaryBuilder:
    """
    Zamienia słownik z danymi wyceny na opis semantyczny z wbudowanymi liczbami.
    Dzięki temu LLM otrzymuje kontekst (np. 'PREMIUM') oraz precyzję (np. 'P/E: 35.5').
    """

    def build(self, valuation: dict) -> dict:
        v = valuation
        if not v:
            return {"valuation": "NO_DATA"}

        summary = {
            "pricing_multiples": self._valuation_level(v),
            "asset_risk_assessment": self._valuation_risk(v),
            "implied_growth": self._growth_expectation(v),
            "structure_sensitivity": self._capital_structure_impact(v)
        }

        return summary

    # -------------------------
    # HELPERS
    # -------------------------
    def _fmt(self, val, prefix="", suffix=""):
        if val is None: return ""
        return f"{prefix}{round(val, 2)}{suffix}"

    # -------------------------
    # INTERPRETACJE
    # -------------------------

    def _valuation_level(self, v: dict) -> str:
        """
        Ocena czy jest 'tanio' czy 'drogo' na podstawie zysków i przychodów.
        """
        pe = v.get("pe_ratio_ttm")
        ps = v.get("ps_ratio_ttm")

        if pe is None or ps is None: return "UNKNOWN"

        label = "FAIR_VALUATION"
        if pe > 40 or ps > 12:
            label = "HYPER_PREMIUM_PRICED"  # Nvidia-like levels
        elif pe > 25 or ps > 8:
            label = "PREMIUM_VALUATION"
        elif pe < 12 and ps < 2:
            label = "DEEP_VALUE_DISCOUNT"
        elif pe < 18 and ps < 4:
            label = "MODERATE_DISCOUNT"

        # Inline: P/E i P/S (Kluczowe mnożniki ceny)
        metrics = f" (P/E: {self._fmt(pe)}, P/S: {self._fmt(ps)})"
        return label + metrics

    def _valuation_risk(self, v: dict) -> str:
        """
        Ocena ryzyka 'przepłacenia' za aktywa (Book Value) oraz bufor bezpieczeństwa (Dywidenda).
        """
        pb = v.get("pb_ratio")
        div_y = v.get("dividend_yield")  # Wartość ułamkowa np. 0.02 = 2%

        if pb is None: return "RISK_UNKNOWN"

        label = "MODERATE_ASSET_VALUATION"
        if pb > 20:
            label = "EXTREME_MULTIPLE_RISK"  # Płacisz głównie za 'goodwill'
        elif pb > 8:
            label = "HIGH_MULTIPLE_RISK"
        elif pb < 1.5:
            label = "ASSET_BACKED_SAFETY"  # Cena bliska wartości księgowej
        elif pb < 1.0:
            label = "TRADING_BELOW_BOOK_VALUE"

        # Inline: P/B i Dividend Yield (Yield działa jak poduszka powietrzna)
        div_str = f", DivYld: {self._fmt(div_y * 100, suffix='%')}" if div_y else ""
        metrics = f" (P/B: {self._fmt(pb)}{div_str})"

        return label + metrics

    def _growth_expectation(self, v: dict) -> str:
        """
        Co rynek 'wycenia' w obecnej cenie? Wysokie P/E = Oczekiwanie wysokiego wzrostu.
        """
        pe = v.get("pe_ratio_ttm")
        # PEG ratio byłoby tu idealne, ale bazujemy na tym co mamy w wejściu

        if pe is None: return "UNKNOWN"

        label = "MODERATE_GROWTH_PRICED_IN"
        if pe > 50:
            label = "AGGRESSIVE_GROWTH_REQUIRED"  # Firma musi rosnąć, żeby uzasadnić cenę
        elif pe > 30:
            label = "HIGH_GROWTH_EXPECTED"
        elif pe < 10:
            label = "NO_GROWTH_OR_DECLINE_PRICED_IN"
        elif pe < 15:
            label = "LIMITED_GROWTH_EXPECTED"

        # Inline: P/E jako proxy oczekiwań
        metrics = f" (Implied by P/E: {self._fmt(pe)})"
        return label + metrics

    def _capital_structure_impact(self, v: dict) -> str:
        """
        Zastępuje _price_sensitivity.
        Mówi o tym, czy wycena rynkowa (Market Cap) różni się drastycznie od wyceny przejęcia (EV).
        """
        ev = v.get("enterprise_value")
        mc = v.get("market_cap")

        if ev is None or mc is None or mc == 0: return "UNKNOWN"

        # EV/MC Ratio
        # > 1.0: EV większe (Dług netto dodaje ciężaru)
        # < 1.0: EV mniejsze (Gotówka netto odejmuje ciężar)
        ratio = ev / mc

        label = "NEUTRAL_STRUCTURE"
        if ratio > 1.5:
            label = "HEAVILY_LEVERAGED_VALUATION"  # EV dużo wyższe przez dług
        elif ratio > 1.1:
            label = "DEBT_SENSITIVE"
        elif ratio < 0.8:
            label = "CASH_RICH_DISCOUNT"  # EV niższe przez gotówkę
        elif ratio < 0.95:
            label = "NET_CASH_POSITION"

        # Inline: EV/MC (Pokazuje mnożnik dźwigni finansowej na wycenie)
        metrics = f" (EV/MC: {self._fmt(ratio)}x)"
        return label + metrics