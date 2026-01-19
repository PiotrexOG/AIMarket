import pandas as pd

from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotDTO


class TechnicalSummaryBuilder:
    """
    Zamienia ostatni wiersz DataFrame z danymi technicznymi
    na semantyczny, LLM-friendly summary analizy technicznej.
    """

    def build(self, fundamental_snapshot: FundamentalSnapshotDTO) -> dict:
        if fundamental_snapshot is None:
            return {"technical_summary": "NO_DATA"}

        summary = {
            "trend": self._trend_structure(fundamental_snapshot),
            "candle": self._candle_type(fundamental_snapshot),
            "momentum": self._momentum_state(fundamental_snapshot),
            "rsi": self._rsi_context(fundamental_snapshot),
            "volume": self._volume_context(fundamental_snapshot),
            "support_resistance": self._sr_context(fundamental_snapshot),
            "volatility": self._volatility_context(fundamental_snapshot),
            "raw_snapshot": self._raw_snapshot(fundamental_snapshot)
        }

        return summary

    # -------------------------
    # INTERPRETACJE
    # -------------------------

    def _trend_structure(self, r) -> str:
        close = r["Close"]
        sma20, sma50, sma200 = r.get("SMA_20"), r.get("SMA_50"), r.get("SMA_200")

        if pd.isna(sma50) or pd.isna(sma200):
            return "INSUFFICIENT_LONG_TERM_DATA"

        # Dodaj sprawdzenie konsolidacji - średnie blisko siebie
        max_ma = max(sma20, sma50, sma200)
        min_ma = min(sma20, sma50, sma200)
        ma_range_pct = (max_ma - min_ma) / min_ma

        if ma_range_pct < 0.05:  # 5% różnicy między średnimi
            return "CONSOLIDATION_NO_TREND"

        if close > sma20 > sma50 > sma200:
            return "STRONG_UPTREND"
        if close < sma20 < sma50 < sma200:
            return "STRONG_DOWNTREND"
        if sma50 > sma200:
            return "BULLISH_LONG_TERM"
        return "BEARISH_LONG_TERM"

    def _candle_type(self, r) -> str:
        o, h, l, c = r["Open"], r["High"], r["Low"], r["Close"]

        body = abs(c - o)
        range_ = h - l

        if range_ == 0:
            return "FLAT_SESSION"

        body_ratio = body / range_

        if c < o and body_ratio > 0.6:
            return "STRONG_BEARISH_CANDLE"
        if c > o and body_ratio > 0.6:
            return "STRONG_BULLISH_CANDLE"
        if body_ratio < 0.25:
            return "INDECISION_DOJI_LIKE"

        return "NEUTRAL_CANDLE"

    def _momentum_state(self, r) -> str:
        macd = r.get("MACD")
        signal = r.get("MACD_signal")
        hist = r.get("MACD_hist")

        if pd.isna(macd) or pd.isna(signal):
            return "MOMENTUM_UNKNOWN"

        if macd < signal and hist < 0:
            return "BEARISH_MOMENTUM_INCREASING"
        if macd > signal and hist > 0:
            return "BULLISH_MOMENTUM_INCREASING"

        return "MOMENTUM_FLATTENING"

    def _rsi_context(self, r) -> str:
        rsi = r.get("RSI_14")

        if pd.isna(rsi):
            return "RSI_UNKNOWN"

        if rsi < 30:
            return "OVERSOLD_POTENTIAL_BOUNCE"
        if rsi < 45:
            return "WEAK_MOMENTUM"
        if 45 <= rsi <= 70:
            if rsi > 55:
                return "STRONG_MOMENTUM"
            return "HEALTHY_MOMENTUM"
        if rsi > 70:
            return "OVERBOUGHT_RISK"

        return "RSI_UNKNOWN"

    def _volume_context(self, r) -> str:
        vol_ratio = r.get("Vol_Ratio_20")

        if pd.isna(vol_ratio):
            return "VOLUME_UNKNOWN"

        if vol_ratio > 1.5:
            return "HIGH_CONVICTION_MOVE"
        if vol_ratio > 1.1:
            return "ABOVE_AVERAGE_VOLUME"
        if vol_ratio < 0.7:
            return "LOW_PARTICIPATION"

        return "NORMAL_VOLUME"

    def _sr_context(self, r) -> str:
        close = r["Close"]
        support = r.get("Support_20")
        resistance = r.get("Resistance_20")

        if pd.isna(support) or pd.isna(resistance):
            return "SR_UNKNOWN"

        range_ = resistance - support
        if range_ <= 0:
            return "SR_INVALID"

        if close < support:
            return "BREAKDOWN_BELOW_SUPPORT"
        if close > resistance:
            return "BREAKOUT_ABOVE_RESISTANCE"
        if (close - support) / range_ < 0.2:
            return "NEAR_SUPPORT"
        if (resistance - close) / range_ < 0.2:
            return "NEAR_RESISTANCE"

        return "RANGE_MIDDLE"

    def _volatility_context(self, r) -> str:
        atr = r.get("ATR_14")
        close = r.get("Close")

        if pd.isna(atr) or close == 0:
            return "VOLATILITY_UNKNOWN"

        atr_pct = atr / close

        # Kolejność OD NAJWYŻSZYCH WARTOŚCI!
        if atr_pct > 0.08:
            return "EXTREME_VOLATILITY_CAUTION"
        elif atr_pct > 0.05:
            return "HIGH_VOLATILITY"
        elif atr_pct < 0.01:
            return "VERY_LOW_VOLATILITY_STAGNATION"
        elif atr_pct < 0.02:
            return "LOW_VOLATILITY"
        else:
            return "NORMAL_VOLATILITY"  # 0.02 - 0.05

    # -------------------------
    # OPCJONALNE
    # -------------------------

    def _raw_snapshot(self, r) -> dict:
        """
        Rozszerzony snapshot liczbowy zawierający esencję danych technicznych.
        Wszystkie wartości są zaokrąglone dla czytelności i oszczędności tokenów.
        """
        close = r.get("Close", 0)

        # Obliczamy dystans do średnich w % (bardzo ważne dla LLM)
        def pct_diff(val, base):
            if pd.isna(val) or pd.isna(base) or base == 0:
                return None
            return round(((val - base) / base) * 100, 2)

        return {
            # Cena i zmienność
            "price": round(close, 2),
            "atr_pct": round((r.get("ATR_14", 0) / close) * 100, 2) if close > 0 else None,

            # Oscylatory
            "rsi": round(r.get("RSI_14", 0), 1),
            "macd_hist": round(r.get("MACD_hist", 0), 4),

            # Położenie względem średnich (Trend)
            "dist_sma20_pct": pct_diff(close, r.get("SMA_20")),
            "dist_sma50_pct": pct_diff(close, r.get("SMA_50")),
            "dist_sma200_pct": pct_diff(close, r.get("SMA_200")),

            # Wsparcie/Opór i Zakres
            "dist_support_pct": pct_diff(close, r.get("Support_20")),
            "dist_resistance_pct": pct_diff(close, r.get("Resistance_20")),

            # Wolumen
            "vol_ratio": round(r.get("Vol_Ratio_20", 0), 2)
        }
