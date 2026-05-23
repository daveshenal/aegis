from app.config import settings


def get_langsmith_config(run_name: str) -> dict:
    """
    Returns a LangGraph-compatible run config dict that
    enables LangSmith tracing for the graph invocation.

    Pass the returned dict as the `config` argument to
    research_graph.invoke(..., config=langsmith_config).
    """
    return {
        "run_name": run_name,
        "tags": ["research", "production"],
        "metadata": {
            "project": settings.LANGCHAIN_PROJECT,
        },
    }