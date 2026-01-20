import pandas as pd
import numpy as np
from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotDTO


class TechnicalSummaryBuilder:
    """
    Builder integrujący wnioski semantyczne z kluczowymi danymi liczbowymi "inline".
    Dzięki temu LLM otrzymuje np. "OVERSOLD (24.5)" zamiast szukać wartości w innej sekcji.
    """

    def build(self, fundamental_snapshot: FundamentalSnapshotDTO) -> dict:
        r = fundamental_snapshot
        if r is None:
            return {"technical_summary": "NO_DATA"}

        summary = {
            # SEKCJA 1: Horyzonty Czasowe z wbudowanymi liczbami
            "horizons": {
                "short_term_14d": self._analyze_short_term(r),
                "medium_term_50d": self._analyze_medium_term(r),
                "long_term_200d": self._analyze_long_term(r)
            },

            # SEKCJA 2: Fizyka Rynku
            "market_physics": {
                "price": r.get("Close", 0),
                "volatility_context": self._volatility_detailed_context(r),
                "volume_dynamics": self._volume_detailed_context(r),
                "sr_landscape": self._sr_detailed_context(r)
            },
        }

        return summary

    # -------------------------
    # HELPER FORMATOWANIA
    # -------------------------
    def _fmt(self, val, decimals=2, is_pct=False):
        """Bezpieczne formatowanie wartości do stringa dla LLM"""
        if pd.isna(val) or val is None:
            return ""

        num = val * 100 if is_pct else val
        formatted = round(num, decimals)

        # Jeśli to procent, dodajemy znak %, jeśli nie - sama liczba
        suffix = "%" if is_pct else ""
        return f" ({formatted}{suffix})"

    # -------------------------
    # HORYZONT KRÓTKI (14-20 dni)
    # -------------------------
    def _analyze_short_term(self, r) -> dict:
        """Fokus: Momentum, RSI, BB PctB, ROC."""

        # 1. Analiza Świecowa (Bez zmian logiki)
        candle_type = "NEUTRAL"
        o, h, l, c = r["Open"], r["High"], r["Low"], r["Close"]
        body = abs(c - o)
        range_ = h - l

        if range_ > 0:
            body_ratio = body / range_
            upper_wick = h - max(c, o)
            lower_wick = min(c, o) - l

            if c < o and body_ratio > 0.6:
                candle_type = "STRONG_BEARISH"
            elif c > o and body_ratio > 0.6:
                candle_type = "STRONG_BULLISH"
            elif body_ratio < 0.15:
                candle_type = "DOJI_INDECISION"
            elif lower_wick > body * 2:
                candle_type = "HAMMER_PINBAR_BULLISH"
            elif upper_wick > body * 2:
                candle_type = "SHOOTING_STAR_BEARISH"

        # 2. RSI Context
        rsi = r.get("RSI_14")
        rsi_state = "RSI_UNKNOWN"
        if pd.notna(rsi):
            if rsi < 30:
                rsi_state = "OVERSOLD_EXTREME"
            elif rsi < 40:
                rsi_state = "BEARISH_ZONE_WEAK"
            elif 40 <= rsi <= 60:
                rsi_state = "NEUTRAL_ZONE"
            elif rsi > 70:
                rsi_state = "OVERBOUGHT_EXTREME"
            elif rsi > 60:
                rsi_state = "BULLISH_ZONE_STRONG"

        # Dodajemy wartość inline
        rsi_state += self._fmt(rsi, 1)

        # 3. Bollinger Bands (%B)
        bb_pct = r.get("BB_Pct_B")
        bb_state = "BB_UNKNOWN"
        if pd.notna(bb_pct):
            if bb_pct > 1.05:
                bb_state = "BLOW_OFF_TOP_ABOVE_UPPER_BAND"
            elif bb_pct > 0.95:
                bb_state = "TESTING_UPPER_BAND"
            elif bb_pct < -0.05:
                bb_state = "PANIC_DUMP_BELOW_LOWER_BAND"
            elif bb_pct < 0.05:
                bb_state = "TESTING_LOWER_BAND"
            elif 0.45 < bb_pct < 0.55:
                bb_state = "EQUILIBRIUM_MID_BAND"
            else:
                bb_state = "WITHIN_NORMAL_BANDS"

        # Dodajemy wartość inline
        bb_state += self._fmt(bb_pct, 2)

        # 4. ROC (Velocity)
        roc = r.get("ROC_10", 0)
        velocity = "NORMAL"
        if roc > 0.15:
            velocity = "EXPLOSIVE_UP"
        elif roc < -0.15:
            velocity = "IMPLOSIVE_DOWN"
        elif abs(roc) < 0.02:
            velocity = "STAGNANT"

        # Dodajemy wartość inline (jako procent dla czytelności)
        velocity += self._fmt(roc, 2, is_pct=True)

        return {
            "candle_pattern": candle_type,
            "momentum_rsi_14": rsi_state,
            "mean_reversion_bb": bb_state,
            "velocity_roc_10": velocity
        }

    # -------------------------
    # HORYZONT ŚREDNI (50 dni)
    # -------------------------
    def _analyze_medium_term(self, r) -> dict:
        """Fokus: Relacja średnich, MACD Hist, Dystans do SMA50."""
        close = r["Close"]
        sma20, sma50 = r.get("SMA_20"), r.get("SMA_50")

        # 1. Struktura Trendu (Spread %)
        trend_structure = "STRUCTURE_UNCLEAR"
        spread_val = None

        if pd.notna(sma20) and pd.notna(sma50):
            spread_val = (sma20 - sma50) / sma50  # Spread między średnimi
            ma_diff_abs = abs(spread_val)

            if ma_diff_abs < 0.03:
                trend_structure = "CONSOLIDATION_COMPRESSED_MAS"
            elif sma20 > sma50:
                trend_structure = "BULLISH_SMA20_GT_SMA50"
            else:
                trend_structure = "BEARISH_SMA20_LT_SMA50"

        # Inline: spread w procentach
        trend_structure += self._fmt(spread_val, 2, is_pct=True)

        # 2. MACD Cycle (Histogram value)
        macd, signal, hist = r.get("MACD"), r.get("MACD_signal"), r.get("MACD_hist")
        macd_state = "MACD_UNKNOWN"

        if pd.notna(macd) and pd.notna(signal):
            if hist > 0:
                if hist > hist * 1.1:
                    macd_state = "BULLISH_ACCELERATING"
                else:
                    macd_state = "BULLISH_FADING"
            else:
                if hist < hist * 1.1:
                    macd_state = "BEARISH_ACCELERATING"
                else:
                    macd_state = "BEARISH_RECOVERING"

            if abs(macd - signal) / abs(signal) < 0.05:
                macd_state += "_POTENTIAL_CROSS"

        # Inline: wartość histogramu (siła pędu)
        macd_state += self._fmt(hist, 4)

        # 3. Pozycja względem SMA50
        pos_vs_50 = "AT_SMA50"
        dist_50 = None
        if pd.notna(sma50):
            dist_50 = (close - sma50) / sma50
            if dist_50 > 0.05:
                pos_vs_50 = "EXTENDED_ABOVE_SMA50"
            elif dist_50 < -0.05:
                pos_vs_50 = "EXTENDED_BELOW_SMA50"
            elif abs(dist_50) < 0.015:
                pos_vs_50 = "TESTING_SUPPORT_RESISTANCE_SMA50"

        # Inline: dystans do bazy trendu w %
        pos_vs_50 += self._fmt(dist_50, 2, is_pct=True)

        return {
            "trend_alignment": trend_structure,
            "cycle_macd": macd_state,
            "position_sma50": pos_vs_50
        }

    # -------------------------
    # HORYZONT DŁUGI (200 dni)
    # -------------------------
    def _analyze_long_term(self, r) -> dict:
        """Fokus: Dystans do SMA200, Dystans do Year High/Low."""
        close = r["Close"]
        sma50, sma200 = r.get("SMA_50"), r.get("SMA_200")
        year_high, year_low = r.get("Year_High"), r.get("Year_Low")

        # 1. Reżim Rynku (Dystans do SMA200)
        regime = "REGIME_UNKNOWN"
        dist_200 = None

        if pd.notna(sma200):
            dist_200 = (close - sma200) / sma200
            if close > sma200:
                if sma50 and sma50 > sma200:
                    regime = "SECULAR_BULL_MARKET"
                else:
                    regime = "BULL_MARKET_CORRECTION_PHASE"
            else:
                if sma50 and sma50 < sma200:
                    regime = "SECULAR_BEAR_MARKET"
                else:
                    regime = "BEAR_MARKET_RELIEF_RALLY"

        # Inline: Dystans do głównej średniej (kluczowe dla inwestora)
        regime += self._fmt(dist_200, 2, is_pct=True)

        # 2. Golden/Death Cross gap
        cross_signal = "NO_MAJOR_CROSS"
        cross_gap = None
        if pd.notna(sma50) and pd.notna(sma200):
            cross_gap = (sma50 - sma200) / sma200
            if -0.02 < cross_gap < 0.02:
                cross_signal = "CROSS_IMMINENT_OR_HAPPENING"
            elif cross_gap > 0.15:
                cross_signal = "ESTABLISHED_BULL_GAP"
            elif cross_gap < -0.15:
                cross_signal = "ESTABLISHED_BEAR_GAP"

        # Inline: Rozwarcie między 50 a 200 (siła trendu długoterminowego)
        cross_signal += self._fmt(cross_gap, 2, is_pct=True)

        # 3. Yearly Range Position
        yearly_ctx = "RANGE_UNKNOWN"
        dist_extr = None  # Dystans do najbliższego ekstremum

        if pd.notna(year_high) and pd.notna(year_low):
            range_len = year_high - year_low
            if range_len > 0:
                curr_pos = (close - year_low) / range_len

                if close >= year_high * 0.98:
                    yearly_ctx = "BREAKOUT_ALL_TIME/YEARLY_HIGHS"
                    dist_extr = (close - year_high) / year_high  # Ile ponad szczyt
                elif close <= year_low * 1.02:
                    yearly_ctx = "BREAKDOWN_YEARLY_LOWS"
                    dist_extr = (close - year_low) / year_low  # Ile pod dołkiem
                elif curr_pos > 0.8:
                    yearly_ctx = "TRADING_NEAR_HIGHS_DISTRIBUTION"
                    dist_extr = (close - year_high) / year_high  # Ile brakuje do szczytu
                elif curr_pos < 0.2:
                    yearly_ctx = "TRADING_NEAR_LOWS_ACCUMULATION"
                    dist_extr = (close - year_low) / year_low  # Ile brakuje do dołka
                else:
                    yearly_ctx = "STUCK_IN_YEARLY_RANGE"
                    # Dla środka zakresu nie dajemy dystansu, bo jest nieistotny

        # Inline: Dystans do ekstremum (tylko jeśli blisko)
        yearly_ctx += self._fmt(dist_extr, 2, is_pct=True)

        return {
            "market_regime": regime,
            "major_crosses": cross_signal,
            "yearly_range_pos": yearly_ctx
        }

    # -------------------------
    # FIZYKA RYNKU
    # -------------------------

    def _volatility_detailed_context(self, r) -> str:
        atr, close = r.get("ATR_14"), r.get("Close")
        if not atr or not close: return "VOL_UNKNOWN"

        atr_pct = atr / close

        ctx = "NORMAL_HEALTHY"
        if atr_pct > 0.08:
            ctx = "EXTREME_CRASH_OR_PUMP_RISK"
        elif atr_pct > 0.05:
            ctx = "HIGH_EXPANDED"
        elif atr_pct < 0.01:
            ctx = "DEAD_STAGNATION"
        elif atr_pct < 0.02:
            ctx = "SQUEEZE_POTENTIAL_EXPLOSION"

        # Inline: ATR jako procent ceny (np. 3.5%) - LLM wie ile 'ruchu' oczekiwać dziennie
        return ctx + self._fmt(atr_pct, 2, is_pct=True)

    def _volume_detailed_context(self, r) -> str:
        vol_ratio = r.get("Vol_Ratio_20")
        if pd.isna(vol_ratio): return "UNKNOWN"

        ctx = "AVERAGE"
        if vol_ratio > 2.5:
            ctx = "CLIMAX_EXTREME"
        elif vol_ratio > 1.5:
            ctx = "HIGH_INSTITUTIONAL_ACTIVITY"
        elif vol_ratio > 1.1:
            ctx = "ELEVATED"
        elif vol_ratio < 0.6:
            ctx = "DRY_NO_INTEREST"

        # Inline: Ratio (np. 1.8x)
        return ctx + self._fmt(vol_ratio, 2)

    def _sr_detailed_context(self, r) -> str:
        close = r["Close"]
        sup20, res20 = r.get("Support_20"), r.get("Resistance_20")
        y_high, y_low = r.get("Year_High"), r.get("Year_Low")

        ctx = "NO_IMMEDIATE_KEY_LEVELS"
        level_val = None  # Wartość poziomu do wyświetlenia

        # Logika SR
        if y_high and close >= y_high * 0.99:
            ctx = "CRITICAL_RESISTANCE_YEAR_HIGH"
            level_val = y_high
        elif y_low and close <= y_low * 1.01:
            ctx = "CRITICAL_SUPPORT_YEAR_LOW"
            level_val = y_low
        elif pd.notna(sup20) and pd.notna(res20):
            range_ = res20 - sup20
            if range_ > 0:
                if close < sup20:
                    ctx = "BREAKDOWN_MONTHLY_SUPPORT"
                    level_val = sup20
                elif close > res20:
                    ctx = "BREAKOUT_MONTHLY_RESISTANCE"
                    level_val = res20
                elif (close - sup20) / range_ < 0.15:
                    ctx = "TESTING_MONTHLY_SUPPORT"
                    level_val = sup20
                elif (res20 - close) / range_ < 0.15:
                    ctx = "TESTING_MONTHLY_RESISTANCE"
                    level_val = res20

        # Inline: podajemy konkretną cenę poziomu, żeby LLM wiedział gdzie stawiać Stop Loss
        if level_val:
            return f"{ctx} (Level: {round(level_val, 2)})"
        return ctx
