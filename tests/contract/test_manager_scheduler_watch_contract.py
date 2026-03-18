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

    def test_list_watch_events_response_shape(self):
        items = [{"id": "evt_1", "event_type": "watch_alert", "watch_job_id": "wj_1"}]
        with patch.object(manager_module, "get_project_watch_events", return_value=items):
            response = self.client.get("/projects/prj_1/watch-events")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "items"})
        self.assertEqual(set(payload["items"][0].keys()), {"id", "event_type", "watch_job_id"})

    def test_list_incidents_response_shape(self):
        items = [{"id": "inc_1", "severity": "high", "status": "open"}]
        with patch.object(manager_module, "get_project_incidents", return_value=items):
            response = self.client.get("/projects/prj_1/incidents")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "items"})
        self.assertEqual(set(payload["items"][0].keys()), {"id", "severity", "status"})

    def test_acknowledge_incident_response_shape(self):
        incident = {"id": "inc_1", "severity": "high", "status": "acknowledged"}
        with patch.object(manager_module, "update_project_incident_status", return_value=incident):
            response = self.client.post("/projects/prj_1/incidents/inc_1/acknowledge")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "incident"})
        self.assertEqual(set(payload["incident"].keys()), {"id", "severity", "status"})

    def test_close_incident_response_shape(self):
        incident = {"id": "inc_1", "severity": "high", "status": "closed"}
        with patch.object(manager_module, "update_project_incident_status", return_value=incident):
            response = self.client.post("/projects/prj_1/incidents/inc_1/close")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "incident"})
        self.assertEqual(set(payload["incident"].keys()), {"id", "severity", "status"})


if __name__ == "__main__":
    unittest.main()
