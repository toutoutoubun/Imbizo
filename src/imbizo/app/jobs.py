"""Local background job helpers."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any


JobCallable = Callable[["ProgressReporter", "CancellationToken"], Any]


class CancellationToken:
    """Cooperative cancellation flag for local background jobs."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""

        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Return whether cancellation has been requested."""

        return self._cancelled


@dataclass(slots=True)
class ProgressUpdate:
    """One job progress update."""

    message: str
    current: int | None = None
    total: int | None = None


@dataclass(slots=True)
class ProgressReporter:
    """Receives progress updates from background jobs."""

    updates: list[ProgressUpdate] = field(default_factory=list)

    def update(self, message: str, current: int | None = None, total: int | None = None) -> None:
        """Report job progress in researcher-readable terms."""

        self.updates.append(ProgressUpdate(message=message, current=current, total=total))


@dataclass(slots=True)
class JobHandle:
    """Handle for a submitted local job."""

    name: str
    future: Future[Any]
    cancellation_token: CancellationToken
    progress: ProgressReporter

    def cancel(self) -> None:
        """Request cooperative cancellation."""

        self.cancellation_token.cancel()


class JobRunner:
    """Run local jobs and marshal progress back to the caller."""

    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="imbizo")

    def submit(self, name: str, job: JobCallable) -> JobHandle:
        """Submit a job and return a handle for progress and cancellation."""

        progress = ProgressReporter()
        token = CancellationToken()
        future = self._executor.submit(job, progress, token)
        return JobHandle(name=name, future=future, cancellation_token=token, progress=progress)
