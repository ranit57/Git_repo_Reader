from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from api.job_runner import JobRunner


router = APIRouter(
    prefix="/ingest",
    tags=["ingestion"],
)


class IngestRequest(BaseModel):
    repo_url: HttpUrl


class IngestResponse(BaseModel):
    job_id: str
    repo_id: str
    status: str


def create_router(
    job_runner: JobRunner,
) -> APIRouter:

    @router.post(
        "",
        response_model=IngestResponse,
    )
    def ingest(request: IngestRequest):
        job_id = job_runner.submit(
            str(request.repo_url)
        )

        return IngestResponse(
            job_id=job_id,
            repo_id=job_runner.get_status(job_id).repo_id,
            status="queued",
        )

    @router.get("/{job_id}")
    def get_ingest_status(job_id: str):
        job = job_runner.get_status(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Ingestion job not found",
            )

        return {
            "job_id": job.job_id,
            "repo_id": job.repo_id,
            "state": job.state,
            "message": job.message,
            "current_step": job.current_step,
            "active_agent": job.active_agent,
            "error": "See server logs for details." if job.error else None,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }

    return router
