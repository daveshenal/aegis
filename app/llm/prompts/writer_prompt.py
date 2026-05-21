from app.graph.state import SubQuestion, RetrievedChunk


WRITER_SYSTEM_PROMPT = """You are an expert research analyst. Your job is to synthesise retrieved source material into a structured, well-reasoned research report.

Rules:
- Write in clear, professional prose. No bullet points in the main body.
- Structure the report with a titled section for each sub-question.
- Every factual claim must be grounded in the provided source chunks.
- Cite sources inline using the format [Source: <source_name>].
- Do not introduce information not present in the retrieved chunks.
- If retrieved chunks are insufficient to answer a sub-question, explicitly state this in that section.
- End with a concise executive summary (3-5 sentences) that directly answers the original query.
- Do not include a preamble. Start directly with the first section heading."""


REVISION_INSTRUCTION = """
You are revising a previous draft based on critic feedback. The feedback is:

{critic_feedback}

Address every point raised. Do not merely rephrase — make substantive improvements.
The structure and citation rules above still apply in full."""


def _format_chunks_for_prompt(
    sub_questions: list[SubQuestion],
    chunks: list[RetrievedChunk],
) -> str:
    # Group chunks by sub-question id
    grouped: dict[str, list[RetrievedChunk]] = {sq["id"]: [] for sq in sub_questions}
    for chunk in chunks:
        sq_id = chunk["sub_question_id"]
        if sq_id in grouped:
            grouped[sq_id].append(chunk)

    sections = []
    for sq in sub_questions:
        sq_chunks = grouped.get(sq["id"], [])
        section = f"Sub-question: {sq['question']}\n"

        if not sq_chunks:
            section += "  [No chunks retrieved for this sub-question]\n"
        else:
            for i, chunk in enumerate(sq_chunks, 1):
                section += (
                    f"  Chunk {i} [Source: {chunk['source']} | Score: {chunk['score']}]:\n"
                    f"  {chunk['text'].strip()}\n\n"
                )
        sections.append(section)

    return "\n".join(sections)


def build_writer_prompt(
    query: str,
    sub_questions: list[SubQuestion],
    retrieved_chunks: list[RetrievedChunk],
    critic_feedback: str | None = None,
) -> str:
    system = WRITER_SYSTEM_PROMPT

    if critic_feedback:
        system += REVISION_INSTRUCTION.format(critic_feedback=critic_feedback)

    context_block = _format_chunks_for_prompt(sub_questions, retrieved_chunks)

    return f"""{system}

Original research query: {query}

Retrieved source material:
{context_block}

Write the full research report now:"""