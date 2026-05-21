import time
from app.graph.state import ResearchState, RetrievedChunk
from app.retrieval.query import query_pipeline


def retriever_node(state: ResearchState) -> dict:
    sub_questions = state["sub_questions"]

    all_chunks: list[RetrievedChunk] = []
    start = time.time()

    for sub_question in sub_questions:
        chunks = query_pipeline(
            question=sub_question["question"],
            sub_question_id=sub_question["id"],
            top_k=5,
        )
        all_chunks.extend(chunks)

    latency = round(time.time() - start, 3)

    return {
        "retrieved_chunks": all_chunks,
        "report_metadata": {
            **state.get("report_metadata", {}),
            "retriever_latency_s": latency,
            "total_chunks_retrieved": len(all_chunks),
            "chunks_per_sub_question": len(all_chunks) // max(len(sub_questions), 1),
        },
    }