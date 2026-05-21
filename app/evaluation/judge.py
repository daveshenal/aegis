import json
from app.graph.state import EvalResult, DimensionScore


PASS_THRESHOLD = 3.5
EXPECTED_DIMENSIONS = {"Coherence", "Coverage", "Groundedness", "Conciseness"}


def parse_eval_result(raw: str) -> EvalResult:
    cleaned = _strip_markdown(raw)

    try:
        data = json.loads(cleaned)
        return _build_eval_result(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return _fallback_eval_result(raw)


def _strip_markdown(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _build_eval_result(data: dict) -> EvalResult:
    raw_scores = data.get("scores", [])

    dimension_scores: list[DimensionScore] = []
    for item in raw_scores:
        dimension = item.get("dimension", "Unknown")
        score = float(item.get("score", 0.0))
        feedback = item.get("feedback", "")
        dimension_scores.append(DimensionScore(
            dimension=dimension,
            score=score,
            feedback=feedback,
        ))

    # Recompute overall score as mean of dimension scores
    # Don't trust the model's self-reported overall — recompute it
    if dimension_scores:
        overall_score = round(
            sum(d["score"] for d in dimension_scores) / len(dimension_scores), 2
        )
    else:
        overall_score = 0.0

    # Pass only if every dimension meets threshold
    passed = all(d["score"] >= PASS_THRESHOLD for d in dimension_scores)

    summary_feedback = data.get("summary_feedback", "No feedback provided.")

    return EvalResult(
        scores=dimension_scores,
        overall_score=overall_score,
        passed=passed,
        summary_feedback=summary_feedback,
    )


def _fallback_eval_result(raw: str) -> EvalResult:
    # If parsing fails entirely, fail the report with a low score
    # so the graph routes to revision rather than silently passing bad output
    fallback_score = DimensionScore(
        dimension="ParseError",
        score=1.0,
        feedback=f"Critic output could not be parsed. Raw output: {raw[:300]}",
    )
    return EvalResult(
        scores=[fallback_score],
        overall_score=1.0,
        passed=False,
        summary_feedback="Critic output was malformed. Revision triggered automatically.",
    )