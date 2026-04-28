from app.models.gemini_setup import client, config, MODEL_ID
from app.models.summarizer_utils import clean_model_output


import time
import random

def generate_summary(prompt):
    MAX_RETRIES = 5

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=config
            )

            if not response.text:
                raise ValueError("Empty response from model")

            raw_text = response.text.strip()
            return clean_model_output(raw_text)

        except Exception as e:
            print(f"❌ Gemini attempt {attempt+1} failed: {e}")

            # ostatnia próba → fallback
            if attempt == MAX_RETRIES - 1:
                return []  # 🔴 zawsze spójny typ

            # exponential backoff + jitter
            sleep_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(sleep_time)
            continue
    return None