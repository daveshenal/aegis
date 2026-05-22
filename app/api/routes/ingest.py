from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.schemas.api import IngestResponse
from app.services.ingestion_service import ingest_from_upload, ingest_from_s3_key

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/upload", response_model=IngestResponse)
async def ingest_upload(file: UploadFile = File(...)) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    allowed_extensions = {".pdf", ".txt", ".md", ".docx"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed_extensions}",
        )

    file_bytes = await file.read()
    result = ingest_from_upload(
        filename=file.filename,
        file_bytes=file_bytes,
    )
    return IngestResponse(**result)


@router.post("/s3", response_model=IngestResponse)
def ingest_s3(s3_key: str = Form(...)) -> IngestResponse:
    if not s3_key.strip():
        raise HTTPException(status_code=400, detail="s3_key must not be empty.")

    result = ingest_from_s3_key(s3_key=s3_key)
    return IngestResponse(**result)