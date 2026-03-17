import unittest
from uuid import uuid4

from packages.history_service import persist_project_closure_memory
from tests.integration.support import ManagerIntegrationTestCase


class ManagerHistoryIntegrationTest(ManagerIntegrationTestCase):

    def test_run_auto_creates_history_and_task_memory(self):
        prefix = f"hist_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="integration history check",
            mode="one_shot",
        )

        run_response = self.client.post(f"/projects/{project_id}/run/auto")
        run_response.raise_for_status()
        payload = run_response.json()

        self.assertEqual(payload["validated"]["validation_run"]["status"], "passed")
        self.assertTrue(payload["memory"]["created"])

        history_response = self.client.get(f"/projects/{project_id}/history")
        history_response.raise_for_status()
        history_payload = history_response.json()

        self.assertEqual(len(history_payload["history"]), 1)
        self.assertEqual(len(history_payload["task_memories"]), 1)
        self.assertIn("diagnose_web_latency", history_payload["task_memories"][0]["summary"])

    def test_persist_project_closure_memory_is_idempotent(self):
        prefix = f"idem_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="integration closure memory idempotency",
            mode="one_shot",
        )

        run_response = self.client.post(f"/projects/{project_id}/run/auto")
        run_response.raise_for_status()
        first_memory = run_response.json()["memory"]
        self.assertTrue(first_memory["created"])

        second_memory = persist_project_closure_memory(project_id)
        self.assertFalse(second_memory["created"])
        self.assertEqual(second_memory["task_memory"]["id"], first_memory["task_memory"]["id"])
        self.assertEqual(second_memory["history"]["id"], first_memory["history"]["id"])

        history_response = self.client.get(f"/projects/{project_id}/history")
        history_response.raise_for_status()
        history_payload = history_response.json()
        self.assertEqual(len(history_payload["history"]), 1)
        self.assertEqual(len(history_payload["task_memories"]), 1)


if __name__ == "__main__":
    unittest.main()
