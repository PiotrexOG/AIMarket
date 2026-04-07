import os
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

API_KEY = os.environ.get("API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    generation_config=GenerationConfig(
        temperature=0.1,
        top_p=0.9,
        top_k=20,
        max_output_tokens=150
    )
)