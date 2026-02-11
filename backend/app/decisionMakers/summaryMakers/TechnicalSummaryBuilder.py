import pandas as pd
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
                "sr_landscape": self._sr_landscape(r)
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
        """
        Fokus: Momentum, RSI, BB PctB, ROC + SMA20 Context + S/R 20 Range.
        Horyzont: 14-20 sesji.
        """

        # 1. Analiza Świecowa (Twoja bazowa logika)
        candle_type = "NEUTRAL"
        o, h, l, c = r.get("Open", 0), r.get("High", 0), r.get("Low", 0), r.get("Close", 0)
        atr = r.get("ATR_14")
        atr_pct = (atr / c) if (pd.notna(atr) and c > 0) else 0.02  # fallback 2%
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

        # 2. RSI Context (Twoja bazowa logika)
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
        rsi_state += self._fmt(rsi, 1)

        # 3. Bollinger Bands (%B) (Twoja bazowa logika)
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
            else:
                bb_state = "WITHIN_NORMAL_BANDS"
        bb_state += self._fmt(bb_pct, 2)

        # 4. ROC (Velocity) - STANDARYZACJA
        # Zamiast 0.15 (15%), używamy krotności ATR.
        roc = r.get("ROC_10", 0)
        # 10-dniowy ruch 'normalny' to np. 2 x ATR_14
        velocity = "NORMAL"
        if roc > (atr_pct * 3):  # Ruch silniejszy niż 3-krotność dziennej zmienności
            velocity = "EXPLOSIVE_UP"
        elif roc < -(atr_pct * 3):
            velocity = "IMPLOSIVE_DOWN"
        elif abs(roc) < (atr_pct * 0.5):
            velocity = "STAGNANT"
        velocity += self._fmt(roc, 2, is_pct=True)

        # 5. Price vs SMA 20 - STANDARYZACJA
        p_vs_sma20_val = r.get("Price_vs_SMA_20")
        sma20_context = "STABLE_NEAR_BASE"

        if pd.notna(p_vs_sma20_val):
            # Tutaj progi adaptacyjne:
            # Bardzo mocne odchylenie to np. 2.5 * ATR
            if p_vs_sma20_val > (atr_pct * 2.5):
                sma20_context = "EXTENDED_BULLISH_OVERSTRETCHED"
            elif p_vs_sma20_val < -(atr_pct * 2.5):
                sma20_context = "EXTENDED_BEARISH_OVERSTRETCHED"
            elif abs(p_vs_sma20_val) < (atr_pct * 0.3):
                sma20_context = "HUGGING_SMA20_CONSOLIDATION"

        sma20_context += self._fmt(p_vs_sma20_val, 2, is_pct=True)

        # 6. S/R 20 (Wsparcie/Opór) - STANDARYZACJA
        sup20 = r.get("Support_20")
        res20 = r.get("Resistance_20")
        sr_status = "IN_MIDDLE_OF_RANGE"

        if pd.notna(sup20) and pd.notna(res20):
            dist_to_sup = (c - sup20) / c
            dist_to_res = (res20 - c) / c

            # 'Bliskość' to teraz 0.5 * ATR, a nie sztywne 1.5%
            near_threshold = atr_pct * 0.5

            if abs(dist_to_sup) < near_threshold:
                sr_status = "AT_CRITICAL_SUPPORT_20"
            elif abs(dist_to_res) < near_threshold:
                sr_status = "AT_CRITICAL_RESISTANCE_20"
            elif c > res20:
                sr_status = "BREAKOUT_ABOVE_20D_HIGH"
            elif c < sup20:
                sr_status = "BREAKDOWN_BELOW_20D_LOW"

        # Inline info o zakresie
        sr_status += f" [Range: {round(sup20, 2) if sup20 else '?'}-{round(res20, 2) if res20 else '?'}]"

        return {
            "candle_pattern": candle_type,
            "momentum_rsi_14": rsi_state,
            "mean_reversion_bb": bb_state,
            "velocity_roc_10": velocity,
            "trend_base_sma20": sma20_context,
            "range_levels_20": sr_status
        }

    # -------------------------
    # HORYZONT ŚREDNI (50 dni)
    # -------------------------
    def _analyze_medium_term(self, r) -> dict:
        """
        Fokus: Struktura trendu (Z-Score), Dynamika MACD, oraz S/R 50 oparte na ATR.
        Horyzont: ~50 sesji (ok. 2-3 miesiące).
        """
        close = r.get("Close", 0)
        sma20 = r.get("SMA_20")
        sma50 = r.get("SMA_50")
        atr = r.get("ATR_14")

        # Miara zmienności bazowej (jako % ceny)
        atr_pct = (atr / close) if (pd.notna(atr) and close > 0) else 0.02

        # --- 1. STRUKTURA TRENDU (Spread SMA20 vs SMA50) ---
        # Używamy ATR do określenia, czy "rozjazd" średnich jest istotny
        trend_structure = "STRUCTURE_UNCLEAR"
        spread_val = None

        if pd.notna(sma20) and pd.notna(sma50):
            spread_val = (sma20 - sma50) / sma50
            # Próg silnego trendu: spread większy niż 1.5-krotność dziennej zmienności
            strong_trend_threshold = atr_pct * 1.5

            if abs(spread_val) < (atr_pct * 0.5):
                trend_structure = "CONSOLIDATION_COMPRESSED_MAS"
            elif spread_val > strong_trend_threshold:
                trend_structure = "BULLISH_EXPANDING_MOMENTUM"
            elif spread_val < -strong_trend_threshold:
                trend_structure = "BEARISH_EXPANDING_MOMENTUM"
            elif spread_val > 0:
                trend_structure = "BULLISH_GRADUAL_ASCENT"
            else:
                trend_structure = "BEARISH_GRADUAL_DESCENT"

        trend_structure += self._fmt(spread_val, 2, is_pct=True)

        # --- 2. MACD CYCLE (Analiza Pochodnej Histogramu) ---
        macd, signal, hist = r.get("MACD"), r.get("MACD_signal"), r.get("MACD_hist")
        hist_prev = r.get("MACD_hist_prev")
        macd_state = "MACD_UNKNOWN"

        if pd.notna(macd) and pd.notna(signal) and pd.notna(hist):
            # Sprawdzamy kierunek zmian histogramu (pęd)
            is_accelerating = abs(hist) > abs(hist_prev)

            if hist > 0:
                macd_state = "BULLISH_ACCELERATING" if is_accelerating else "BULLISH_FADING"
            else:
                macd_state = "BEARISH_ACCELERATING" if is_accelerating else "BEARISH_RECOVERING"

            # Sygnały przecięcia (Crosses)
            if hist > 0 and hist_prev <= 0:
                macd_state = "BULLISH_ZERO_CROSS_CONFIRMED"
            elif hist < 0 and hist_prev >= 0:
                macd_state = "BEARISH_ZERO_CROSS_CONFIRMED"

        macd_state += self._fmt(hist, 4)

        # --- 3. POZYCJA STATYSTYCZNA (Z-Score vs SMA50) ---
        # To mówi LLM: "Czy ta cena jest nienaturalnie wysoko/nisko?"
        std50 = r.get("Std_50")
        z_score = (close - sma50) / std50 if (pd.notna(std50) and std50 > 0) else None
        pos_vs_50 = "AT_SMA50"

        if z_score is not None:
            if z_score > 2.2:
                pos_vs_50 = "OVEREXTENDED_BULLISH_STAT_OUTLIER"  # Wykupienie > 98% przypadków
            elif z_score < -2.2:
                pos_vs_50 = "OVEREXTENDED_BEARISH_STAT_OUTLIER"  # Wyprzedanie > 98% przypadków
            elif 0.5 > z_score > -0.5:
                pos_vs_50 = "MEAN_REVERSION_HEALTHY_BASE"
            elif z_score > 0:
                pos_vs_50 = "BULLISH_TREND_POSITION"
            else:
                pos_vs_50 = "BEARISH_TREND_POSITION"

        pos_vs_50 += f" (Z:{round(z_score, 2)})" if z_score is not None else ""

        # --- 4. POZIOMY S/R 50 (Strefy Adaptacyjne) ---
        sup50 = r.get("Support_50")
        res50 = r.get("Resistance_50")
        sr_50_status = "INSIDE_MONTHLY_RANGE"

        if pd.notna(sup50) and pd.notna(res50):
            dist_to_sup = (close - sup50) / close
            dist_to_res = (res50 - close) / close

            # Bufor strefy to 0.75 * ATR (dla mid-term szukamy 'obszaru', nie punktu)
            zone_buffer = atr_pct * 0.75

            if abs(dist_to_sup) < zone_buffer:
                sr_50_status = "STRENGTHENING_AT_MONTHLY_SUPPORT_ZONE"
            elif abs(dist_to_res) < zone_buffer:
                sr_50_status = "STRENGTHENING_AT_MONTHLY_RESISTANCE_ZONE"
            elif close > res50:
                sr_50_status = "MONTHLY_BREAKOUT_ABOVE_RANGE"
            elif close < sup50:
                sr_50_status = "MONTHLY_BREAKDOWN_BELOW_RANGE"

        sr_50_status += f" [Zone: {round(sup50, 2)}-{round(res50, 2)}]"

        return {
            "trend_alignment": trend_structure,
            "cycle_macd": macd_state,
            "position_sma50_zscore": pos_vs_50,
            "range_levels_50": sr_50_status
        }

    # -------------------------
    # HORYZONT DŁUGI (200 dni)
    # -------------------------
    def _analyze_long_term(self, r) -> dict:
        """
        Fokus: Reżim rynkowy (SMA200), struktura cyklu (Crosses)
        oraz pozycja w 200-sesyjnym kanale (zamiast sztywnego roku).
        """
        close = r.get("Close", 0)
        sma50, sma200 = r.get("SMA_50"), r.get("SMA_200")
        sup200 = r.get("Support_200")
        res200 = r.get("Resistance_200")

        # 1. Reżim Rynku (Bazujący na Price_vs_SMA_200)
        # To mówi nam, czy w skali roku jesteśmy w trendzie wzrostowym czy spadkowym.
        p_vs_sma200 = r.get("Price_vs_SMA_200")
        regime = "REGIME_UNKNOWN"

        if pd.notna(p_vs_sma200):
            if p_vs_sma200 > 0:
                # Jeśli 50 jest nad 200, to silna hossa (Secular Bull)
                if pd.notna(sma50) and sma50 > sma200:
                    regime = "SECULAR_BULL_MARKET"
                else:
                    regime = "BULL_MARKET_CORRECTION"
            else:
                # Jeśli 50 jest pod 200, to silna bessa (Secular Bear)
                if pd.notna(sma50) and sma50 < sma200:
                    regime = "SECULAR_BEAR_MARKET"
                else:
                    regime = "BEAR_MARKET_RELIEF_RALLY"

        regime += self._fmt(p_vs_sma200, 2, is_pct=True)

        # 2. Golden/Death Cross Gap
        # Mierzy dystans między 50-tką a 200-tką (tzw. "rozstęp trendu").
        cross_signal = "NO_MAJOR_CROSS"
        cross_gap = None
        if pd.notna(sma50) and pd.notna(sma200):
            cross_gap = (sma50 - sma200) / sma200
            if abs(cross_gap) < 0.015:
                cross_signal = "CROSS_IMMINENT_POTENTIAL_PIVOT"
            elif cross_gap > 0.18:
                cross_signal = "EXTREME_BULLISH_STRETCH_EXHAUSTION_RISK"
            elif cross_gap > 0:
                cross_signal = "HEALTHY_GOLDEN_CROSS_STRUCTURE"
            elif cross_gap < -0.18:
                cross_signal = "EXTREME_BEARISH_STRETCH_REBOUND_LIKELY"
            else:
                cross_signal = "DEATH_CROSS_STRUCTURE"

        cross_signal += self._fmt(cross_gap, 2, is_pct=True)

        # 3. Pozycja w Zakresie 200-sesyjnym (Zastępuje Yearly Range)
        # Wykorzystujemy Support_200 i Resistance_200 jako ekstrema trendu.
        range_ctx = "RANGE_UNKNOWN"

        # Zamiast skomplikowanych ifów dla dystansu, dodaj czytelny wskaźnik pozycji:
        if pd.notna(sup200) and pd.notna(res200):
            total_range = res200 - sup200
            if total_range > 0:
                relative_pos = (close - sup200) / total_range

                # Klasyfikacja dystrybucji/akumulacji
                if relative_pos > 0.90:
                    range_ctx = "ATH_OR_TOP_OF_CYCLE"  # Podażowa ściana
                elif relative_pos < 0.10:
                    range_ctx = "MULTI_MONTH_LOW_ACCUMULATION"  # Popytowa strefa
                elif relative_pos > 0.65:
                    range_ctx = "BULLISH_UPPER_QUADRANT"
                elif relative_pos < 0.35:
                    range_ctx = "BEARISH_LOWER_QUADRANT"
                else:
                    range_ctx = "MID_CYCLE_NEUTRAL_ZONE"

                range_ctx += f" [Pos: {round(relative_pos * 100, 1)}%]"

        return {
            "market_regime": regime,
            "major_crosses": cross_signal,
            "long_term_range_pos": range_ctx
        }

    # -------------------------
    # FIZYKA RYNKU
    # -------------------------

    def _volatility_detailed_context(self, r) -> str:
        """
        Łączy zmienność nominalną (% ceny) z relatywną (obecny ATR vs średni ATR).
        """
        atr = r.get("ATR_14")
        close = r.get("Close", 0)
        # Średni ATR z 50 sesji pozwala wykryć 'skoki' zmienności
        avg_atr = r.get("ATR_SMA_50")

        if not atr or not close or close == 0:
            return "VOL_UNKNOWN"

        atr_pct = atr / close
        # rel_vol > 1.0 oznacza, że zmienność rośnie
        rel_vol = (atr / avg_atr) if (avg_atr and avg_atr > 0) else 1.0

        # A. Charakterystyka waloru (Regime)
        if atr_pct > 0.05:
            regime = "HIGH_VOLATILITY_ASSET"  # np. NewConnect / Crypto
        elif atr_pct < 0.015:
            regime = "LOW_VOLATILITY_ASSET"  # np. Blue Chip / Dividend
        else:
            regime = "MODERATE_VOLATILITY"

        # B. Obecna dynamika (Event)
        if rel_vol > 1.8:
            event = "VOLATILITY_EXPLOSION_UNSTABLE"
        elif rel_vol > 1.3:
            event = "EXPANDING_RANGE"
        elif rel_vol < 0.7:
            event = "VOLATILITY_SQUEEZE_COMPRESSION"
        else:
            event = "STABLE_NORMAL_FLUX"

        return f"{event} | {regime} (ATR: {self._fmt(atr_pct, 2, is_pct=True)})"

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

    def _sr_landscape(self, r) -> dict:
        close = r.get("Close", 0)
        atr_pct = (r.get("ATR_14") / close) if (r.get("ATR_14") and close > 0) else 0.02

        # Mapowanie dla skrócenia nazw w raporcie
        short_names = {
            "Short-term (20d)": "20d",
            "Medium-term (50d)": "50d",
            "Institutional (200d)": "200d",
            "Major Cycle (200d)": "200d"
        }

        levels = [
            {"n": "20d", "v": r.get("Support_20"), "t": "sup"},
            {"n": "50d", "v": r.get("Support_50"), "t": "sup"},
            {"n": "200d", "v": r.get("Support_200"), "t": "sup"},
            {"n": "20d", "v": r.get("Resistance_20"), "t": "res"},
            {"n": "50d", "v": r.get("Resistance_50"), "t": "res"},
            {"n": "200d", "v": r.get("Resistance_200"), "t": "res"},
        ]

        valid = [l for l in levels if pd.notna(l["v"])]
        sups = sorted([l for l in valid if l["t"] == "sup" and l["v"] <= close], key=lambda x: x["v"], reverse=True)
        resis = sorted([l for l in valid if l["t"] == "res" and l["v"] > close], key=lambda x: x["v"])

        # 1. Funkcja pomocnicza do zwięzłych opisów
        def get_brief_prox(price, level_val):
            if not level_val: return ""
            d = abs(price - level_val) / price
            if d < (atr_pct * 0.5): return "TESTING"
            if d < atr_pct: return "NEAR"
            return "DISTANT"

        # 2. Logika "Power Zones" - zamiast listy par, po prostu zliczamy zagęszczenie
        valid_vals = sorted([l["v"] for l in valid])
        clusters = 0
        for i in range(len(valid_vals) - 1):
            if abs(valid_vals[i + 1] - valid_vals[i]) / valid_vals[i] < (atr_pct * 0.8):
                clusters += 1

        structure = "CLEAN"
        if clusters > 0:
            structure = f"POWER_ZONE_CONFLUENCE({clusters})"

        gap = (resis[0]["v"] - sups[0]["v"]) / close if (sups and resis) else 1.0
        if gap < (atr_pct * 2.5): structure = "TIGHT_SQUEEZE"

        # 3. Formatowanie wyjścia - maksymalnie konkretnie
        s_top = sups[0] if sups else None
        r_top = resis[0] if resis else None

        floor_info = f"{get_brief_prox(close, s_top['v'])} @{s_top['n']}" if s_top else "NO_FLOOR"
        ceil_info = f"{get_brief_prox(close, r_top['v'])} @{r_top['n']}" if r_top else "BLUE_SKY"

        # Bias
        all_res = [l["v"] for l in valid if l["t"] == "res"]
        all_sup = [l["v"] for l in valid if l["t"] == "sup"]

        bias = "RANGE"
        if all_res and close > max(all_res):
            bias = "UNCONFINED_BULLISH"
        elif all_sup and close < min(all_sup):
            bias = "HEAVY_BEARISH"

        return {
            "barriers": f"F:{floor_info} | C:{ceil_info}",
            "structure": structure,
            "bias": bias
        }

