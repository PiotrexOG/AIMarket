from datetime import datetime, timedelta, timezone

import pytz
import yfinance as yf
import pandas as pd

class YahooClient:
    def __init__(self):
        self.timezone = timezone.utc

    def fetch_history(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
        interval: str
    ) -> pd.DataFrame:
        """
        Pobiera dane historyczne z Yahoo Finance dla danego tickera.
        """
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(
            start=start.strftime("%Y-%m-%d"),
            end=(end + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval=interval
        )

        if df.empty:
            return pd.DataFrame()  # brak danych

        # Reset index i dodanie kolumny Ticker
        df.reset_index(inplace=True)
        df['Ticker'] = ticker

        # Wybór kolumn i formatowanie
        df = df[['Datetime', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df['Datetime'] = pd.to_datetime(df['Datetime']).dt.tz_convert("UTC")
        df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].round(2)

        return df

    def fetch_valuation_snapshot(self, ticker: str) -> dict:
        t = yf.Ticker(ticker)
        info = t.info

        return {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
        }

    def fetch_fundamental_snapshot(self, ticker: str) -> dict:
        t = yf.Ticker(ticker)
        info = t.info

        return {
            "revenue_ttm": info.get("totalRevenue"),
            "revenue_growth": info.get("revenueGrowth"),
            "eps_ttm": info.get("trailingEps"),
            "eps_growth": info.get("earningsGrowth"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "net_margin": info.get("profitMargins"),
            "free_cash_flow": info.get("freeCashflow"),
        }

    def fetch_earnings_calendar(self, ticker: str) -> list[dict]:
        """
        Pobiera daty earnings + EPS estimate (jeśli dostępne).
        """
        t = yf.Ticker(ticker)
        results = []

        try:
            df = t.earnings_dates
            if df is None or df.empty:
                return results

            df = df.reset_index()

            for _, row in df.iterrows():
                earnings_date = row["Earnings Date"]

                eps_estimate = None
                if "EPS Estimate" in row and pd.notna(row["EPS Estimate"]):
                    eps_estimate = float(row["EPS Estimate"])

                results.append({
                    "earnings_date": earnings_date,
                    "eps_estimate": eps_estimate
                })

        except Exception:
            pass

        return results

    def fetch_analyst_snapshot(self, ticker: str) -> dict:
        info = yf.Ticker(ticker).info

        return {
            "recommendation_key": info.get("recommendationKey"),
            "recommendation_mean": info.get("recommendationMean"),
            "analyst_count": info.get("numberOfAnalystOpinions"),
            "target_mean": info.get("targetMeanPrice"),
            "target_low": info.get("targetLowPrice"),
            "target_high": info.get("targetHighPrice"),
        }





