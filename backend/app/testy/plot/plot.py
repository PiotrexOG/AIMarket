import os
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE_DIR = Path(__file__).resolve().parents[3] / "data" / "company_news"

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

    plt.figure(figsize=(12, 6))
    plt.plot(daily_counts.index, daily_counts.values)

    plt.title(f"News count per day - {ticker_name}")
    plt.xlabel("Date")
    plt.ylabel("Number of articles")

    # ustawienie każdej daty na osi X
    ax = plt.gca()
    interval = max(1, len(daily_counts) // 20)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    plt.xticks(rotation=45)

    zero_days_sequences = []
    current_sequence = []

    for date, val in daily_counts.items():
        if val == 0:
            current_sequence.append(str(date))
        else:
            if len(current_sequence) >= 5:
                zero_days_sequences.append(current_sequence)
            current_sequence = []

    # sprawdzenie ostatniej sekwencji (jeśli kończy się zerami)
    if len(current_sequence) >= 5:
        zero_days_sequences.append(current_sequence)

    plt.tight_layout()

    plt.tight_layout()

    # zapis wykresu do pliku
    output_file = f"{ticker_name}_news_plot.png"
    plt.savefig(output_file)
    plt.close()

    print(f"{ticker_name} - dni bez newsów:")
    for d in zero_days_sequences:
        print(d)

    print(f"Zapisano wykres: {output_file}")


def main():
    for ticker in os.listdir(BASE_DIR):
        ticker_path = os.path.join(BASE_DIR, ticker)

        if os.path.isdir(ticker_path):
            print(f"Przetwarzanie: {ticker}")
            process_ticker(ticker_path, ticker)


if __name__ == "__main__":
    main()