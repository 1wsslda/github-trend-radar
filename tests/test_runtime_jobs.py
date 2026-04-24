from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.jobs import make_job_event_runtime
from gitsonar.runtime.utils import iso_now, normalize


class RuntimeJobsTests(unittest.TestCase):
    def test_job_lifecycle_records_normalized_events(self):
        runtime = make_job_event_runtime(normalize=normalize, iso_now=iso_now, max_events=10)

        created = runtime.create_job("discovery", title="Keyword discovery", payload={"query": "agent"})
        running = runtime.update_job(
            created["id"],
            status="running",
            stage="searching",
            progress=0.5,
            message="Searching GitHub",
            payload={"count": 3},
        )
        completed = runtime.update_job(created["id"], status="completed", progress=1.0, message="Done")

        self.assertEqual(created["job_type"], "discovery")
        self.assertEqual(running["progress_percent"], 50)
        self.assertEqual(completed["status"], "completed")
        self.assertTrue(completed["finished_at"])

        events = runtime.export_events()["events"]
        self.assertEqual([event["event_type"] for event in events], ["job.created", "job.updated", "job.completed"])
        self.assertEqual(events[-1]["job_id"], created["id"])

    def test_events_are_pruned_and_can_be_filtered_by_after_id(self):
        runtime = make_job_event_runtime(normalize=normalize, iso_now=iso_now, max_events=3)
        job = runtime.create_job("refresh")
        runtime.record_event("custom.one", job_id=job["id"])
        marker = runtime.record_event("custom.two", job_id=job["id"])
        runtime.record_event("custom.three", job_id=job["id"])

        events = runtime.export_events()["events"]
        self.assertEqual([event["event_type"] for event in events], ["custom.one", "custom.two", "custom.three"])
        self.assertEqual([event["event_type"] for event in runtime.export_events(after_id=marker["id"])["events"]], ["custom.three"])

    def test_export_jobs_filters_by_status(self):
        runtime = make_job_event_runtime(normalize=normalize, iso_now=iso_now, max_events=10)
        runtime.create_job("refresh")
        running = runtime.create_job("ai", title="AI insight")
        runtime.update_job(running["id"], status="running")

        payload = runtime.export_jobs(status="running")

        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["jobs"][0]["job_type"], "ai")


if __name__ == "__main__":
    unittest.main()
