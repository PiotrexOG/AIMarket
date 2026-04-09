import os
import json
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = r"C:\Users\pwwesolo\PycharmProjects\AIMARKET\AIMarket\backend\data\company_news"

def process_ticker(ticker_path, ticker_name):
    all_data = []

    # przechodzimy po wszystkich plikach json
    for file in os.listdir(ticker_path):
        if file.endswith(".json"):
            file_path = os.path.join(ticker_path, file)

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for item in data:
                        if "datetime" in item:
                            all_data.append(item["datetime"])
                except Exception as e:
                    print(f"Błąd w pliku {file_path}: {e}")

    if not all_data:
        print(f"Brak danych dla {ticker_name}")
        return

    # konwersja do pandas datetime
    df = pd.DataFrame(all_data, columns=["datetime"])
    df["datetime"] = pd.to_datetime(df["datetime"])

    # wyciągamy samą datę (bez godziny)
    df["date"] = df["datetime"].dt.date

    # liczymy ilość newsów per dzień
    daily_counts = df.groupby("date").size()

    # tworzymy pełny zakres dat (żeby zobaczyć "dziury")
    full_range = pd.date_range(start=daily_counts.index.min(),
                               end=daily_counts.index.max())

    daily_counts = daily_counts.reindex(full_range.date, fill_value=0)

    # wykres
    plt.figure(figsize=(12, 6))
    plt.plot(daily_counts.index, daily_counts.values)
    plt.title(f"News count per day - {ticker_name}")
    plt.xlabel("Date")
    plt.ylabel("Number of articles")
    plt.xticks(rotation=45)

    plt.tight_layout()

    # zapis wykresu do pliku
    output_file = f"{ticker_name}_news_plot.png"
    plt.savefig(output_file)
    plt.close()

    print(f"Zapisano wykres: {output_file}")


def main():
    for ticker in os.listdir(BASE_DIR):
        ticker_path = os.path.join(BASE_DIR, ticker)

        if os.path.isdir(ticker_path):
            print(f"Przetwarzanie: {ticker}")
            process_ticker(ticker_path, ticker)


if __name__ == "__main__":
    main()