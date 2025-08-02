import csv
import yfinance as yf
import pandas as pd

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
    #df['Datetime'] = df['Datetime'].dt.strftime("%Y-%m-%d %H:%M:%S")
    df['Datetime'] = pd.to_datetime(df['Datetime']).dt.tz_localize(None)
    df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].round(2)

    df.to_csv(f"{ticker_name}.csv", index=False)
    print(f"📁 Dane zapisane do {ticker_name}.csv")