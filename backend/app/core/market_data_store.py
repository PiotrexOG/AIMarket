import sqlite3
import pandas as pd
from app.core.data_loader import fetch_data_to_sqlite

class MarketDataStore:
    def __init__(self, tickers, start_date, end_date, db_path="market_data.db"):
        self.tickers = tickers
        self.db_path = db_path
        self._ensure_data(tickers, start_date, end_date)

    def _ensure_data(self, tickers, start_date, end_date):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 🛡️ Tworzymy tabelę tylko jeśli nie istnieje
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    Datetime TEXT,
                    Ticker TEXT,
                    Open REAL,
                    High REAL,
                    Low REAL,
                    Close REAL,
                    Volume REAL
                )
            """)
            conn.commit()

        for ticker in tickers:
            with sqlite3.connect(self.db_path) as conn:
                try:
                    result = pd.read_sql_query(
                        "SELECT COUNT(*) FROM market_data WHERE Ticker = ?",
                        conn,
                        params=(ticker,)
                    )
                except Exception as e:
                    print(f"❌ Błąd SQL dla {ticker}: {e}")
                    return

                if result.iloc[0, 0] == 0:
                    print(f"⬇️ Brak danych dla {ticker}, pobieram...")
                    fetch_data_to_sqlite(start_date, end_date, ticker, "1h", db_path=self.db_path)


    def get_data_for_day(self, date_time):
        result = {}
        with sqlite3.connect(self.db_path) as conn:
            for ticker in self.tickers:
                df = pd.read_sql_query(
                    """
                    SELECT * FROM market_data
                    WHERE Ticker = ?
                    AND Datetime <= ?
                    ORDER BY Datetime DESC
                    LIMIT 1
                    """,
                    conn,
                    params=(ticker, date_time.isoformat())
                )
                if not df.empty:
                    result[ticker] = df.iloc[0].to_dict()
        return result

    def get_price(self, ticker, date_time):
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(
                """
                SELECT Close FROM market_data
                WHERE Ticker = ?
                AND Datetime <= ?
                ORDER BY Datetime DESC
                LIMIT 1
                """,
                conn,
                params=(ticker, date_time.isoformat())
            )
            return float(df.iloc[0]['Close']) if not df.empty else None
