from app.models.examples import EXAMPLE_STYLES
from app.models.summarizer_utils import normalize_text, filter_noise_news


def get_example_style(ticker):
    examples = EXAMPLE_STYLES.get(ticker, [])

    if not examples:
        return ""

    return "\n".join(f"- {e}" for e in examples)


def build_summary_prompt(ticker, date, news_list):

    example_style = get_example_style(ticker)
    news_list = filter_noise_news(news_list)

    context = ""

    for idx, n in enumerate(news_list):
        headline = normalize_text(n["headline"])
        summary = normalize_text(n.get("summary", ""))

        context += f"{idx} | {headline} | {summary}\n"

    return f"""
TARGET COMPANY: {ticker}
DATE: {date}

EXAMPLE STYLE:
{example_style}

DATA:
{context}

OUTPUT:
"""