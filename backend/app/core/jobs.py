"""A small in-process job queue so large uploads are indexed in the background.

A single worker thread processes jobs in order, which also keeps index writes
serialised. Job state lives in memory: after a restart, unfinished jobs are gone and
the client can simply upload again.
"""

from __future__ import annotations

import itertools
import logging
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

log = logging.getLogger("ragforge.jobs")
Status = Literal["queued", "running", "done", "failed"]


@dataclass
class Job:
    id: int
    kind: str
    owner_id: int
    status: Status = "queued"
    result: Any = None
    error: str | None = None
    created: float = field(default_factory=time.time)
    finished: float | None = None


class JobQueue:
    def __init__(self, max_kept: int = 500) -> None:
        self._jobs: dict[int, Job] = {}
        self._queue: queue.Queue[tuple[Job, Callable[[], Any]] | None] = queue.Queue()
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self.max_kept = max_kept
        self._worker = threading.Thread(target=self._run, name="ragforge-jobs", daemon=True)
        self._worker.start()

    def submit(self, kind: str, owner_id: int, fn: Callable[[], Any]) -> Job:
        job = Job(next(self._ids), kind, owner_id)
        with self._lock:
            self._jobs[job.id] = job
            self._prune()
        self._queue.put((job, fn))
        return job

    def get(self, job_id: int) -> Job | None:
        return self._jobs.get(job_id)

    def _prune(self) -> None:
        finished = [j for j in self._jobs.values() if j.status in ("done", "failed")]
        excess = max(0, len(self._jobs) - self.max_kept)
        for job in sorted(finished, key=lambda j: j.created)[:excess]:
            del self._jobs[job.id]

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            job, fn = item
            job.status = "running"
            try:
                job.result = fn()
                job.status = "done"
            except Exception as exc:  # report any failure on the job, keep the worker alive
                log.exception("job %s failed", job.id)
                job.error = str(exc) or exc.__class__.__name__
                job.status = "failed"
            finally:
                job.finished = time.time()
                self._queue.task_done()

    def join(self) -> None:
        """Block until every submitted job has finished (used in tests and shutdown)."""
        self._queue.join()

    def shutdown(self) -> None:
        self._queue.put(None)
