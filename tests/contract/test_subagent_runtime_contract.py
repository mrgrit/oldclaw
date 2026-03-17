import subprocess
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.integration.support import load_module


subagent_module = load_module(
    "oldclaw_subagent_contract",
    "apps/subagent-runtime/src/main.py",
)


class SubagentRuntimeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(subagent_module.create_app())

    def test_capabilities_response_shape(self):
        response = self.client.get("/capabilities")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"service", "capabilities", "note"})
        self.assertIsInstance(payload["capabilities"], list)

    def test_run_script_response_shape(self):
        completed = subprocess.CompletedProcess(
            args=["/bin/bash", "-lc", "printf 'ok'"],
            returncode=0,
            stdout="ok\n",
            stderr="",
        )
        recorded = {
            "job_run": {"id": "job_1", "status": "completed"},
            "evidence": {"id": "ev_1", "exit_code": 0},
        }
        with patch.object(subagent_module.subprocess, "run", return_value=completed), patch.object(
            subagent_module, "record_subagent_execution_result", return_value=recorded
        ):
            response = self.client.post(
                "/a2a/run_script",
                json={
                    "project_id": "prj_contract",
                    "job_run_id": "job_1",
                    "script": "printf 'ok'",
                    "timeout_s": 10,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"status", "detail"})
        self.assertEqual(
            set(payload["detail"].keys()),
            {"project_id", "job_run_id", "command", "stdout", "stderr", "exit_code", "job_run", "evidence"},
        )

    def test_run_script_timeout_error_shape(self):
        timeout_exc = subprocess.TimeoutExpired(
            cmd=["/bin/bash", "-lc", "sleep 999"],
            timeout=3,
            output="partial stdout",
            stderr="partial stderr",
        )
        recorded = {
            "job_run": {"id": "job_1", "status": "failed"},
            "evidence": {"id": "ev_1", "exit_code": 124},
        }
        with patch.object(subagent_module.subprocess, "run", side_effect=timeout_exc), patch.object(
            subagent_module, "record_subagent_execution_result", return_value=recorded
        ):
            response = self.client.post(
                "/a2a/run_script",
                json={
                    "project_id": "prj_contract",
                    "job_run_id": "job_1",
                    "script": "sleep 999",
                    "timeout_s": 3,
                },
            )

        self.assertEqual(response.status_code, 504)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"detail"})
        self.assertEqual(
            set(payload["detail"].keys()),
            {"message", "project_id", "job_run_id", "timeout_s", "job_run", "evidence"},
        )
        self.assertEqual(payload["detail"]["message"], "script execution timed out")


if __name__ == "__main__":
    unittest.main()
