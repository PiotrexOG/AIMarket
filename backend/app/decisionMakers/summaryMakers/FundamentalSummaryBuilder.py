from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotCreate


class FundamentalSummaryBuilder:
    """
    Zamienia FundamentalSnapshot (TTM / kwartalne)
    na semantyczny, LLM-friendly summary fundamentów.
    """

    def build(self, snapshot: "FundamentalSnapshotCreate") -> dict:
        if snapshot is None:
            return {"fundamentals": "NO_DATA"}

        return {
            "business_quality": self._business_quality(snapshot),
            "financial_health": self._financial_health(snapshot),
            "cash_generation": self._cash_generation(snapshot),
            "growth_profile": self._growth_profile(snapshot),
            "company_maturity": self._company_maturity(snapshot),
            "raw_snapshot": self._raw_snapshot(snapshot)
        }

    # -------------------------
    # INTERPRETACJE
    # -------------------------

    def _business_quality(self, s) -> str:
        if s.gross_margin_ttm is None or s.operating_margin_ttm is None:
            return "BUSINESS_QUALITY_UNKNOWN"

        if s.gross_margin_ttm > 0.5 and s.operating_margin_ttm > 0.3:
            return "EXCEPTIONAL_MARGIN_BUSINESS"
        if s.gross_margin_ttm > 0.4 and s.operating_margin_ttm > 0.25:
            return "HIGH_MARGIN_BUSINESS"
        if s.operating_margin_ttm < 0.1:
            return "LOW_MARGIN_BUSINESS"

        return "AVERAGE_MARGIN_BUSINESS"

    def _financial_health(self, s) -> str:
        if s.total_debt is None or s.cash_and_equivalents is None:
            return "FINANCIAL_HEALTH_UNKNOWN"

        net_debt = s.total_debt - s.cash_and_equivalents

        if net_debt <= 0:
            return "NET_CASH_POSITION"
        if s.equity and net_debt > s.equity:
            return "BALANCE_SHEET_STRESSED"
        if s.equity and net_debt < s.equity * 0.5:
            return "HEALTHY_BALANCE_SHEET"

        return "MODERATE_LEVERAGE"

    def _cash_generation(self, s) -> str:
        if s.free_cash_flow_ttm is None or s.revenue_ttm is None:
            return "CASH_GENERATION_UNKNOWN"

        fcf_margin = s.free_cash_flow_ttm / s.revenue_ttm

        if fcf_margin > 0.25:
            return "EXCELLENT_CASH_GENERATION"
        if fcf_margin > 0.15:
            return "STRONG_CASH_GENERATOR"
        if fcf_margin < 0.05:
            return "WEAK_CASH_GENERATION"

        return "MODERATE_CASH_GENERATION"

    def _growth_profile(self, s) -> str:
        if s.revenue_growth_ttm_yoy is None or s.eps_growth_ttm_yoy is None:
            return "GROWTH_PROFILE_UNKNOWN"

        if s.revenue_growth_ttm_yoy > 0.15 and s.eps_growth_ttm_yoy > 0.15:
            return "STRONG_GROWTH"
        if s.revenue_growth_ttm_yoy < 0.05 and s.eps_growth_ttm_yoy < 0:
            return "SLOW_GROWTH_WITH_EARNINGS_PRESSURE"
        if s.revenue_growth_ttm_yoy < 0:
            return "REVENUE_CONTRACTION"

        return "MODERATE_GROWTH"

    def _company_maturity(self, s) -> str:
        if s.revenue_ttm is None:
            return "COMPANY_SIZE_UNKNOWN"

        if s.revenue_ttm > 200_000_000_000:
            return "MEGA_CAP_MATURE"
        if s.revenue_ttm > 50_000_000_000:
            return "LARGE_CAP_ESTABLISHED"

        return "MID_CAP_OR_GROWTH_STAGE"

    def _raw_snapshot(self, s) -> dict:
        """
        Zbiór twardych danych finansowych.
        Konwertuje wartości nominalne na czytelne dla LLM formaty.
        """
        net_debt = (s.total_debt or 0) - (s.cash_and_equivalents or 0)

        # Bezpieczne dzielenie dla marż i wskaźników
        def safe_ratio(nom, den, round_to=4):
            if not nom or not den or den == 0:
                return None
            return round(nom / den, round_to)

        return {
            # Rentowność (w ujęciu ułamkowym, np. 0.15 = 15%)
            "margins": {
                "gross": safe_ratio(s.gross_margin_ttm, 1),  # Zakładając że s.gross_margin_ttm to float 0-1
                "operating": safe_ratio(s.operating_margin_ttm, 1),
                "fcf_margin": safe_ratio(s.free_cash_flow_ttm, s.revenue_ttm)
            },
            # Dynamika wzrostu YoY
            "growth_yoy": {
                "revenue": round(s.revenue_growth_ttm_yoy, 4) if s.revenue_growth_ttm_yoy is not None else None,
                "eps": round(s.eps_growth_ttm_yoy, 4) if s.eps_growth_ttm_yoy is not None else None
            },
            # Bilans i zadłużenie
            "balance_sheet": {
                "net_debt_nominal": net_debt,
                "cash_and_equivalents": s.cash_and_equivalents,
                "debt_to_equity": safe_ratio(s.total_debt, s.equity),
                "current_ratio": round(s.current_ratio, 2) if hasattr(s, 'current_ratio') else None
            },
            # Wielkość skali (w milionach dla czytelności, jeśli dane są w jednostkach podstawowych)
            "scale": {
                "revenue_ttm_mln": round(s.revenue_ttm / 1_000_000, 2) if s.revenue_ttm else None,
                "fcf_ttm_mln": round(s.free_cash_flow_ttm / 1_000_000, 2) if s.free_cash_flow_ttm else None
            }
        }
