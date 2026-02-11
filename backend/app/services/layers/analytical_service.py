import numpy as np
import pandas as pd

class AnalyticalService:
    """
    Serwis liczący wskaźniki techniczne na żądanie.
    Nie zapisuje niczego do bazy – działa na przekazanym DataFrame.
    """

    def __init__(self):
        pass

    # -------------------------
    # GŁÓWNY INTERFEJS
    # -------------------------

    def resample_to_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agreguje świece godzinowe do dziennych OHLCV.
        ZAWSZE pomija bieżący dzień - używa tylko pełnych, zamkniętych dni.
        Zakłada, że df['Datetime'] jest typu datetime.
        """

        df = df.copy()

        # Dodaj kolumnę z datą (bez czasu)
        df["Date"] = df["Datetime"].dt.date
        df["Date"] = pd.to_datetime(df["Date"])  # normalizacja

        # Znajdź najnowszą datę w danych
        latest_date = df["Date"].max()

        # Filtruj - usuń wszystkie wiersze z najnowszą datą (bieżący dzień)
        df_previous_days = df[df["Date"] < latest_date]

        # Jeśli nie ma danych historycznych, zwróć pusty DataFrame
        if df_previous_days.empty:
            return pd.DataFrame()

        # Agreguj do dziennych OHLCV tylko dla poprzednich dni
        daily = df_previous_days.groupby("Date").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
            "Ticker": "first"
        })

        daily.reset_index(drop=False, inplace=True)
        daily.rename(columns={"Date": "Datetime"}, inplace=True)

        return daily

    def compute_all(self, df: pd.DataFrame, use_daily=True) -> pd.DataFrame:
        """
        Wzbogaca dataframe o komplet wskaźników technicznych.
        """
        df = df.copy()

        # Zapisz najnowszy wiersz przed resamplingiem
        latest_row = df.iloc[-1].copy() if not df.empty else None

        if use_daily:
            df = self.resample_to_daily(df)

        if df.empty:
            return pd.DataFrame()

        # Oblicz wskaźniki na danych dziennych
        df = self.sma(df, 20)
        df = self.sma(df, 50)
        df = self.sma(df, 200)

        df = self.st_dev(df, 50)
        df = self.st_dev(df, 200)

        df = self.support_resistance(df, 20)
        df = self.price_vs_sma(df, 20)

        df = self.support_resistance(df, 50)
        df = self.price_vs_sma(df, 50)

        df = self.support_resistance(df, 200)
        df = self.price_vs_sma(df, 200)

        df = self.volume_ratio(df, 20)



        df = self.rsi(df, 14)
        df = self.macd(df)
        df = self.atr(df, 14, 50)


        df = self.roc(df, 10)

        df = self.bollinger_bands(df, 20, 2)

        # Jeśli mamy najnowszy wiersz, nadpisz OHLCV w ostatnim wierszu wynikowym
        if latest_row is not None:
            # Usuń strefę czasową – dopasuj do dataframe
            latest_row['Datetime'] = pd.to_datetime(latest_row['Datetime']).tz_localize(None)

            df.iloc[-1, df.columns.get_indexer(['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])] = [
                latest_row['Datetime'],
                latest_row['Open'], latest_row['High'], latest_row['Low'],
                latest_row['Close'], latest_row['Volume']
            ]

        return df

    # -------------------------
    # WSKAŹNIKI
    # -------------------------

    def bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        sma = df["Close"].rolling(period).mean()
        std = df["Close"].rolling(period).std()
        df["BB_Upper"] = sma + (std * std_dev)
        df["BB_Lower"] = sma - (std * std_dev)
        # %B - Gdzie jesteśmy w kanale (0 = dolna wstęga, 1 = górna)
        df["BB_Pct_B"] = (df["Close"] - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"])
        return df

    def yearly_high_low(self, df: pd.DataFrame) -> pd.DataFrame:
        # 252 dni handlowe to ok. rok kalendarzowy
        df["Year_High"] = df["High"].rolling(252).max()
        df["Year_Low"] = df["Low"].rolling(252).min()
        return df

    def sma(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        df[f"SMA_{period}"] = df["Close"].rolling(period).mean()
        return df

    def st_dev(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        df[f"Std_{period}"] = df["Close"].rolling(period).std()
        return df

    def ema(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        df[f"EMA_{period}"] = df["Close"].ewm(span=period, adjust=False).mean()
        return df

    def rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss
        df[f"RSI_{period}"] = 100 - (100 / (1 + rs))
        return df

    def macd(self, df: pd.DataFrame) -> pd.DataFrame:
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()

        df["MACD"] = ema12 - ema26
        df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

        df["MACD_hist_prev"] = df["MACD_hist"].shift(1, fill_value=0)

        return df

    def atr(self, df: pd.DataFrame, period_1: int = 14, period_2: int = 50) -> pd.DataFrame:
        # 1. Obliczamy bazowy True Range
        tr1 = df["High"] - df["Low"]
        tr2 = abs(df["High"] - df["Close"].shift(1))
        tr3 = abs(df["Low"] - df["Close"].shift(1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # 2. ATR 14 (standardowa zmienność krótkoterminowa)
        df[f"ATR_{period_1}"] = tr.rolling(window=period_1).mean()

        # 3. ATR_SMA_50 (benchmark zmienności - "normalna" zmienność dla tej spółki)
        # Najpierw liczymy ATR 14, a potem wyciągamy z niego średnią z 50 sesji
        df[f"ATR_SMA_{period_2}"] = df[f"ATR_{period_1}"].rolling(window=period_2).mean()

        return df

    def volume_ratio(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        df[f"Vol_SMA_{period}"] = df["Volume"].rolling(period).mean()
        df[f"Vol_Ratio_{period}"] = df["Volume"] / df[f"Vol_SMA_{period}"]
        return df

    def support_resistance(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        df[f"Support_{period}"] = df["Low"].rolling(period).min()
        df[f"Resistance_{period}"] = df["High"].rolling(period).max()
        return df

    def price_vs_sma(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        sma_col = f"SMA_{period}"
        if sma_col in df:
            df[f"Price_vs_SMA_{period}"] = df["Close"] / df[sma_col] - 1
        return df

    def roc(self, df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
        df[f"ROC_{period}"] = df["Close"].pct_change(periods=period)
        return df
