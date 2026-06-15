import boto3
import tempfile
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import Settings as LlamaSettings
from app.retrieval.pinecone_client import get_pinecone_index
from app.retrieval.llama_config import configure_llama_settings
from app.config import settings


def ingest_from_s3(s3_key: str) -> int:
    """
    Downloads a document from S3, chunks it, embeds it,
    and upserts into Pinecone. Returns number of chunks ingested.
    """
    configure_llama_settings()

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, os.path.basename(s3_key))
        s3.download_file(settings.S3_BUCKET_NAME, s3_key, local_path)

        documents = SimpleDirectoryReader(tmpdir).load_data()

        # Attach source metadata to every document
        for doc in documents:
            doc.metadata["source"] = s3_key

        splitter = SentenceSplitter(
            chunk_size=LlamaSettings.chunk_size,
            chunk_overlap=LlamaSettings.chunk_overlap,
        )
        nodes = splitter.get_nodes_from_documents(documents)

        pinecone_index = get_pinecone_index()
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            show_progress=True,
        )

    return len(nodes)


def ingest_from_local(file_path: str) -> int:
    """
    Ingests a local file directly — used by scripts/ingest_sample_docs.py
    and docker-compose local dev workflow.
    """
    configure_llama_settings()

    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()

    for doc in documents:
        doc.metadata["source"] = os.path.basename(file_path)

    splitter = SentenceSplitter(
        chunk_size=LlamaSettings.chunk_size,
        chunk_overlap=LlamaSettings.chunk_overlap,
    )
    nodes = splitter.get_nodes_from_documents(documents)

    pinecone_index = get_pinecone_index()
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        show_progress=True,
    )

    return len(nodes)