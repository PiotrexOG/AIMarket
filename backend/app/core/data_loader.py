import csv
import yfinance as yf
import pandas as pd
import pytz

def load_market_data(ticker):
    """Wczytuje dane giełdowe z pliku CSV"""
    with open(f"{ticker}.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

def save_results(file_path, results):
    """Zapisuje wyniki symulacji do pliku CSV"""
    with open(file_path, mode='w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['Datetime', 'Close', 'Decision', 'Cash', 'Shares', 'Explanation'])
        for row in results:
            writer.writerow(row)


def fetch_data(start_date, end_date, ticker_name, interv):
    ticker = yf.Ticker(ticker_name)
    df = ticker.history(start=start_date, end=end_date, interval=interv)
    df.reset_index(inplace=True)

    df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]

    # Sprawdź, czy czas już ma strefę czasową
    if df['Datetime'].dt.tz is None:
        # Jeśli nie ma strefy czasowej, ustaw jako UTC i przekonwertuj na Nowy Jork
        df['Datetime'] = pd.to_datetime(df['Datetime']).dt.tz_localize('UTC').dt.tz_convert('America/New_York')
    else:
        # Jeśli już ma strefę czasową, po prostu przekonwertuj
        df['Datetime'] = df['Datetime'].dt.tz_convert('America/New_York')

    df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].round(2)
    df.to_csv(f"{ticker_name}.csv", index=False)
    print(f"📁 Dane zapisane do {ticker_name}.csv")