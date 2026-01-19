class ValuationSummaryBuilder:
    """
    Zamienia bieżącą wycenę rynkową (price-based)
    na semantyczny, LLM-friendly summary valuation.
    """

    def build(self, valuation: dict) -> dict:
        if not valuation:
            return {"valuation": "NO_DATA"}

        return {
            "valuation_level": self._valuation_level(valuation),
            "valuation_risk": self._valuation_risk(valuation),
            "growth_expectation_embedded": self._growth_expectation(valuation),
            "price_sensitivity": self._price_sensitivity(valuation),
            "raw_snapshot": self._raw_snapshot(valuation)
        }

    # -------------------------
    # INTERPRETACJE
    # -------------------------

    def _valuation_level(self, v: dict) -> str:
        pe = v.get("pe_ratio_ttm")
        ps = v.get("ps_ratio_ttm")

        if pe is None or ps is None:
            return "VALUATION_UNKNOWN"

        if pe > 30 or ps > 8:
            return "PREMIUM_VALUATION"
        if pe < 15 and ps < 3:
            return "DISCOUNT_VALUATION"

        return "FAIR_VALUATION"

    def _valuation_risk(self, v: dict) -> str:
        pe = v.get("pe_ratio_ttm")
        pb = v.get("pb_ratio")

        if pe is None or pb is None:
            return "VALUATION_RISK_UNKNOWN"

        if pe > 30 and pb > 20:
            return "HIGH_MULTIPLE_RISK"
        if pe < 18:
            return "LOW_VALUATION_RISK"

        return "MODERATE_VALUATION_RISK"

    def _growth_expectation(self, v: dict) -> str:
        pe = v.get("pe_ratio_ttm")
        ps = v.get("ps_ratio_ttm")

        if pe is None or ps is None:
            return "GROWTH_EXPECTATION_UNKNOWN"

        if pe > 30 and ps > 7:
            return "AGGRESSIVE_GROWTH_PRICED_IN"
        if pe < 18 and ps < 4:
            return "LIMITED_GROWTH_PRICED_IN"

        return "MODERATE_GROWTH_EXPECTATION"

    def _price_sensitivity(self, v: dict) -> str:
        pe = v.get("pe_ratio_ttm")
        ev = v.get("enterprise_value")
        mc = v.get("market_cap")

        if pe is None or ev is None or mc is None:
            return "PRICE_SENSITIVITY_UNKNOWN"

        if pe > 30:
            return "HIGH_SENSITIVITY_TO_EARNINGS"
        if abs(ev - mc) / mc > 0.1:
            return "SENSITIVE_TO_BALANCE_SHEET"

        return "NORMAL_PRICE_SENSITIVITY"

    def _raw_snapshot(self, v: dict) -> dict:
        """
        Zbiór kluczowych mnożników wyceny.
        Pomaga LLM zrozumieć strukturę kapitałową i realną cenę aktywów.
        """
        ev = v.get("enterprise_value")
        mc = v.get("market_cap")

        # Obliczamy dźwignię (EV/MC) - jeśli > 1, spółka ma dług netto
        ev_mc_ratio = round(ev / mc, 2) if ev and mc else None

        return {
            "pe_ttm": round(v.get("pe_ratio_ttm", 0), 2),
            "ps_ttm": round(v.get("ps_ratio_ttm", 0), 2),
            "pb_ratio": round(v.get("pb_ratio", 0), 2),
            "forward_pe": round(v.get("forward_pe", 0), 2) if v.get("forward_pe") else "N/A",
            "ev_to_market_cap": ev_mc_ratio,
            "dividend_yield": round(v.get("dividend_yield", 0), 3) if v.get("dividend_yield") else 0,
            "peg_ratio": round(v.get("peg_ratio", 0), 2) if v.get("peg_ratio") else "N/A"
        }
