from pydantic import BaseModel


class DimensionScoreSchema(BaseModel):
    dimension: str
    score: float
    feedback: str


class EvalResultSchema(BaseModel):
    scores: list[DimensionScoreSchema]
    overall_score: float
    passed: bool
    summary_feedback: str