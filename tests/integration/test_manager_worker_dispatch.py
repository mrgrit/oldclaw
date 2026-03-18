import unittest
from uuid import uuid4

from tests.integration.support import ManagerIntegrationTestCase


class ManagerWorkerDispatchIntegrationTest(ManagerIntegrationTestCase):
    def test_scheduler_run_once_trigger_processes_due_schedule(self):
        project_id = self.create_project(
            name=f"project-scheduler-dispatch-{uuid4().hex[:8]}",
            request_text="manager scheduler trigger",
        )
        self.client.post(
            f"/projects/{project_id}/schedules",
            json={"schedule_type": "interval", "metadata": {"interval_seconds": 60}},
        ).raise_for_status()

        response = self.client.post("/projects/scheduler/run-once")
        response.raise_for_status()
        payload = response.json()["result"]

        self.assertGreaterEqual(payload["processed_count"], 1)

    def test_watch_run_once_trigger_processes_running_watch_job(self):
        project_id = self.create_project(
            name=f"project-watch-dispatch-{uuid4().hex[:8]}",
            request_text="manager watch trigger",
        )
        self.client.post(
            f"/projects/{project_id}/watch-jobs",
            json={"watch_type": "heartbeat", "metadata": {"event_type": "watch_alert"}},
        ).raise_for_status()

        response = self.client.post("/projects/watch/run-once")
        response.raise_for_status()
        payload = response.json()["result"]

        self.assertGreaterEqual(payload["processed_count"], 1)


if __name__ == "__main__":
    unittest.main()
