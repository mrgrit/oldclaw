import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def load_manager_module():
    file_path = Path("apps/manager-api/src/main.py").resolve()
    spec = importlib.util.spec_from_file_location("oldclaw_manager_main", file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_manager_module()
    app = module.create_app()
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "report-http-project",
            "request_text": "report http smoke",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    client.post(f"/projects/{project_id}/plan").raise_for_status()
    client.post(f"/projects/{project_id}/execute").raise_for_status()
    client.post(f"/projects/{project_id}/validate").raise_for_status()

    finalize_response = client.post(f"/projects/{project_id}/report/finalize")
    finalize_response.raise_for_status()
    finalized = finalize_response.json()

    evidence_response = client.post(
        f"/projects/{project_id}/evidence/minimal",
        json={
            "command": "echo OK",
            "stdout": "OK",
            "stderr": "",
            "exit_code": 0,
        },
    )
    evidence_response.raise_for_status()
    evidence = evidence_response.json()

    report_response = client.get(f"/projects/{project_id}/report")
    report_response.raise_for_status()
    report = report_response.json()

    print("HTTP_PROJECT_ID:", project_id)
    print("HTTP_FINAL_STAGE:", finalized["result"]["project"]["current_stage"])
    print("HTTP_EVIDENCE_ID:", evidence["evidence"]["id"])
    print("HTTP_REPORT_ID:", report["report"]["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
