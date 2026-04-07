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
    news_list = news_list[:20]

    context = ""

    for idx, n in enumerate(news_list):
        headline = normalize_text(n["headline"])
        summary = normalize_text(n.get("summary", ""))

        context += f"{idx} | {headline} | {summary}\n"

    return f"""
Role: Financial Event Extractor.

Task:
Identify MATERIAL events directly affecting company ticker {ticker} on {date}.

IMPORTANT:
Events must have a DIRECT impact on the company itself.

ACCEPTABLE EVENTS:
- Regulatory rulings targeting the company
- M&A involving the company
- Partnerships involving the company
- Production or supply chain changes
- Company guidance
- Product launches or delays
- Major lawsuits involving the company
- Major strategic decisions

IGNORE COMPLETELY:
- Analyst opinions
- Investment advice
- Market commentary
- Rankings or "top stocks"
- News primarily about other companies
- Industry news where the company is only mentioned as a peer

CRITICAL RULE:
If the event does NOT clearly and directly affect {ticker},
IGNORE IT.

Prefer returning NONE rather than weakly related news.

FORMAT RULES:
- Maximum 10 words per bullet
- Each bullet must start with "- "
- Bullet points only
- No commentary
- No explanations
- No IDs

If no material event exists return exactly:
NONE

EXAMPLE STYLE:
{example_style}

DATA:
{context}

OUTPUT:
"""