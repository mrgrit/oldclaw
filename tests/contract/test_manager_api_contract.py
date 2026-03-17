import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from packages.policy_engine import PolicyDecision
from packages.project_service import ProjectNotFoundError, ProjectStageError
from tests.integration.support import load_module


manager_module = load_module(
    "oldclaw_manager_contract",
    "apps/manager-api/src/main.py",
)


class ManagerApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(manager_module.create_app())

    def test_create_project_response_shape(self):
        fake_project = {
            "id": "prj_contract",
            "name": "contract-project",
            "request_text": "contract check",
            "mode": "one_shot",
            "status": "created",
            "current_stage": "intake",
        }
        with patch.object(manager_module, "create_project_record", return_value=fake_project):
            response = self.client.post(
                "/projects",
                json={
                    "name": "contract-project",
                    "request_text": "contract check",
                    "mode": "one_shot",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "project"})
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(
            set(payload["project"].keys()),
            {"id", "name", "request_text", "mode", "status", "current_stage"},
        )

    def test_policy_check_response_shape(self):
        decision = PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason="sensitive playbook requires approval",
            policy_name="sensitive_playbook_requires_approval",
            risk_level="medium",
            playbook_name="onboard_new_linux_server",
            target_count=1,
            mode="one_shot",
        )
        latest_approval = {"id": "apr_1", "status": "approval_required"}
        approval_request = {
            "project_id": "prj_contract",
            "required": True,
            "reason": decision.reason,
            "policy_name": decision.policy_name,
            "risk_level": decision.risk_level,
            "playbook_name": decision.playbook_name,
            "mode": decision.mode,
            "target_count": decision.target_count,
            "status": "approval_required",
        }
        with patch.object(manager_module, "evaluate_project_policy", return_value=decision), patch.object(
            manager_module, "list_project_approvals", return_value=[latest_approval]
        ), patch.object(manager_module, "build_approval_request", return_value=approval_request):
            response = self.client.get("/projects/prj_contract/policy-check")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            set(payload.keys()),
            {"status", "project_id", "policy", "latest_approval", "approval_request"},
        )
        self.assertEqual(payload["project_id"], "prj_contract")
        self.assertEqual(
            set(payload["policy"].keys()),
            {
                "allowed",
                "requires_approval",
                "reason",
                "policy_name",
                "risk_level",
                "playbook_name",
                "target_count",
                "mode",
            },
        )
        self.assertEqual(set(payload["latest_approval"].keys()), {"id", "status"})
        self.assertEqual(
            set(payload["approval_request"].keys()),
            {
                "project_id",
                "required",
                "reason",
                "policy_name",
                "risk_level",
                "playbook_name",
                "mode",
                "target_count",
                "status",
            },
        )

    def test_run_auto_approval_required_error_shape(self):
        decision = PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason="sensitive playbook requires approval",
            policy_name="sensitive_playbook_requires_approval",
            risk_level="medium",
            playbook_name="onboard_new_linux_server",
            target_count=1,
            mode="one_shot",
        )
        denial_detail = {
            "message": decision.reason,
            "policy": decision.to_dict(),
            "approval_request": {
                "project_id": "prj_contract",
                "required": True,
                "reason": decision.reason,
                "policy_name": decision.policy_name,
                "risk_level": decision.risk_level,
                "playbook_name": decision.playbook_name,
                "mode": decision.mode,
                "target_count": decision.target_count,
                "status": "approval_required",
                "approval_id": "apr_1",
            },
        }
        with patch.object(manager_module, "get_project_record", return_value={"current_stage": "intake"}), patch.object(
            manager_module, "plan_project_record", return_value={"id": "prj_contract", "current_stage": "plan"}
        ), patch.object(
            manager_module, "_require_execution_policy", side_effect=manager_module.PolicyDeniedError(decision)
        ), patch.object(manager_module, "_build_policy_denial_detail", return_value=denial_detail):
            response = self.client.post("/projects/prj_contract/run/auto")

        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"detail"})
        self.assertEqual(set(payload["detail"].keys()), {"message", "policy", "approval_request"})
        self.assertEqual(payload["detail"]["approval_request"]["status"], "approval_required")

    def test_execute_run_stage_error_shape(self):
        with patch.object(
            manager_module,
            "_require_execution_policy",
            return_value={"allowed": True, "requires_approval": False},
        ), patch.object(
            manager_module,
            "execute_project_record",
            side_effect=ProjectStageError("Project must be in plan stage before execute"),
        ):
            response = self.client.post(
                "/projects/prj_contract/execute/run",
                json={"script": "printf 'noop'", "timeout_s": 10},
            )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"detail"})
        self.assertEqual(set(payload["detail"].keys()), {"message"})
        self.assertIn("execute", payload["detail"]["message"])

    def test_get_project_not_found_error_shape(self):
        with patch.object(
            manager_module,
            "get_project_record",
            side_effect=ProjectNotFoundError("Project not found: prj_missing"),
        ):
            response = self.client.get("/projects/prj_missing")

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"detail"})
        self.assertEqual(set(payload["detail"].keys()), {"message"})
        self.assertIn("prj_missing", payload["detail"]["message"])

    def test_execute_run_upstream_error_shape(self):
        def failing_runner(payload: dict):
            request = httpx.Request("POST", "http://subagent.local/a2a/run_script")
            response = httpx.Response(500, request=request, text='{"status":"error"}')
            raise httpx.HTTPStatusError(
                "upstream failure",
                request=request,
                response=response,
            )

        client = TestClient(manager_module.create_app(subagent_runner=failing_runner))
        with patch.object(
            manager_module,
            "_require_execution_policy",
            return_value={"allowed": True, "requires_approval": False},
        ), patch.object(
            manager_module,
            "execute_project_record",
            return_value={"id": "prj_contract", "current_stage": "execute"},
        ), patch.object(
            manager_module,
            "create_subagent_job_run",
            return_value={"id": "job_1"},
        ):
            response = client.post(
                "/projects/prj_contract/execute/run",
                json={"script": "printf 'noop'", "timeout_s": 10},
            )

        self.assertEqual(response.status_code, 502)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"detail"})
        self.assertEqual(set(payload["detail"].keys()), {"message", "status_code", "body"})
        self.assertEqual(payload["detail"]["message"], "subagent returned error response")


if __name__ == "__main__":
    unittest.main()
