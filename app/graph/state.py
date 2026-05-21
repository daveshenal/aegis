from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class SubQuestion(TypedDict):
    id: str
    question: str


class RetrievedChunk(TypedDict):
    sub_question_id: str
    text: str
    source: str
    score: float


class DimensionScore(TypedDict):
    dimension: str
    score: float
    feedback: str


class EvalResult(TypedDict):
    scores: list[DimensionScore]
    overall_score: float
    passed: bool
    summary_feedback: str


class ResearchState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────
    query: str                          # Original user query, never mutated

    # ── Planner output ─────────────────────────────────────────────
    sub_questions: list[SubQuestion]    # Decomposed sub-questions from planner

    # ── Retriever output ───────────────────────────────────────────
    retrieved_chunks: list[RetrievedChunk]  # All chunks across all sub-questions

    # ── Writer output ──────────────────────────────────────────────
    draft_report: str                   # Current draft — overwritten on each revision

    # ── Critic output ──────────────────────────────────────────────
    eval_result: EvalResult             # Latest critic evaluation

    # ── Revision tracking ──────────────────────────────────────────
    revision_count: int                 # How many revision loops have happened
    max_revisions: int                  # Hard cap — set at graph entry, never changes

    # ── Final output ───────────────────────────────────────────────
    final_report: str                   # Set only when critic passes
    report_metadata: dict[str, Any]     # Token counts, latency, prompt versions, etc.