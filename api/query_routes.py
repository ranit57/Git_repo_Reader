from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from query.orchestrator import QueryOrchestrator


class QueryRequest(BaseModel):
    repo_id: str
    query: str


class QueryResponse(BaseModel):
    answer: str


def create_router(
    orchestrator: QueryOrchestrator,
) -> APIRouter:
    router = APIRouter(
        prefix="/query",
        tags=["query"],
    )

    @router.post("", response_model=QueryResponse)
    def query(request: QueryRequest):
        try:
            answer = orchestrator.run(request.query, request.repo_id)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Query failed",
            ) from exc

        return QueryResponse(answer=answer)

    return router
