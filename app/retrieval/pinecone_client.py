from pinecone import Pinecone
from app.config import settings

# Module-level singleton — initialised once per process
_pinecone_client: Pinecone | None = None
_pinecone_index = None


def _get_client() -> Pinecone:
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
    return _pinecone_client


def get_pinecone_index():
    global _pinecone_index
    if _pinecone_index is None:
        client = _get_client()
        _pinecone_index = client.Index(settings.PINECONE_INDEX_NAME)
    return _pinecone_index