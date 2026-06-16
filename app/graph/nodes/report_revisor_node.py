import time
from app.graph.state import ResearchState
from app.llm.gemini import generate_flash
from app.llm.prompts.revisor_prompt import build_revisor_prompt


def report_revisor_node(state: ResearchState) -> dict:
    draft_report = state["draft_report"]
    eval_result = state["eval_result"]
    query = state["query"]
    revision_count = state["revision_count"]

    # Identify only the dimensions that failed
    failed_dimensions = [
        dim for dim in eval_result["scores"]
        if dim["score"] < 3.5
    ]

    prompt = build_revisor_prompt(
        query=query,
        draft_report=draft_report,
        failed_dimensions=failed_dimensions,
        summary_feedback=eval_result["summary_feedback"],
    )

    start = time.time()
    response = generate_flash(prompt)
    latency = round(time.time() - start, 3)

    return {
        "draft_report": response,
        "report_metadata": {
            **state.get("report_metadata", {}),
            f"revisor_latency_s_pass_{revision_count}": latency,
            f"revisor_input_tokens_pass_{revision_count}": len(prompt) // 4,
            f"revisor_output_tokens_pass_{revision_count}": len(response) // 4,
        },
    }