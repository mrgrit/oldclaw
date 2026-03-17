import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from packages.project_service import ProjectNotFoundError
from tests.integration.support import load_module


master_module = load_module(
    "oldclaw_master_contract",
    "apps/master-service/src/main.py",
)


class MasterServiceContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(master_module.create_app())

    def test_review_response_shape(self):
        context = {
            "project": {"current_stage": "close", "status": "completed"},
            "report": {"id": "rpt_1"},
            "evidence": [{"id": "ev_1"}],
            "validations": [{"id": "val_1", "status": "passed"}],
            "approvals": [],
            "latest_validation": {"status": "passed"},
            "latest_approval": None,
        }
        review_row = {
            "id": "mrv_1",
            "project_id": "prj_contract",
            "reviewer_agent_id": "master-contract",
            "status": "approved",
            "review_summary": "Master review approved the completed project.",
            "findings": {"validation_status": "passed"},
        }
        with patch.object(master_module, "_build_review_context", return_value=context), patch.object(
            master_module, "create_master_review_record", return_value=review_row
        ):
            response = self.client.post(
                "/projects/prj_contract/review",
                json={
                    "project_id": "prj_contract",
                    "reviewer_id": "master-contract",
                    "comments": "contract review",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "review", "context"})
        self.assertEqual(
            set(payload["review"].keys()),
            {"id", "project_id", "reviewer_agent_id", "status", "review_summary", "findings"},
        )
        self.assertEqual(
            set(payload["context"].keys()),
            {"evidence_count", "validation_count", "approval_count"},
        )

    def test_replan_response_shape(self):
        context = {
            "latest_validation": {"status": "failed"},
            "latest_approval": None,
        }
        with patch.object(master_module, "_build_review_context", return_value=context):
            response = self.client.post(
                "/projects/prj_contract/replan",
                json={"reviewer_id": "master-contract", "comments": "replan contract"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project_id", "reviewer_id", "actions", "comments"})
        self.assertIsInstance(payload["actions"], list)

    def test_get_reviews_not_found_error_shape(self):
        with patch.object(
            master_module,
            "get_master_reviews_for_project",
            side_effect=ProjectNotFoundError("Project not found: prj_missing"),
        ):
            response = self.client.get("/projects/prj_missing/reviews")

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"detail"})
        self.assertEqual(set(payload["detail"].keys()), {"message"})
        self.assertIn("prj_missing", payload["detail"]["message"])


if __name__ == "__main__":
    unittest.main()
