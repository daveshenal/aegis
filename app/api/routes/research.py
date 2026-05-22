from fastapi import APIRouter, HTTPException
from app.schemas.api import ResearchRequest, ResearchResponse
from app.services.research_service import run_research

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchResponse)
def research(request: ResearchRequest) -> ResearchResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    try:
        result = run_research(query=request.query)
        return ResearchResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))