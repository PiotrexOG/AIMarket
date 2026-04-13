import os
from google import genai
from google.genai import types

API_KEY = os.environ.get("API_KEY")

# Inicjalizacja klienta
client = genai.Client(api_key=API_KEY)

# Nazwa modelu
MODEL_ID = "gemini-2.5-flash-lite"

# Konfiguracja - tutaj ląduje Twoja instrukcja systemowa (Role, Task, Rules)
# Dzięki temu model zawsze "pamięta" o roli, a Ty przesyłasz tylko dane
config = types.GenerateContentConfig(
    temperature=0.1,
    top_p=0.9,
    top_k=20,
    max_output_tokens=150,
    system_instruction="""
    Role: Financial Event Extractor.

    Task:
    Identify MATERIAL events directly affecting the target company provided in the data.

    IMPORTANT:
    Events must have a DIRECT impact on the company itself.

    ACCEPTABLE EVENTS:
    - Regulatory rulings, M&A, Partnerships, Supply chain changes.
    - Company guidance, Product launches/delays, Lawsuits, Strategic decisions.

    IGNORE COMPLETELY:
    - Analyst opinions, Investment advice, Market commentary.
    - News primarily about other companies or general industry trends.

    CRITICAL RULE:
    If the event does NOT clearly and directly affect the target company, IGNORE IT.
    Prefer returning NONE rather than weakly related news.

    FORMAT RULES:
    - Maximum 10 words per bullet.
    - Each bullet must start with "- ".
    - Bullet points only, no commentary, no explanations, no IDs.
    - If no material event exists return exactly: NONE
    """
)