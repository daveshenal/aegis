from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings as LlamaSettings
from app.config import settings


def configure_llama_settings() -> None:
    LlamaSettings.embed_model = GeminiEmbedding(
        model_name="models/text-embedding-004",
        api_key=settings.GEMINI_API_KEY,
    )
    LlamaSettings.chunk_size = 512
    LlamaSettings.chunk_overlap = 64
