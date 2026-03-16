import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

from packages.project_service import (
    create_project_record,
    execute_project_record,
    get_evidence_for_project,
    get_job_run_record,
    plan_project_record,
)


def load_subagent_module():
    file_path = Path("apps/subagent-runtime/src/main.py").resolve()
    spec = importlib.util.spec_from_file_location("oldclaw_subagent_main", file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    project = create_project_record(
        name="subagent-run-script-smoke",
        request_text="subagent runtime smoke",
        mode="one_shot",
    )
    project_id = project["id"]
    plan_project_record(project_id)
    executed = execute_project_record(project_id)
    job_run_id = executed["job_run"]["id"]

    module = load_subagent_module()
    app = module.create_app()
    client = TestClient(app)

    response = client.post(
        "/a2a/run_script",
        json={
            "project_id": project_id,
            "job_run_id": job_run_id,
            "script": "printf 'subagent-ok'",
            "timeout_s": 10,
        },
    )
    response.raise_for_status()
    payload = response.json()

    job_run = get_job_run_record(job_run_id)
    evidence = get_evidence_for_project(project_id)

    print("SUBAGENT_PROJECT_ID:", project_id)
    print("SUBAGENT_JOB_RUN_ID:", job_run_id)
    print("SUBAGENT_HTTP_STATUS:", payload["status"])
    print("SUBAGENT_EXIT_CODE:", payload["detail"]["exit_code"])
    print("SUBAGENT_JOB_STATUS:", job_run["status"])
    print("SUBAGENT_EVIDENCE_COUNT:", len(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
