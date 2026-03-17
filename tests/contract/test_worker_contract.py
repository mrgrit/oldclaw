import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.integration.support import load_module


scheduler_module = load_module(
    "oldclaw_scheduler_contract",
    "apps/scheduler-worker/src/main.py",
)
watch_module = load_module(
    "oldclaw_watch_contract",
    "apps/watch-worker/src/main.py",
)


class WorkerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scheduler_client = TestClient(scheduler_module.create_app())
        cls.watch_client = TestClient(watch_module.create_app())

    def test_scheduler_run_once_response_shape(self):
        result = {
            "loaded_count": 1,
            "processed_count": 1,
            "items": [{"schedule": {"id": "sch_1"}, "history": {"id": "hist_1"}}],
        }
        with patch.object(scheduler_module, "run_scheduler_once", return_value=result):
            response = self.scheduler_client.post("/run-once")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "loaded_count", "processed_count", "items"})
        self.assertEqual(payload["status"], "ok")
        self.assertIsInstance(payload["items"], list)

    def test_watch_run_once_response_shape(self):
        result = {
            "loaded_count": 1,
            "processed_count": 1,
            "items": [{"watch_job": {"id": "wj_1"}, "watch_event": {"id": "evt_1"}, "incident": None, "history": {"id": "hist_1"}}],
        }
        with patch.object(watch_module, "run_watch_once", return_value=result):
            response = self.watch_client.post("/run-once")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "loaded_count", "processed_count", "items"})
        self.assertEqual(payload["status"], "ok")
        self.assertIsInstance(payload["items"], list)


if __name__ == "__main__":
    unittest.main()
