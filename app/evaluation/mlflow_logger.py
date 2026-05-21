import mlflow
from app.graph.state import ResearchState
from app.evaluation.metrics import (
    citation_coverage_score,
    section_coverage_score,
    avg_chunk_score,
    revision_efficiency_score,
)
from app.config import settings


def log_run_to_mlflow(state: ResearchState, prompt_versions: dict) -> None:
    """
    Logs a completed research graph run to MLflow.
    Call this from research_service.py after the graph finishes.

    prompt_versions: dict mapping prompt name to version string
    e.g. {"planner": "v1.2", "writer": "v2.0", "critic": "v1.0"}
    """
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment("agentic-research-system")

    with mlflow.start_run():
        eval_result = state.get("eval_result", {})
        metadata = state.get("report_metadata", {})
        chunks = state.get("retrieved_chunks", [])
        sub_questions = state.get("sub_questions", [])
        final_report = state.get("final_report", "")
        revision_count = state.get("revision_count", 0)

        # ── Prompt versions ────────────────────────────────────────
        for name, version in prompt_versions.items():
            mlflow.log_param(f"prompt_{name}_version", version)

        # ── Graph config ───────────────────────────────────────────
        mlflow.log_param("max_revisions", state.get("max_revisions"))
        mlflow.log_param("query", state.get("query", "")[:250])

        # ── LLM-as-judge scores ────────────────────────────────────
        for dim_score in eval_result.get("scores", []):
            mlflow.log_metric(
                f"judge_{dim_score['dimension'].lower()}_score",
                dim_score["score"],
            )
        mlflow.log_metric("judge_overall_score", eval_result.get("overall_score", 0.0))
        mlflow.log_metric("judge_passed", int(eval_result.get("passed", False)))

        # ── Custom structural metrics ──────────────────────────────
        mlflow.log_metric(
            "citation_coverage",
            citation_coverage_score(final_report, chunks),
        )
        mlflow.log_metric(
            "section_coverage",
            section_coverage_score(final_report, sub_questions),
        )
        mlflow.log_metric(
            "avg_chunk_similarity",
            avg_chunk_score(chunks),
        )
        mlflow.log_metric(
            "revision_efficiency",
            revision_efficiency_score(revision_count, state.get("max_revisions", 3)),
        )

        # ── Cost and latency ───────────────────────────────────────
        mlflow.log_metric("revision_count", revision_count)
        mlflow.log_metric(
            "total_chunks_retrieved",
            metadata.get("total_chunks_retrieved", 0),
        )

        for key, value in metadata.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)

        # ── Artifacts ─────────────────────────────────────────────
        if final_report:
            mlflow.log_text(final_report, "final_report.md")