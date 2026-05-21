from langgraph.graph import StateGraph, END
from app.graph.state import ResearchState
from app.graph.nodes.planner_node import planner_node
from app.graph.nodes.retriever_node import retriever_node
from app.graph.nodes.report_writer_node import report_writer_node
from app.graph.nodes.report_critic_node import report_critic_node
from app.graph.nodes.report_revisor_node import report_revisor_node


# ── Conditional routing function ───────────────────────────────────────────────
# Called by LangGraph after every critic node execution.
# Returns the name of the next node to route to.

def route_after_critic(state: ResearchState) -> str:
    eval_result = state["eval_result"]
    revision_count = state["revision_count"]
    max_revisions = state["max_revisions"]

    # Force exit if we've hit the revision cap — return best draft we have
    if revision_count >= max_revisions:
        return "output"

    # Route to revisor if critic did not pass
    if not eval_result["passed"]:
        return "revisor"

    # Critic passed — proceed to output
    return "output"


# ── Output node ────────────────────────────────────────────────────────────────
# Finalises the report by copying draft_report into final_report.
# Kept here rather than a separate file because it has no LLM call —
# it's pure state manipulation.

def output_node(state: ResearchState) -> dict:
    return {
        "final_report": state["draft_report"],
        "report_metadata": {
            **state.get("report_metadata", {}),
            "revision_count": state["revision_count"],
            "passed_critic": state["eval_result"]["passed"],
            "final_score": state["eval_result"]["overall_score"],
        },
    }


# ── Graph assembly ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(ResearchState)

    # Register nodes
    builder.add_node("planner",  planner_node)
    builder.add_node("retriever", retriever_node)
    builder.add_node("writer",   report_writer_node)
    builder.add_node("critic",   report_critic_node)
    builder.add_node("revisor",  report_revisor_node)
    builder.add_node("output",   output_node)

    # Entry point
    builder.set_entry_point("planner")

    # Linear edges
    builder.add_edge("planner",   "retriever")
    builder.add_edge("retriever", "writer")
    builder.add_edge("writer",    "critic")

    # Conditional edge after critic
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "revisor": "revisor",
            "output":  "output",
        }
    )

    # Revisor loops back to writer
    builder.add_edge("revisor", "writer")

    # Output is terminal
    builder.add_edge("output", END)

    return builder.compile()


# ── Singleton graph instance ───────────────────────────────────────────────────
# Compiled once at import time and reused across all requests.
# StateGraph compilation is expensive — don't do it per request.

research_graph = build_graph()