from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str

    # AWS
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str

    # LangSmith
    LANGCHAIN_API_KEY: str
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_PROJECT: str = "aegis"

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    # Graph
    MAX_REVISIONS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()