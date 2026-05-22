from app.graph.state import DimensionScore


REVISOR_SYSTEM_PROMPT = """You are an expert research editor. You will receive a research report that has failed a quality evaluation on one or more dimensions. Your job is to produce an improved version of the report that directly addresses the identified weaknesses.

Rules:
- Only fix what is broken. Do not restructure sections that passed evaluation.
- Preserve all citations and source references from the original draft.
- Do not introduce new information not present in the original draft.
- Do not add a preamble or explanation of what you changed.
- Return the full revised report, not just the changed sections.
- Maintain the same section structure and heading format as the original."""


def _format_failed_dimensions(failed_dimensions: list[DimensionScore]) -> str:
    if not failed_dimensions:
        return "No specific dimensions failed — apply general quality improvements."

    lines = []
    for dim in failed_dimensions:
        lines.append(
            f"  - {dim['dimension']} (score: {dim['score']}/5.0):\n"
            f"    {dim['feedback']}"
        )
    return "\n".join(lines)


def build_revisor_prompt(
    query: str,
    draft_report: str,
    failed_dimensions: list[DimensionScore],
    summary_feedback: str,
) -> str:
    failed_block = _format_failed_dimensions(failed_dimensions)

    return f"""{REVISOR_SYSTEM_PROMPT}

Original research query: {query}

Overall critic feedback:
{summary_feedback}

Dimensions that failed and must be fixed:
{failed_block}

Current draft report:
{draft_report}

Write the full revised report now:"""