from pydantic import BaseModel


class ReportSection(BaseModel):
    heading: str
    content: str


class Citation(BaseModel):
    source: str
    relevance_score: float


class FinalReport(BaseModel):
    title: str
    query: str
    generated_at: str
    sections: list[ReportSection]
    executive_summary: str
    citations: list[Citation]
    sub_questions: list[str]
    evaluation: dict
    metadata: dict