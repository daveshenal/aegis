# Custom structural evaluation metrics
# These are computed post-generation and logged to MLflow
# They complement the LLM-as-judge scores with deterministic signals


def citation_coverage_score(report: str, chunks: list[dict]) -> float:
    """
    Fraction of retrieved sources that appear at least once
    as a citation in the final report.
    A score of 1.0 means every retrieved source was cited.
    """
    sources = {chunk["source"] for chunk in chunks}
    if not sources:
        return 0.0

    cited = sum(1 for source in sources if source in report)
    return round(cited / len(sources), 3)


def section_coverage_score(report: str, sub_questions: list[dict]) -> float:
    """
    Fraction of sub-questions that have a corresponding
    headed section in the report.
    Uses a loose keyword match — checks if key terms from
    each sub-question appear as a heading in the report.
    """
    if not sub_questions:
        return 0.0

    report_lower = report.lower()
    matched = 0

    for sq in sub_questions:
        # Extract content words (ignore stop words)
        words = [
            w for w in sq["question"].lower().split()
            if w not in _STOP_WORDS and len(w) > 3
        ]
        # A section is considered covered if at least half
        # the content words appear near a heading marker (#)
        heading_lines = [
            line for line in report_lower.splitlines()
            if line.strip().startswith("#")
        ]
        heading_text = " ".join(heading_lines)
        matches = sum(1 for w in words if w in heading_text)
        if words and matches / len(words) >= 0.5:
            matched += 1

    return round(matched / len(sub_questions), 3)


def avg_chunk_score(chunks: list[dict]) -> float:
    """
    Mean similarity score of all retrieved chunks.
    A proxy for retrieval quality — low values suggest
    the query decomposition produced poorly-matched sub-questions.
    """
    if not chunks:
        return 0.0
    return round(sum(c["score"] for c in chunks) / len(chunks), 3)


def revision_efficiency_score(revision_count: int, max_revisions: int) -> float:
    """
    1.0 if the report passed on the first attempt.
    Decreases with each revision loop needed.
    Useful for tracking prompt quality over time in MLflow.
    """
    if max_revisions <= 1:
        return 1.0
    return round(1.0 - ((revision_count - 1) / max_revisions), 3)


_STOP_WORDS = {
    "what", "when", "where", "which", "how", "does", "are",
    "the", "and", "for", "with", "that", "this", "from",
    "have", "been", "will", "into", "about", "used", "using",
}