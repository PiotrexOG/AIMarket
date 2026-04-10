from pathlib import Path

def delete_files(base_path: str):
    base = Path(base_path)

    for file in base.rglob("*"):
        if file.is_file() and file.name.endswith("03_2026.json"):
            print(f"Usuwam: {file}")
            file.unlink()

        if file.is_file() and file.name.endswith("04_2026.json"):
            print(f"Usuwam: {file}")
            file.unlink()

if __name__ == "__main__":
    delete_files(r"C:\Users\pwwesolo\PycharmProjects\AIMARKET\AIMarket\backend\data\news\company_news_scored")