import os
import subprocess
import sys
import time
import unittest
from uuid import uuid4

import httpx

from tests.integration.support import ensure_refs


MANAGER_PORT = 18090
MASTER_PORT = 18091
SUBAGENT_PORT = 18092
MANAGER_URL = f"http://127.0.0.1:{MANAGER_PORT}"
MASTER_URL = f"http://127.0.0.1:{MASTER_PORT}"
SUBAGENT_URL = f"http://127.0.0.1:{SUBAGENT_PORT}"


def wait_for_health(base_url: str, timeout_s: int = 20) -> dict:
    started_at = time.time()
    last_error = None
    while time.time() - started_at < timeout_s:
        try:
            response = httpx.get(f"{base_url}/health", timeout=3.0)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"health check failed for {base_url}: {last_error}")


class HttpServiceFlowE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = os.environ.copy()
        env["OLDCLAW_SUBAGENT_URL"] = SUBAGENT_URL
        env["OLDCLAW_MASTER_URL"] = MASTER_URL
        cls.processes = [
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "--app-dir",
                    "apps/subagent-runtime/src",
                    "main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(SUBAGENT_PORT),
                ],
                cwd="/home/oldclaw/oldclaw",
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            ),
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "--app-dir",
                    "apps/master-service/src",
                    "main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(MASTER_PORT),
                ],
                cwd="/home/oldclaw/oldclaw",
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            ),
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "--app-dir",
                    "apps/manager-api/src",
                    "main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(MANAGER_PORT),
                ],
                cwd="/home/oldclaw/oldclaw",
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            ),
        ]
        wait_for_health(SUBAGENT_URL)
        wait_for_health(MASTER_URL)
        wait_for_health(MANAGER_URL)

    @classmethod
    def tearDownClass(cls) -> None:
        for process in getattr(cls, "processes", []):
            process.terminate()
        for process in getattr(cls, "processes", []):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    def create_project(self, *, name: str, request_text: str, mode: str = "one_shot") -> str:
        response = httpx.post(
            f"{MANAGER_URL}/projects",
            json={"name": name, "request_text": request_text, "mode": mode},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()["project"]["id"]

    def link_refs(self, project_id: str, target_id: str, playbook_id: str) -> None:
        target_response = httpx.post(
            f"{MANAGER_URL}/projects/{project_id}/targets/{target_id}",
            timeout=10.0,
        )
        target_response.raise_for_status()
        playbook_response = httpx.post(
            f"{MANAGER_URL}/projects/{project_id}/playbooks/{playbook_id}",
            timeout=10.0,
        )
        playbook_response.raise_for_status()

    def create_linked_project(
        self,
        *,
        prefix: str,
        playbook_name: str,
        request_text: str,
        mode: str = "one_shot",
    ) -> str:
        _, target_id, playbook_id = ensure_refs(playbook_name, prefix)
        project_id = self.create_project(
            name=f"project-{prefix}",
            request_text=request_text,
            mode=mode,
        )
        self.link_refs(project_id, target_id, playbook_id)
        return project_id

    def test_run_auto_over_http_reaches_close(self):
        prefix = f"e2eok_{uuid4().hex[:8]}"
        project_id = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="e2e run auto over http",
        )

        response = httpx.post(f"{MANAGER_URL}/projects/{project_id}/run/auto", timeout=30.0)
        response.raise_for_status()
        payload = response.json()

        self.assertEqual(payload["validated"]["validation_run"]["status"], "passed")
        self.assertEqual(payload["closed"]["current_stage"], "close")
        self.assertEqual(payload["subagent_result"]["detail"]["exit_code"], 0)

        report_response = httpx.get(f"{MANAGER_URL}/projects/{project_id}/report", timeout=10.0)
        report_response.raise_for_status()
        report = report_response.json()["report"]
        self.assertIn("diagnose_web_latency", report["summary"])

    def test_run_auto_over_http_returns_approval_required_for_sensitive_playbook(self):
        prefix = f"e2edeny_{uuid4().hex[:8]}"
        project_id = self.create_linked_project(
            prefix=prefix,
            playbook_name="onboard_new_linux_server",
            request_text="e2e approval denial over http",
        )

        response = httpx.post(f"{MANAGER_URL}/projects/{project_id}/run/auto", timeout=15.0)
        self.assertEqual(response.status_code, 403)
        payload = response.json()["detail"]

        self.assertEqual(payload["policy"]["policy_name"], "sensitive_playbook_requires_approval")
        self.assertEqual(payload["approval_request"]["status"], "approval_required")

    def test_run_auto_review_over_http_reaches_master_approval(self):
        prefix = f"e2ereview_{uuid4().hex[:8]}"
        project_id = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="e2e run auto review over http",
        )

        response = httpx.post(
            f"{MANAGER_URL}/projects/{project_id}/run/auto/review",
            json={"reviewer_id": "e2e-master", "comments": "http handoff"},
            timeout=35.0,
        )
        response.raise_for_status()
        payload = response.json()

        self.assertEqual(payload["closed"]["current_stage"], "close")
        self.assertEqual(payload["validated"]["validation_run"]["status"], "passed")
        self.assertEqual(payload["master_review"]["review"]["status"], "approved")
        self.assertGreaterEqual(payload["master_review"]["context"]["evidence_count"], 1)

    def test_sensitive_playbook_can_rerun_over_http_after_approval(self):
        prefix = f"e2eapprove_{uuid4().hex[:8]}"
        project_id = self.create_linked_project(
            prefix=prefix,
            playbook_name="onboard_new_linux_server",
            request_text="e2e approval rerun over http",
        )

        denied = httpx.post(f"{MANAGER_URL}/projects/{project_id}/run/auto", timeout=15.0)
        self.assertEqual(denied.status_code, 403)
        approval_id = denied.json()["detail"]["approval_request"]["approval_id"]

        approve_response = httpx.post(
            f"{MANAGER_URL}/projects/{project_id}/approvals/{approval_id}/approve",
            json={"approver_id": "e2e-reviewer"},
            timeout=10.0,
        )
        approve_response.raise_for_status()
        self.assertEqual(approve_response.json()["approval"]["status"], "approved")

        rerun = httpx.post(f"{MANAGER_URL}/projects/{project_id}/run/auto", timeout=35.0)
        rerun.raise_for_status()
        payload = rerun.json()

        self.assertEqual(payload["policy"]["approval_status"], "approved")
        self.assertEqual(payload["closed"]["current_stage"], "close")

    def test_execute_run_failure_then_validate_failed_over_http(self):
        prefix = f"e2efail_{uuid4().hex[:8]}"
        project_id = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="e2e execute failure over http",
        )

        plan_response = httpx.post(f"{MANAGER_URL}/projects/{project_id}/plan", timeout=10.0)
        plan_response.raise_for_status()

        execute_response = httpx.post(
            f"{MANAGER_URL}/projects/{project_id}/execute/run",
            json={
                "script": "printf 'e2e execute failure\\n'; exit 7",
                "timeout_s": 10,
            },
            timeout=20.0,
        )
        execute_response.raise_for_status()
        execute_payload = execute_response.json()
        self.assertEqual(execute_payload["subagent_result"]["detail"]["exit_code"], 7)

        validate_response = httpx.post(
            f"{MANAGER_URL}/projects/{project_id}/validate",
            timeout=10.0,
        )
        validate_response.raise_for_status()
        validate_payload = validate_response.json()["result"]

        self.assertEqual(validate_payload["validation_run"]["status"], "failed")
        self.assertEqual(
            validate_payload["validation_run"]["actual_result"]["failing_evidence_count"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
