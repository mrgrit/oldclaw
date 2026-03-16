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
    subagent_module = load_module("oldclaw_subagent_main_for_failure", "apps/subagent-runtime/src/main.py")
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        return response.json()

    return runner


def main() -> int:
    manager_module = load_module("oldclaw_manager_main_for_failure", "apps/manager-api/src/main.py")
    app = manager_module.create_app(subagent_runner=build_subagent_runner())
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "manager-execute-failure-smoke",
            "request_text": "manager execute failure smoke",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    client.post(f"/projects/{project_id}/plan").raise_for_status()

    run_response = client.post(
        f"/projects/{project_id}/execute/run",
        json={
            "script": "printf 'execute-run-fail'; exit 7",
            "timeout_s": 10,
        },
    )
    run_response.raise_for_status()
    execute_payload = run_response.json()

    validate_response = client.post(f"/projects/{project_id}/validate")
    validate_response.raise_for_status()
    validated = validate_response.json()["result"]

    client.post(f"/projects/{project_id}/report/finalize").raise_for_status()
    client.post(f"/projects/{project_id}/close").raise_for_status()

    report_response = client.get(f"/projects/{project_id}/report")
    report_response.raise_for_status()
    report = report_response.json()["report"]

    evidence_response = client.get(f"/projects/{project_id}/evidence")
    evidence_response.raise_for_status()
    evidence = evidence_response.json()["items"]

    print("EXECUTE_FAILURE_PROJECT_ID:", project_id)
    print("EXECUTE_FAILURE_EXIT_CODE:", execute_payload["subagent_result"]["detail"]["exit_code"])
    print("EXECUTE_FAILURE_VALIDATE_STATUS:", validated["validation_run"]["status"])
    print("EXECUTE_FAILURE_REPORT_SUMMARY:", report["summary"])
    print("EXECUTE_FAILURE_EVIDENCE_COUNT:", len(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
