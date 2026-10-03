from dataclasses import dataclass
from datetime import datetime
from typing import Literal


JobState = Literal[
    "queued",
    "cloning",
    "analyzing",
    "parsing",
    "embedding",
    "storing",
    "ready",
    "failed",
]


@dataclass
class JobStatus:
    job_id: str
    repo_id: str
    state: JobState
    message: str | None = None
    error: str | None = None
    current_step: str | None = None
    active_agent: str | None = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def update(
        self,
        state: JobState,
        message: str | None = None,
        error: str | None = None,
        current_step: str | None = None,
        active_agent: str | None = None,
    ) -> None:
        self.state = state
        self.message = message
        self.error = error
        self.current_step = current_step
        self.active_agent = active_agent
        self.updated_at = datetime.now()