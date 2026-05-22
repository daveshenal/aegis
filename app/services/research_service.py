import time
from app.graph.graph import research_graph
from app.graph.state import ResearchState
from app.evaluation.mlflow_logger import log_run_to_mlflow
from app.observability.langsmith import get_langsmith_config
from app.config import settings

# Prompt versions — bump these manually when you change a prompt
# MLflow will track which version produced which scores
PROMPT_VERSIONS = {
    "planner": "v1.0",
    "writer":  "v1.0",
    "critic":  "v1.0",
    "revisor": "v1.0",
}


def run_research(query: str) -> dict:
    """
    Entry point for the research pipeline.
    Initialises state, runs the LangGraph graph,
    logs results to MLflow, and returns a structured response.
    """

    initial_state: ResearchState = {
        "query": query,
        "sub_questions": [],
        "retrieved_chunks": [],
        "draft_report": "",
        "eval_result": {
            "scores": [],
            "overall_score": 0.0,
            "passed": False,
            "summary_feedback": "",
        },
        "revision_count": 0,
        "max_revisions": settings.MAX_REVISIONS,
        "final_report": "",
        "report_metadata": {
            "prompt_versions": PROMPT_VERSIONS,
        },
    }

    # LangSmith tracing config — passed as run config to the graph
    langsmith_config = get_langsmith_config(run_name=f"research: {query[:60]}")

    wall_start = time.time()

    final_state: ResearchState = research_graph.invoke(
        initial_state,
        config=langsmith_config,
    )

    wall_latency = round(time.time() - wall_start, 3)

    final_state["report_metadata"]["wall_latency_s"] = wall_latency

    # Log completed run to MLflow
    try:
        log_run_to_mlflow(final_state, PROMPT_VERSIONS)
    except Exception as e:
        # MLflow logging failure must never break the API response
        print(f"[MLflow] Logging failed: {e}")

    return _format_response(final_state)


def _format_response(state: ResearchState) -> dict:
    eval_result = state.get("eval_result", {})
    metadata = state.get("report_metadata", {})

    return {
        "query": state["query"],
        "final_report": state.get("final_report", ""),
        "passed_evaluation": eval_result.get("passed", False),
        "overall_score": eval_result.get("overall_score", 0.0),
        "dimension_scores": eval_result.get("scores", []),
        "revision_count": state.get("revision_count", 0),
        "sub_questions": [sq["question"] for sq in state.get("sub_questions", [])],
        "sources_used": list({
            chunk["source"]
            for chunk in state.get("retrieved_chunks", [])
        }),
        "metadata": {
            "wall_latency_s": metadata.get("wall_latency_s"),
            "total_chunks_retrieved": metadata.get("total_chunks_retrieved"),
            "prompt_versions": metadata.get("prompt_versions"),
        },
    }