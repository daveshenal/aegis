from app.retrieval.ingestion import ingest_from_s3, ingest_from_local
from app.utils.s3_client import upload_to_s3
import tempfile
import os


def ingest_from_upload(filename: str, file_bytes: bytes) -> dict:
    """
    Handles the full ingestion flow for an uploaded file:
    1. Writes bytes to a temp file
    2. Uploads to S3 for durable storage
    3. Runs LlamaIndex ingestion pipeline against the temp file
    Returns a summary of what was ingested.
    """
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f"_{filename}",
    ) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        s3_key = f"documents/{filename}"
        upload_to_s3(local_path=tmp_path, s3_key=s3_key)

        chunk_count = ingest_from_local(tmp_path)

        return {
            "filename": filename,
            "s3_key": s3_key,
            "chunks_ingested": chunk_count,
            "status": "success",
        }
    finally:
        os.unlink(tmp_path)


def ingest_from_s3_key(s3_key: str) -> dict:
    """
    Triggers ingestion for a document already in S3.
    Useful for bulk re-ingestion or re-indexing workflows.
    """
    chunk_count = ingest_from_s3(s3_key)

    return {
        "s3_key": s3_key,
        "chunks_ingested": chunk_count,
        "status": "success",
    }