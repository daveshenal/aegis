import time
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import StorageContext
from app.retrieval.pinecone_client import get_pinecone_index
from app.graph.state import RetrievedChunk


def _build_retriever(top_k: int) -> VectorIndexRetriever:
    pinecone_index = get_pinecone_index()

    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k,
    )

    return retriever


def query_pipeline(
    question: str,
    sub_question_id: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    retriever = _build_retriever(top_k)

    # Postprocessor filters out low-quality chunks below similarity threshold
    postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)

    nodes = retriever.retrieve(question)
    nodes = postprocessor.postprocess_nodes(nodes)

    chunks: list[RetrievedChunk] = []
    for node in nodes:
        chunks.append(RetrievedChunk(
            sub_question_id=sub_question_id,
            text=node.get_content(),
            source=node.metadata.get("source", "unknown"),
            score=round(node.score or 0.0, 4),
        ))

    return chunks