import time
from app.graph.state import ResearchState
from app.llm.gemini import generate_flash
from app.llm.prompts.critic_prompt import build_critic_prompt
from app.evaluation.judge import parse_eval_result


def report_critic_node(state: ResearchState) -> dict:
    query = state["query"]
    sub_questions = state["sub_questions"]
    draft_report = state["draft_report"]
    revision_count = state["revision_count"]

    prompt = build_critic_prompt(
        query=query,
        sub_questions=sub_questions,
        draft_report=draft_report,
    )

    start = time.time()
    response = generate_flash(prompt)
    latency = round(time.time() - start, 3)

    eval_result = parse_eval_result(response.text)

    return {
        "eval_result": eval_result,
        "report_metadata": {
            **state.get("report_metadata", {}),
            f"critic_latency_s_pass_{revision_count}": latency,
            f"critic_score_pass_{revision_count}": eval_result["overall_score"],
            f"critic_passed_pass_{revision_count}": eval_result["passed"],
            f"critic_input_tokens_pass_{revision_count}": len(prompt) // 4,
            f"critic_output_tokens_pass_{revision_count}": len(response.text) // 4,
        },
    }