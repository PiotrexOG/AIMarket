from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotCreate


class FundamentalSummaryBuilder:
    """
    Zamienia FundamentalSnapshot na opis semantyczny z wbudowanymi
    kluczowymi liczbami (inline metrics), ułatwiając pracę LLM.
    """

    def build(self, snapshot: "FundamentalSnapshotCreate") -> dict:
        if snapshot is None:
            return {"fundamentals": "NO_DATA"}

        summary = {
            "business_quality": self._business_quality(snapshot),
            "financial_health": self._financial_health(snapshot),
            "cash_generation": self._cash_generation(snapshot),
            "growth_profile": self._growth_profile(snapshot),
            "company_scale": self._company_maturity(snapshot)
        }

        return summary

    # -------------------------
    # HELPERS FORMATOWANIA
    # -------------------------

    def _fmt_pct(self, val, decimals=1):
        """0.15 -> 15.0%"""
        if val is None: return ""
        return f"{round(val * 100, decimals)}%"

    def _fmt_money(self, val):
        """1_500_000_000 -> $1.5B"""
        if val is None: return ""
        abs_val = abs(val)
        if abs_val >= 1e9: return f"${val / 1e9}B"
        if abs_val >= 1e6: return f"${val / 1e6}M"
        return f"${round(val, 2)}"

    # -------------------------
    # INTERPRETACJE Z LICZBAMI
    # -------------------------

    def _business_quality(self, s) -> str:
        gm, om = s.gross_margin_ttm, s.operating_margin_ttm

        # Logika semantyczna
        label = "UNKNOWN"
        if gm is not None and om is not None:
            if gm > 0.5 and om > 0.3:
                label = "EXCEPTIONAL_MARGIN_BUSINESS"  # Moat?
            elif gm > 0.4 and om > 0.2:
                label = "HIGH_MARGIN_BUSINESS"
            elif om < 0.08:
                label = "LOW_MARGIN_BUSINESS_THIN"
            else:
                label = "AVERAGE_MARGIN_BUSINESS"

        # Inline Metrics: GM i OM to serce jakości biznesu
        metrics = f" (Gross: {self._fmt_pct(gm)}, Oper: {self._fmt_pct(om)})"
        return label + metrics

    def _financial_health(self, s) -> str:
        debt = s.total_debt
        cash = s.cash_and_equivalents
        equity = s.equity
        fcf = s.free_cash_flow_ttm

        if debt is None or cash is None:
            return "UNKNOWN"

        net_debt = debt - cash

        # --- 1. LOGIKA SEMANTYCZNA (bez zmian, bo jest dobra) ---
        label = "MODERATE_LEVERAGE"
        if net_debt <= 0:
            label = "NET_CASH_FORTRESS"
        elif equity and net_debt > equity:
            label = "BALANCE_SHEET_STRESSED"
        elif equity and net_debt < equity * 0.4:
            label = "HEALTHY_BALANCE_SHEET"

        # --- 2. INLINE METRICS (Zamiast nominali -> relacje) ---
        metrics_parts = []

        # A. Dźwignia (Net Debt vs Equity)
        # Mówi: Jak bardzo firma jest zadłużona względem własnego majątku?
        if equity and equity > 0:
            nd_eq_ratio = abs(net_debt) / equity
            # Jeśli Net Debt ujemny (Cash), pokazujemy NetCash/Eq
            prefix = "NetCash/Eq" if net_debt < 0 else "NetDebt/Eq"
            metrics_parts.append(f"{prefix}: {round(nd_eq_ratio, 2)}x")

        # B. Pokrycie (Net Debt vs FCF) - O TO PYTAŁEŚ
        # Mówi: Ile lat zajmie spłata długu netto z wolnych przepływów?
        # Liczymy to tylko, gdy firma ma realny dług (Net Debt > 0)
        if net_debt > 0 and fcf and fcf > 0:
            years_to_repay = net_debt / fcf
            metrics_parts.append(f"YrsToPay: {round(years_to_repay, 1)}x")

        # Jeśli firma ma dług, ale pali gotówkę (ujemne FCF), to jest krytyczne info
        elif net_debt > 0 and fcf and fcf < 0:
            metrics_parts.append("YrsToPay: IMPOSSIBLE (Neg FCF)")

        metrics_str = ", ".join(metrics_parts)
        return f"{label} ({metrics_str})"

    def _cash_generation(self, s) -> str:
        fcf = s.free_cash_flow_ttm
        rev = s.revenue_ttm

        if fcf is None or rev is None or rev == 0: return "UNKNOWN"

        fcf_margin = fcf / rev
        label = "MODERATE_CASH_GEN"

        if fcf_margin > 0.25:
            label = "CASH_COW_EXCELLENT"
        elif fcf_margin > 0.15:
            label = "STRONG_CASH_GENERATION"
        elif fcf_margin < 0.0:
            label = "CASH_BURNER_NEGATIVE_FCF"  # Uwaga, pali gotówkę!
        elif fcf_margin < 0.05:
            label = "WEAK_CASH_CONVERSION"

        # Inline Metrics: FCF Margin (Ile gotówki zostaje z każdego dolara sprzedaży)
        metrics = f" (FCF Mgn: {self._fmt_pct(fcf_margin)})"
        return label + metrics

    def _growth_profile(self, s) -> str:
        rev_g = s.revenue_growth_ttm_yoy
        eps_g = s.eps_growth_ttm_yoy

        if rev_g is None: return "UNKNOWN"

        label = "MODERATE_GROWTH"

        # Logika Growth vs Value trap
        if eps_g is not None:
            if rev_g > 0.20 and eps_g > 0.20:
                label = "HYPER_GROWTH"
            elif rev_g > 0.10 and eps_g > 0.10:
                label = "STRONG_STABLE_GROWTH"
            elif rev_g < 0.05 and eps_g < 0:
                label = "STAGNATION_WITH_PROFIT_ISSUES"
            elif rev_g < 0:
                label = "REVENUE_CONTRACTION"
        else:
            # Fallback gdy brak danych o EPS growth
            if rev_g > 0.15: label = "STRONG_TOPLINE_GROWTH"

        # Inline Metrics: Rev i EPS (Wzrost przychodów vs zysków)
        metrics = f" (Rev: {self._fmt_pct(rev_g)}, EPS: {self._fmt_pct(eps_g)})"
        return label + metrics

    def _company_maturity(self, s) -> str:
        rev = s.revenue_ttm
        if rev is None: return "SIZE_UNKNOWN"

        label = "MID_CAP_OR_GROWTH"
        if rev > 100_000_000_000:
            label = "MEGA_CAP_TITAN"
        elif rev > 20_000_000_000:
            label = "LARGE_CAP_ESTABLISHED"
        elif rev < 1_000_000_000:
            label = "SMALL_CAP_SPECULATIVE"

        # Inline Metrics: Skala przychodów (żeby odróżnić Apple od start-upu)
        metrics = f" (Rev TTM: {self._fmt_money(rev)})"
        return label + metrics