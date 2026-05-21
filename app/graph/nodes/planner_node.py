import json
import time
import uuid
from app.graph.state import ResearchState, SubQuestion
from app.llm.gemini import gemini_flash
from app.llm.prompts.planner_prompt import build_planner_prompt


def planner_node(state: ResearchState) -> dict:
    query = state["query"]

    prompt = build_planner_prompt(query)

    start = time.time()
    response = gemini_flash.generate_content(prompt)
    latency = round(time.time() - start, 3)

    sub_questions = _parse_sub_questions(response.text)

    return {
        "sub_questions": sub_questions,
        "report_metadata": {
            **state.get("report_metadata", {}),
            "planner_latency_s": latency,
            "planner_input_tokens": _count_tokens(prompt),
            "planner_output_tokens": _count_tokens(response.text),
        },
    }


def _parse_sub_questions(raw: str) -> list[SubQuestion]:
    # Strip markdown fences if model wraps output in ```json ... ```
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback — treat each non-empty line as a sub-question
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        data = [{"question": l} for l in lines]

    sub_questions: list[SubQuestion] = []
    for i, item in enumerate(data):
        question_text = item if isinstance(item, str) else item.get("question", "")
        if question_text:
            sub_questions.append(SubQuestion(
                id=str(uuid.uuid4()),
                question=question_text.strip(),
            ))

    return sub_questions


def _count_tokens(text: str) -> int:
    # Rough approximation — 1 token ≈ 4 characters
    # Replace with gemini_flash.count_tokens() if you want exact counts
    return len(text) // 4