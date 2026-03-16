import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

from packages.project_service import get_connection


def load_module(module_name: str, path: str):
    file_path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_subagent_runner():
    subagent_module = load_module("oldclaw_subagent_main_for_run_auto", "apps/subagent-runtime/src/main.py")
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def ensure_dummy_asset_target_playbook() -> tuple[str, str, str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO assets (
                    id, name, type, platform, env, mgmt_ip, roles,
                    subagent_status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, NOW(), NOW()
                )
                ON CONFLICT DO NOTHING
                """,
                (
                    "ast_run_auto",
                    "run_auto_asset",
                    "linux_host",
                    "linux",
                    "dev",
                    "127.0.0.1",
                    "[]",
                    "healthy",
                ),
            )
            cur.execute(
                """
                INSERT INTO targets (
                    id, asset_id, base_url, resolved_at, health, metadata
                ) VALUES (
                    %s, %s, %s, NOW(), %s, '{}'::jsonb
                )
                ON CONFLICT DO NOTHING
                """,
                ("tgt_run_auto", "ast_run_auto", "http://run-auto-target.local", "ok"),
            )
            cur.execute(
                "SELECT id FROM playbooks WHERE name = %s AND version = %s",
                ("diagnose_web_latency", "1.0.0"),
            )
            row = cur.fetchone()
            playbook_id = row[0] if row is not None else "pb_run_auto"
            if row is None:
                cur.execute(
                    """
                    INSERT INTO playbooks (
                        id, version, name, category, description, execution_mode,
                        default_risk_level, input_schema_ref, output_schema_ref,
                        dry_run_supported, explain_supported, required_asset_roles,
                        failure_policy, policy_bindings, enabled, metadata, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, NULL, NULL,
                        false, false, '[]'::jsonb,
                        '{}'::jsonb, '[]'::jsonb, true, '{}'::jsonb, NOW()
                    )
                    RETURNING id
                    """,
                    (
                        playbook_id,
                        "1.0.0",
                        "diagnose_web_latency",
                        "ops",
                        "run auto smoke playbook",
                        "one_shot",
                        "medium",
                    ),
                )
                playbook_id = cur.fetchone()[0]
        conn.commit()
    return ("ast_run_auto", "tgt_run_auto", playbook_id)


def main() -> int:
    _, target_id, playbook_id = ensure_dummy_asset_target_playbook()

    manager_module = load_module("oldclaw_manager_main_for_run_auto", "apps/manager-api/src/main.py")
    app = manager_module.create_app(subagent_runner=build_subagent_runner())
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "manager-run-auto-smoke",
            "request_text": "run project end to end",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    client.post(f"/projects/{project_id}/targets/{target_id}").raise_for_status()
    client.post(f"/projects/{project_id}/playbooks/{playbook_id}").raise_for_status()

    run_response = client.post(f"/projects/{project_id}/run/auto")
    run_response.raise_for_status()
    payload = run_response.json()

    final_project_response = client.get(f"/projects/{project_id}")
    final_project_response.raise_for_status()
    final_project = final_project_response.json()["project"]

    report_response = client.get(f"/projects/{project_id}/report")
    report_response.raise_for_status()
    report = report_response.json()["report"]

    evidence_response = client.get(f"/projects/{project_id}/evidence")
    evidence_response.raise_for_status()
    evidence_count = len(evidence_response.json().get("items", []))

    print("RUN_AUTO_PROJECT_ID:", project_id)
    print("RUN_AUTO_PLAYBOOK:", payload["execution_plan"]["playbook"]["name"])
    print("RUN_AUTO_REQUIRED_SKILLS:", ",".join(payload["execution_plan"]["manifest"]["required_skills"]))
    print("RUN_AUTO_SKILL_EVIDENCE_COUNT:", len(payload["skill_evidence"]))
    print("RUN_AUTO_VALIDATION_STATUS:", payload["validated"]["validation_run"]["status"])
    print("RUN_AUTO_EXIT_CODE:", payload["subagent_result"]["detail"]["exit_code"])
    print("RUN_AUTO_FINAL_STAGE:", final_project["current_stage"])
    print("RUN_AUTO_FINAL_STATUS:", final_project["status"])
    print("RUN_AUTO_REPORT_SUMMARY:", report["summary"])
    print("RUN_AUTO_EVIDENCE_COUNT:", evidence_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
