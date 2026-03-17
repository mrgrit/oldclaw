import unittest
from uuid import uuid4

from tests.integration.support import ManagerIntegrationTestCase


class ManagerSchedulerWatchIntegrationTest(ManagerIntegrationTestCase):
    def test_create_and_list_project_schedules(self):
        project_id = self.create_project(
            name=f"project-schedule-api-{uuid4().hex[:8]}",
            request_text="manager schedule api check",
        )

        create_response = self.client.post(
            f"/projects/{project_id}/schedules",
            json={
                "schedule_type": "interval",
                "metadata": {"interval_seconds": 120},
            },
        )
        create_response.raise_for_status()
        schedule = create_response.json()["schedule"]

        list_response = self.client.get(f"/projects/{project_id}/schedules")
        list_response.raise_for_status()
        items = list_response.json()["items"]

        matching = [item for item in items if str(item["id"]) == str(schedule["id"])]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["schedule_type"], "interval")

    def test_create_and_list_project_watch_jobs(self):
        project_id = self.create_project(
            name=f"project-watch-api-{uuid4().hex[:8]}",
            request_text="manager watch api check",
        )

        create_response = self.client.post(
            f"/projects/{project_id}/watch-jobs",
            json={
                "watch_type": "heartbeat",
                "metadata": {"event_type": "watch_alert", "create_incident": True},
            },
        )
        create_response.raise_for_status()
        watch_job = create_response.json()["watch_job"]

        list_response = self.client.get(f"/projects/{project_id}/watch-jobs")
        list_response.raise_for_status()
        items = list_response.json()["items"]

        matching = [item for item in items if str(item["id"]) == str(watch_job["id"])]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["watch_type"], "heartbeat")


if __name__ == "__main__":
    unittest.main()
