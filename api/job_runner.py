import threading
import uuid
import traceback
from datetime import datetime
from pathlib import Path

from ingestion.cloner import RepositoryCloner
from ingestion.orchestrator import IngestionOrchestrator
from models.job_status import JobStatus


class JobRunner:
    def __init__(
        self,
        cloner: RepositoryCloner,
        orchestrator: IngestionOrchestrator,
    ):
        self.cloner = cloner
        self.orchestrator = orchestrator
        self.jobs: dict[str, JobStatus] = {}
        self._lock = threading.Lock()

    def submit(self, repo_url: str) -> str:
        job_id = str(uuid.uuid4())
        repo_id = self.cloner.repo_id_from_url(repo_url)

        job = JobStatus(
            job_id=job_id,
            repo_id=repo_id,
            state="queued",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with self._lock:
            self.jobs[job_id] = job

        thread = threading.Thread(
            target=self._run,
            args=(job_id, repo_url),
            daemon=True,
        )
        thread.start()

        return job_id

    def get_status(
        self,
        job_id: str,
    ) -> JobStatus | None:
        with self._lock:
            return self.jobs.get(job_id)

    def _run(
        self,
        job_id: str,
        repo_url: str,
    ) -> None:
        job = self.jobs[job_id]

        try:
            job.update(
                "cloning",
                "Cloning repository",
                current_step="cloning",
                active_agent="repository_cloner",
            )

            repo_path = self.cloner.clone(
                repo_url,
                job.repo_id,
            )

            job.update(
                "analyzing",
                "Analyzing repository",
                current_step="analyzing",
                active_agent="ingestion_orchestrator",
            )

            def progress_callback(step: str, message: str, agent: str | None = None) -> None:
                job.update(
                    job.state,
                    message,
                    current_step=step,
                    active_agent=agent,
                )

            self.orchestrator.run(
                Path(repo_path),
                job.repo_id,
                progress_callback=progress_callback,
            )

            # Post-ingest validation: ensure chunks were created
            try:
                chunk_count = self.orchestrator.postgres.count_chunks(job.repo_id)
                file_count = self.orchestrator.postgres.count_files(job.repo_id)
            except Exception as exc:
                # If counting fails, treat as ingestion failure
                tb = traceback.format_exc()
                job.update(
                    "failed",
                    f"Post-ingest validation failed: {exc}",
                    error=tb,
                    current_step="failed",
                    active_agent=None,
                )
                print(tb)
                return

            if chunk_count == 0:
                msg = (
                    f"Ingestion completed but no chunks were inserted (files={file_count}, chunks={chunk_count})."
                )
                job.update(
                    "failed",
                    msg,
                    error=msg,
                    current_step="failed",
                    active_agent=None,
                )
                print(msg)
                return

            job.update(
                "ready",
                "Repository ingestion completed",
                current_step="completed",
                active_agent=None,
            )

        except Exception as exc:
            tb = traceback.format_exc()
            # update job with full traceback to aid debugging
            job.update(
                "failed",
                f"Repository ingestion failed: {exc}",
                error=tb,
                current_step="failed",
                active_agent=None,
            )
            # also print to server logs
            print(tb)