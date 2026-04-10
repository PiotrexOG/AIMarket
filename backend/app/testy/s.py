from pathlib import Path

def delete_files(base_path: str):
    base = Path(base_path)

    for file in base.rglob("*"):
        if file.is_file() and file.name.endswith("03_2026.json"):
            print(f"Usuwam: {file}")
            file.unlink()

if __name__ == "__main__":
    delete_files(r"C:\Users\user\Desktop\magisterka\AIMarket\backend\data\company_news_summarized")