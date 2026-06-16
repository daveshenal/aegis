import time
from app.graph.state import ResearchState, RetrievedChunk
from app.llm.gemini import generate_pro
from app.llm.prompts.writer_prompt import build_writer_prompt


def report_writer_node(state: ResearchState) -> dict:
    query = state["query"]
    sub_questions = state["sub_questions"]
    retrieved_chunks = state["retrieved_chunks"]
    revision_count = state.get("revision_count", 0)

    # On revision passes, include critic feedback in the prompt
    critic_feedback = None
    if revision_count > 0:
        eval_result = state.get("eval_result")
        if eval_result:
            critic_feedback = eval_result["summary_feedback"]

    prompt = build_writer_prompt(
        query=query,
        sub_questions=sub_questions,
        retrieved_chunks=retrieved_chunks,
        critic_feedback=critic_feedback,
    )

    start = time.time()
    response = generate_pro(prompt)
    latency = round(time.time() - start, 3)

    return {
        "draft_report": response.text,
        "revision_count": revision_count + 1,
        "report_metadata": {
            **state.get("report_metadata", {}),
            f"writer_latency_s_pass_{revision_count + 1}": latency,
            f"writer_input_tokens_pass_{revision_count + 1}": len(prompt) // 4,
            f"writer_output_tokens_pass_{revision_count + 1}": len(response.text) // 4,
        },
    }


def _group_chunks_by_sub_question(
    sub_questions: list,
    chunks: list[RetrievedChunk],
) -> dict[str, list[RetrievedChunk]]:
    grouped = {sq["id"]: [] for sq in sub_questions}
    for chunk in chunks:
        sq_id = chunk["sub_question_id"]
        if sq_id in grouped:
            grouped[sq_id].append(chunk)
    return grouped