import re
from collections import defaultdict


def normalize_text(text):
    text = text.replace("&#39;", "'").replace("&quot;", '"')
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def filter_noise_news(news_list):
    noise_keywords = [
        "analyst",
        "price target",
        "jim cramer",
        "top stock",
        "best stocks",
        "stock to buy",
        "market commentary",
        "wall street says",
        "investor favorite"
    ]

    filtered = []

    for n in news_list:
        headline = n["headline"].lower()
        summary = n.get("summary", "").lower()

        text = headline + " " + summary

        if any(k in text for k in noise_keywords):
            continue

        filtered.append(n)

    return filtered


def group_news_by_date(news_items):
    grouped = defaultdict(list)

    for item in news_items:
        date_str = item["datetime"].split("T")[0]
        grouped[date_str].append(item)

    return grouped


def clean_model_output(decoded):

    decoded = normalize_text(decoded)

    if decoded.upper().startswith("NONE"):
        return []

    bullets = []

    for line in decoded.split("\n"):
        line = line.strip()

        if not line:
            continue

        line = re.sub(r"^\-\s*", "", line)
        line = re.sub(r"ID:\d+", "", line)

        if len(line) < 8:
            continue

        if "no material" in line.lower():
            continue

        if "therefore" in line.lower():
            continue

        bullets.append(line.strip())

    return bullets[:3]