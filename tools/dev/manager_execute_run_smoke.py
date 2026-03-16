import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def load_module(module_name: str, path: str):
    file_path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_subagent_runner():
    subagent_module = load_module("oldclaw_subagent_main_for_execute", "apps/subagent-runtime/src/main.py")
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def main() -> int:
    manager_module = load_module("oldclaw_manager_main_for_execute", "apps/manager-api/src/main.py")
    app = manager_module.create_app(subagent_runner=build_subagent_runner())
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "manager-execute-run-smoke",
            "request_text": "manager execute run smoke",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    plan_response = client.post(f"/projects/{project_id}/plan")
    plan_response.raise_for_status()

    run_response = client.post(
        f"/projects/{project_id}/execute/run",
        json={
            "script": "printf 'execute-run-ok'",
            "timeout_s": 10,
        },
    )
    run_response.raise_for_status()
    payload = run_response.json()

    evidence_response = client.get(f"/projects/{project_id}/evidence")
    evidence_response.raise_for_status()
    evidence_count = len(evidence_response.json().get("items", []))

    print("EXECUTE_RUN_PROJECT_ID:", project_id)
    print("EXECUTE_RUN_MANAGER_JOB_ID:", payload["execute_result"]["job_run"]["id"])
    print("EXECUTE_RUN_SUBAGENT_JOB_ID:", payload["job_run"]["id"])
    print("EXECUTE_RUN_PARENT_JOB_ID:", payload["job_run"]["parent_job_id"])
    print("EXECUTE_RUN_EXIT_CODE:", payload["subagent_result"]["detail"]["exit_code"])
    print("EXECUTE_RUN_EVIDENCE_COUNT:", evidence_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
