from llama_index.core import Settings as LlamaSettings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from google.genai.types import EmbedContentConfig
from app.config import settings


def configure_llama_settings() -> None:
    LlamaSettings.embed_model = GoogleGenAIEmbedding(
        model_name="models/gemini-embedding-001",
        api_key=settings.GEMINI_API_KEY,
        embedding_config=EmbedContentConfig(
            output_dimensionality=768
        )
    )

    LlamaSettings.chunk_size = 512
    LlamaSettings.chunk_overlap = 64