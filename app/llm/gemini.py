from google import genai
from google.genai import types

from app.config import settings


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


_generation_config = types.GenerateContentConfig(
    temperature=0.3,
    max_output_tokens=4096,
)


def generate_flash(prompt: str):
    response = client.models.generate_content(
        model=settings.GEMINI_FLASH_MODEL,
        contents=prompt,
        config=_generation_config,
    )

    return response


def generate_pro(prompt: str):
    response = client.models.generate_content(
        model=settings.GEMINI_PRO_MODEL,
        contents=prompt,
        config=_generation_config,
    )

    return response