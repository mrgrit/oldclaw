import json
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from packages.project_service import create_project_record, get_connection
from tests.integration.support import load_module


class WorkerFlowIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        scheduler_module = load_module(
            f"oldclaw_scheduler_test_{uuid4().hex}",
            "apps/scheduler-worker/src/main.py",
        )
        watch_module = load_module(
            f"oldclaw_watch_test_{uuid4().hex}",
            "apps/watch-worker/src/main.py",
        )
        cls.scheduler_client = TestClient(scheduler_module.create_app())
        cls.watch_client = TestClient(watch_module.create_app())

    def create_project(self, name: str, request_text: str) -> str:
        project = create_project_record(name=name, request_text=request_text, mode="one_shot")
        return project["id"]

    def test_scheduler_run_once_updates_schedule_and_history(self):
        project_id = self.create_project(
            name=f"project-schedule-{uuid4().hex[:8]}",
            request_text="scheduler integration check",
        )
        schedule_id = None
        due_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO schedules (project_id, schedule_type, next_run, enabled, metadata)
                    VALUES (%s, %s, %s, true, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        project_id,
                        "interval",
                        due_at,
                        json.dumps({"interval_seconds": 60}),
                    ),
                )
                schedule_id = str(cur.fetchone()[0])
            conn.commit()

        response = self.scheduler_client.post("/run-once")
        response.raise_for_status()
        payload = response.json()

        matching_items = [
            item for item in payload["items"] if str(item["schedule"]["id"]) == schedule_id
        ]
        self.assertEqual(len(matching_items), 1)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM histories WHERE project_id = %s AND event = %s",
                    (project_id, "schedule_triggered"),
                )
                history_count = cur.fetchone()[0]
                cur.execute(
                    "SELECT last_run, next_run FROM schedules WHERE id = %s",
                    (schedule_id,),
                )
                last_run, next_run = cur.fetchone()

        self.assertEqual(history_count, 1)
        self.assertIsNotNone(last_run)
        self.assertIsNotNone(next_run)

    def test_watch_run_once_creates_event_and_incident(self):
        project_id = self.create_project(
            name=f"project-watch-{uuid4().hex[:8]}",
            request_text="watch integration check",
        )
        watch_job_id = None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO watch_jobs (project_id, watch_type, status, metadata)
                    VALUES (%s, %s, 'running', %s::jsonb)
                    RETURNING id
                    """,
                    (
                        project_id,
                        "heartbeat",
                        json.dumps(
                            {
                                "event_type": "watch_alert",
                                "create_incident": True,
                                "severity": "high",
                                "summary": "Watch alert from integration test",
                            }
                        ),
                    ),
                )
                watch_job_id = str(cur.fetchone()[0])
            conn.commit()

        response = self.watch_client.post("/run-once")
        response.raise_for_status()
        payload = response.json()

        matching_items = [
            item for item in payload["items"] if str(item["watch_job"]["id"]) == watch_job_id
        ]
        self.assertEqual(len(matching_items), 1)
        self.assertIsNotNone(matching_items[0]["incident"])

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM watch_events WHERE watch_job_id = %s",
                    (watch_job_id,),
                )
                event_count = cur.fetchone()[0]
                cur.execute(
                    "SELECT COUNT(*) FROM incidents WHERE project_id = %s",
                    (project_id,),
                )
                incident_count = cur.fetchone()[0]
                cur.execute(
                    "SELECT COUNT(*) FROM histories WHERE project_id = %s AND event = %s",
                    (project_id, "watch_job_processed"),
                )
                history_count = cur.fetchone()[0]

        self.assertEqual(event_count, 1)
        self.assertEqual(incident_count, 1)
        self.assertEqual(history_count, 1)


if __name__ == "__main__":
    unittest.main()
