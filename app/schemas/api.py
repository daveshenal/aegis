from pydantic import BaseModel, Field
from app.schemas.evaluation import DimensionScoreSchema


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=1000)


class ResearchResponse(BaseModel):
    query: str
    final_report: str
    passed_evaluation: bool
    overall_score: float
    dimension_scores: list[DimensionScoreSchema]
    revision_count: int
    sub_questions: list[str]
    sources_used: list[str]
    metadata: dict


class IngestRequest(BaseModel):
    s3_key: str = Field(..., min_length=1)


class IngestResponse(BaseModel):
    filename: str | None = None
    s3_key: str
    chunks_ingested: int
    status: str