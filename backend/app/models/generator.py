from app.models.gemini_setup import client, config, MODEL_ID
from app.models.summarizer_utils import clean_model_output


def generate_summary(prompt):
    try:
        # W nowym SDK wysyłamy prompt jako string (contents)
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=config
        )

        if not response.text:
            return []

        raw_text = response.text.strip()
        return clean_model_output(raw_text)

    except Exception as e:
        print("❌ Gemini error:", e)
        return []