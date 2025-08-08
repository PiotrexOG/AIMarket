import sqlite3
import pandas as pd
import yfinance as yf

def fetch_data_to_sqlite(start_date, end_date, ticker_name, interv, db_path="market_data.db"):
    import sqlite3
    import yfinance as yf
    import pandas as pd

    ticker = yf.Ticker(ticker_name)
    df = ticker.history(
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        interval=interv
    )

    if df.empty:
        print(f"⚠️ Brak danych dla {ticker_name} w zakresie {start_date} ➜ {end_date}")
        return  # 🚨 Zatrzymaj funkcję, nie ma danych do zapisania

    df.reset_index(inplace=True)
    df['Ticker'] = ticker_name

    df = df[['Datetime', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df['Datetime'] = pd.to_datetime(df['Datetime']).dt.tz_convert('America/New_York')
    df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].round(2)

    with sqlite3.connect(db_path) as conn:
        df.to_sql("market_data", conn, if_exists='append', index=False)

    print(f"✅ Dane dla {ticker_name} zapisane do bazy {db_path}")
