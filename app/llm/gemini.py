import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

# Generation config shared across both models
_generation_config = genai.GenerationConfig(
    temperature=0.3,
    max_output_tokens=4096,
)

# Flash — used for planner, critic, revisor (fast, cheap)
gemini_flash = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=_generation_config,
)

# Pro — used for writer (higher quality, more expensive)
gemini_pro = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    generation_config=_generation_config,
)