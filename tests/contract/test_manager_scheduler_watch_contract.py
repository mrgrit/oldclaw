import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.integration.support import load_module


manager_module = load_module(
    "oldclaw_manager_scheduler_watch_contract",
    "apps/manager-api/src/main.py",
)


class ManagerSchedulerWatchContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(manager_module.create_app())

    def test_create_schedule_response_shape(self):
        schedule = {"id": "sch_1", "project_id": "prj_1", "schedule_type": "interval"}
        with patch.object(manager_module, "create_schedule_record", return_value=schedule):
            response = self.client.post(
                "/projects/prj_1/schedules",
                json={"schedule_type": "interval", "metadata": {"interval_seconds": 60}},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "schedule"})
        self.assertEqual(set(payload["schedule"].keys()), {"id", "project_id", "schedule_type"})

    def test_create_watch_job_response_shape(self):
        watch_job = {"id": "wj_1", "project_id": "prj_1", "watch_type": "heartbeat"}
        with patch.object(manager_module, "create_watch_job_record", return_value=watch_job):
            response = self.client.post(
                "/projects/prj_1/watch-jobs",
                json={"watch_type": "heartbeat", "metadata": {"event_type": "watch_alert"}},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "watch_job"})
        self.assertEqual(set(payload["watch_job"].keys()), {"id", "project_id", "watch_type"})


if __name__ == "__main__":
    unittest.main()
