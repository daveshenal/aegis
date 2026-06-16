from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings as LlamaSettings
from app.config import settings


def configure_llama_settings() -> None:
    LlamaSettings.embed_model = GeminiEmbedding(
        model_name="models/gemini-embedding-001",
        api_key=settings.GEMINI_API_KEY,
        output_dimensionality=768,
    )
    LlamaSettings.chunk_size = 512
    LlamaSettings.chunk_overlap = 64
