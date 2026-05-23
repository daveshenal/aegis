from fastapi import FastAPI
from app.api.routes.research import router as research_router
from app.api.routes.ingest import router as ingest_router
from app.observability.logging import setup_logging

setup_logging()

app = FastAPI(
    title="Agentic Research System",
    description="Multi-agent research synthesis pipeline powered by LangGraph and Gemini.",
    version="1.0.0",
)

app.include_router(research_router)
app.include_router(ingest_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}