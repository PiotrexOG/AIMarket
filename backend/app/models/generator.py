from app.models.gemini_setup import model
from app.models.summarizer_utils import clean_model_output


def generate_summary(prompt):

    try:
        response = model.generate_content(
            [
                {"role": "user", "parts": [prompt]}
            ]
        )

        raw_text = response.text.strip()

    except Exception as e:
        print("Gemini error:", e)
        return []

    return clean_model_output(raw_text)