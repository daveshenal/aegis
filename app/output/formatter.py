from datetime import datetime, timezone
from app.graph.state import ResearchState
from app.schemas.report import FinalReport, ReportSection, Citation


def format_final_report(state: ResearchState) -> FinalReport:
    """
    Transforms the completed graph state into a structured
    FinalReport schema ready for JSON serialisation or PDF rendering.
    """
    final_report_text = state.get("final_report", "")
    eval_result = state.get("eval_result", {})
    metadata = state.get("report_metadata", {})
    chunks = state.get("retrieved_chunks", [])
    sub_questions = state.get("sub_questions", [])

    sections = _parse_sections(final_report_text)
    citations = _extract_citations(chunks)

    return FinalReport(
        title=_generate_title(state["query"]),
        query=state["query"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        sections=sections,
        executive_summary=_extract_executive_summary(final_report_text),
        citations=citations,
        sub_questions=[sq["question"] for sq in sub_questions],
        evaluation={
            "overall_score": eval_result.get("overall_score", 0.0),
            "passed": eval_result.get("passed", False),
            "dimension_scores": eval_result.get("scores", []),
            "summary_feedback": eval_result.get("summary_feedback", ""),
        },
        metadata={
            "revision_count": state.get("revision_count", 0),
            "total_chunks_retrieved": metadata.get("total_chunks_retrieved", 0),
            "wall_latency_s": metadata.get("wall_latency_s"),
            "prompt_versions": metadata.get("prompt_versions", {}),
        },
    )


def _generate_title(query: str) -> str:
    # Capitalise first letter, strip trailing punctuation
    query = query.strip().rstrip("?.,!")
    return query[0].upper() + query[1:] if query else "Research Report"


def _parse_sections(report_text: str) -> list[ReportSection]:
    """
    Splits the report on markdown headings (## or #).
    Each heading becomes a ReportSection with its following content.
    """
    sections: list[ReportSection] = []
    current_heading = None
    current_lines: list[str] = []

    for line in report_text.splitlines():
        stripped = line.strip()

        if stripped.startswith("## ") or stripped.startswith("# "):
            # Save previous section
            if current_heading is not None:
                sections.append(ReportSection(
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                ))
            current_heading = stripped.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save final section
    if current_heading is not None:
        sections.append(ReportSection(
            heading=current_heading,
            content="\n".join(current_lines).strip(),
        ))

    return sections


def _extract_executive_summary(report_text: str) -> str:
    """
    Looks for an executive summary section by heading keyword.
    Falls back to the last paragraph of the report if not found.
    """
    lines = report_text.splitlines()
    summary_keywords = {"executive summary", "summary", "conclusion"}

    in_summary = False
    summary_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().lower()
            if any(kw in heading for kw in summary_keywords):
                in_summary = True
                summary_lines = []
                continue
            elif in_summary:
                break
        elif in_summary:
            summary_lines.append(line)

    if summary_lines:
        return "\n".join(summary_lines).strip()

    # Fallback — return last non-empty paragraph
    paragraphs = [p.strip() for p in report_text.split("\n\n") if p.strip()]
    return paragraphs[-1] if paragraphs else ""


def _extract_citations(chunks: list) -> list[Citation]:
    """
    Deduplicated list of sources from retrieved chunks.
    One Citation per unique source, preserving highest score seen.
    """
    seen: dict[str, float] = {}
    for chunk in chunks:
        source = chunk.get("source", "unknown")
        score = chunk.get("score", 0.0)
        if source not in seen or score > seen[source]:
            seen[source] = score

    return [
        Citation(source=source, relevance_score=round(score, 4))
        for source, score in sorted(seen.items(), key=lambda x: -x[1])
    ]