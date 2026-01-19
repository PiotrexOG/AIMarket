from typing import List, Optional

from app.db.schemas.layers.analyst_grades_scheme import AnalystGradesDTO


class AnalystConsensusBuilder:
    """
    Zamienia dane o ocenach analityków (current + previous)
    na semantyczny, LLM-friendly summary sentymentu.
    """

    def build(
            self,
            data: Optional[List["AnalystGradesDTO"]]
    ) -> dict:
        if not data or len(data) < 1:
            return {"analyst_consensus": "NO_DATA"}

        current = data[0]
        previous = data[1] if len(data) > 1 else None

        cur = self._dto_to_percentages(current)
        prev = self._dto_to_percentages(previous) if previous else None

        summary = {
            "consensus_state": self._consensus_state(cur),
            "conviction_level": self._conviction_level(cur),
            "momentum": self._sentiment_momentum(cur, prev),
            "polarization": self._polarization_state(cur, prev)
        }

        return summary

    # -------------------------
    # CORE LOGIC
    # -------------------------

    def _dto_to_percentages(self, dto) -> Optional[dict]:
        if dto is None:
            return None

        values = {
            "strong_buy": dto.analystRatingsStrongBuy or 0,
            "buy": dto.analystRatingsBuy or 0,
            "hold": dto.analystRatingsHold or 0,
            "sell": dto.analystRatingsSell or 0,
            "strong_sell": dto.analystRatingsStrongSell or 0,
        }

        total = sum(values.values())
        if total == 0:
            return None

        bullish = values["strong_buy"] + values["buy"]
        bearish = values["sell"] + values["strong_sell"]

        return {
            "bullish": bullish / total * 100,
            "bearish": bearish / total * 100,
            "hold": values["hold"] / total * 100,
            "strong_buy": values["strong_buy"] / total * 100,
            "strong_sell": values["strong_sell"] / total * 100,
        }

    # -------------------------
    # INTERPRETACJE
    # -------------------------

    def _consensus_state(self, cur: Optional[dict]) -> str:
        if not cur:
            return "CONSENSUS_UNKNOWN"

        if cur["bullish"] >= 65:
            return "STRONGLY_BULLISH_CONSENSUS"
        if cur["bullish"] >= 50:
            return "BULLISH_CONSENSUS"
        if cur["bearish"] >= 50:
            return "BEARISH_CONSENSUS"
        if cur["bearish"] >= 65:
            return "STRONGLY_BEARISH_CONSENSUS"

        return "MIXED_CONSENSUS"

    def _conviction_level(self, cur: Optional[dict]) -> str:
        if not cur:
            return "CONVICTION_UNKNOWN"

        strong_total = cur["strong_buy"] + cur["strong_sell"]

        if strong_total >= 35:
            return "HIGH_CONVICTION"
        if strong_total >= 20:
            return "MODERATE_CONVICTION"

        return "LOW_CONVICTION"

    def _sentiment_momentum(
            self,
            cur: Optional[dict],
            prev: Optional[dict]
    ) -> str:
        if not cur or not prev:
            return "MOMENTUM_UNKNOWN"

        bullish_delta = cur["bullish"] - prev["bullish"]
        bearish_delta = cur["bearish"] - prev["bearish"]

        if bullish_delta > 3 and bearish_delta < 0:
            return "SENTIMENT_IMPROVING"
        if bullish_delta < -3 and bearish_delta > 0:
            return "SENTIMENT_DETERIORATING"
        if abs(bullish_delta) < 2 and abs(bearish_delta) < 2:
            return "SENTIMENT_STABLE"

        return "SENTIMENT_MIXED"

    def _polarization_state(
            self,
            cur: Optional[dict],
            prev: Optional[dict]
    ) -> str:
        if not cur or not prev:
            return "POLARIZATION_UNKNOWN"

        cur_extreme = cur["strong_buy"] + cur["strong_sell"]
        prev_extreme = prev["strong_buy"] + prev["strong_sell"]

        delta = cur_extreme - prev_extreme

        if delta > 3:
            return "INCREASING_POLARIZATION"
        if delta < -3:
            return "DECREASING_POLARIZATION"

        return "POLARIZATION_STABLE"
