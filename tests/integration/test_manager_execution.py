import unittest
from uuid import uuid4

from tests.integration.support import ManagerIntegrationTestCase


class ManagerExecutionIntegrationTest(ManagerIntegrationTestCase):

    def move_project_to_execute(self, project_id: str) -> None:
        response = self.client.post(f"/projects/{project_id}/plan")
        response.raise_for_status()

    def test_execute_run_failure_produces_failed_validation(self):
        prefix = f"fail_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="integration failure validation check",
            mode="one_shot",
        )
        self.move_project_to_execute(project_id)

        response = self.client.post(
            f"/projects/{project_id}/execute/run",
            json={
                "script": "printf 'integration execute failure\\n'; exit 9",
                "timeout_s": 10,
            },
        )
        response.raise_for_status()
        execute_payload = response.json()
        self.assertEqual(execute_payload["subagent_result"]["detail"]["exit_code"], 9)

        validate_response = self.client.post(f"/projects/{project_id}/validate")
        validate_response.raise_for_status()
        validate_payload = validate_response.json()["result"]

        self.assertEqual(validate_payload["validation_run"]["status"], "failed")
        self.assertEqual(
            validate_payload["validation_run"]["actual_result"]["failing_evidence_count"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
