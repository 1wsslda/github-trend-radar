#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
from itertools import count
from types import SimpleNamespace

TERMINAL_JOB_STATUSES = {"completed", "failed", "cancelled"}


def _clone(payload: object) -> object:
    return json.loads(json.dumps(payload, ensure_ascii=False))


def make_job_event_runtime(*, normalize, iso_now, max_events: int = 200, max_jobs: int = 50):
    lock = threading.RLock()
    job_counter = count(1)
    event_counter = count(1)
    jobs: dict[str, dict[str, object]] = {}
    events: list[dict[str, object]] = []

    def clamp_progress(value: object) -> float:
        try:
            progress = float(value)
        except (TypeError, ValueError):
            progress = 0.0
        return max(0.0, min(1.0, progress))

    def job_snapshot(job: dict[str, object]) -> dict[str, object]:
        progress = clamp_progress(job.get("progress"))
        snapshot = dict(job)
        snapshot["progress"] = progress
        snapshot["progress_percent"] = max(0, min(100, int(round(progress * 100))))
        return _clone(snapshot)

    def prune_jobs() -> None:
        if len(jobs) <= max_jobs:
            return
        terminal_ids = [
            job_id
            for job_id, job in jobs.items()
            if normalize(job.get("status")) in TERMINAL_JOB_STATUSES
        ]
        for job_id in terminal_ids[: max(0, len(jobs) - max_jobs)]:
            jobs.pop(job_id, None)

    def prune_events() -> None:
        if len(events) > max_events:
            del events[: len(events) - max_events]

    def record_event(event_type: object, *, job_id: object = "", payload: object | None = None) -> dict[str, object]:
        clean_type = normalize(event_type) or "event"
        event = {
            "id": f"event-{next(event_counter):06d}",
            "event_type": clean_type,
            "job_id": normalize(job_id),
            "created_at": iso_now(),
            "payload": _clone(payload if isinstance(payload, dict) else {}),
        }
        with lock:
            events.append(event)
            prune_events()
            return _clone(event)

    def create_job(job_type: object, *, title: object = "", payload: object | None = None) -> dict[str, object]:
        created_at = iso_now()
        job = {
            "id": f"job-{next(job_counter):06d}",
            "job_type": normalize(job_type) or "job",
            "title": normalize(title),
            "status": "queued",
            "stage": "",
            "message": "",
            "progress": 0.0,
            "created_at": created_at,
            "updated_at": created_at,
            "started_at": "",
            "finished_at": "",
            "payload": _clone(payload if isinstance(payload, dict) else {}),
        }
        with lock:
            jobs[job["id"]] = job
            prune_jobs()
        record_event("job.created", job_id=job["id"], payload=job_snapshot(job))
        return job_snapshot(job)

    def update_job(
        job_id: object,
        *,
        status: object | None = None,
        stage: object | None = None,
        progress: object | None = None,
        message: object | None = None,
        payload: object | None = None,
    ) -> dict[str, object]:
        clean_id = normalize(job_id)
        with lock:
            if clean_id not in jobs:
                raise ValueError("job not found")
            job = jobs[clean_id]
            next_status = normalize(status) if status is not None else normalize(job.get("status"))
            now = iso_now()
            if next_status:
                job["status"] = next_status
                if next_status == "running" and not normalize(job.get("started_at")):
                    job["started_at"] = now
                if next_status in TERMINAL_JOB_STATUSES:
                    job["finished_at"] = normalize(job.get("finished_at")) or now
            if stage is not None:
                job["stage"] = normalize(stage)
            if progress is not None:
                job["progress"] = clamp_progress(progress)
            if message is not None:
                job["message"] = normalize(message)
            if isinstance(payload, dict):
                job["payload"] = _clone(payload)
            job["updated_at"] = now
            snapshot = job_snapshot(job)
        event_type = "job.completed" if normalize(snapshot.get("status")) in TERMINAL_JOB_STATUSES else "job.updated"
        record_event(event_type, job_id=clean_id, payload=snapshot)
        return snapshot

    def export_jobs(*, status: object = "") -> dict[str, object]:
        clean_status = normalize(status)
        with lock:
            snapshots = [job_snapshot(job) for job in jobs.values()]
        if clean_status:
            snapshots = [job for job in snapshots if normalize(job.get("status")) == clean_status]
        return {
            "ok": True,
            "status": clean_status,
            "count": len(snapshots),
            "jobs": snapshots,
        }

    def export_events(*, after_id: object = "", limit: object = 100) -> dict[str, object]:
        clean_after = normalize(after_id)
        try:
            clean_limit = max(1, min(500, int(limit)))
        except (TypeError, ValueError):
            clean_limit = 100
        with lock:
            snapshots = _clone(events)
        if clean_after:
            matching_indexes = [index for index, event in enumerate(snapshots) if event.get("id") == clean_after]
            if matching_indexes:
                snapshots = snapshots[matching_indexes[-1] + 1 :]
        snapshots = snapshots[-clean_limit:]
        return {
            "ok": True,
            "after_id": clean_after,
            "count": len(snapshots),
            "events": snapshots,
        }

    return SimpleNamespace(
        create_job=create_job,
        update_job=update_job,
        record_event=record_event,
        export_jobs=export_jobs,
        export_events=export_events,
    )


__all__ = ["TERMINAL_JOB_STATUSES", "make_job_event_runtime"]
