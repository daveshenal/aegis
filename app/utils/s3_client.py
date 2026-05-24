import boto3
from app.config import settings

_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
    return _s3_client


def upload_to_s3(local_path: str, s3_key: str) -> str:
    client = _get_client()
    client.upload_file(local_path, settings.S3_BUCKET_NAME, s3_key)
    return f"s3://{settings.S3_BUCKET_NAME}/{s3_key}"


def download_from_s3(s3_key: str, local_path: str) -> None:
    client = _get_client()
    client.download_file(settings.S3_BUCKET_NAME, s3_key, local_path)