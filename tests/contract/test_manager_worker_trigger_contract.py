import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.integration.support import load_module


manager_module = load_module(
    "oldclaw_manager_worker_trigger_contract",
    "apps/manager-api/src/main.py",
)


class ManagerWorkerTriggerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(manager_module.create_app())

    def test_scheduler_run_once_trigger_response_shape(self):
        result = {"status": "ok", "processed_count": 1, "items": []}
        client = TestClient(manager_module.create_app(scheduler_runner=lambda: result))
        response = client.post("/projects/scheduler/run-once")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "result"})
        self.assertEqual(set(payload["result"].keys()), {"status", "processed_count", "items"})

    def test_watch_run_once_trigger_response_shape(self):
        result = {"status": "ok", "processed_count": 1, "items": []}
        client = TestClient(manager_module.create_app(watch_runner=lambda: result))
        response = client.post("/projects/watch/run-once")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "result"})
        self.assertEqual(set(payload["result"].keys()), {"status", "processed_count", "items"})


if __name__ == "__main__":
    unittest.main()
