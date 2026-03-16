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
    subagent_module = load_module("oldclaw_subagent_main_for_auto", "apps/subagent-runtime/src/main.py")
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
                    "ast_auto",
                    "auto_asset",
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
                ("tgt_auto", "ast_auto", "http://auto-target.local", "ok"),
            )
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
                ON CONFLICT DO NOTHING
                """,
                (
                    "pb_auto",
                    "1.0.0",
                    "diagnose_web_latency",
                    "ops",
                    "auto execution smoke playbook",
                    "one_shot",
                    "medium",
                ),
            )
        conn.commit()
    return ("ast_auto", "tgt_auto", "pb_auto")


def main() -> int:
    _, target_id, playbook_id = ensure_dummy_asset_target_playbook()

    manager_module = load_module("oldclaw_manager_main_for_auto", "apps/manager-api/src/main.py")
    app = manager_module.create_app(subagent_runner=build_subagent_runner())
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "manager-execute-auto-smoke",
            "request_text": "run auto execution path",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    client.post(f"/projects/{project_id}/targets/{target_id}").raise_for_status()
    client.post(f"/projects/{project_id}/playbooks/{playbook_id}").raise_for_status()
    client.post(f"/projects/{project_id}/plan").raise_for_status()

    auto_response = client.post(f"/projects/{project_id}/execute/auto")
    auto_response.raise_for_status()
    payload = auto_response.json()

    evidence_response = client.get(f"/projects/{project_id}/evidence")
    evidence_response.raise_for_status()
    evidence_count = len(evidence_response.json().get("items", []))

    print("EXECUTE_AUTO_PROJECT_ID:", project_id)
    print("EXECUTE_AUTO_TARGET_ID:", target_id)
    print("EXECUTE_AUTO_PLAYBOOK_ID:", playbook_id)
    print("EXECUTE_AUTO_PARENT_JOB_ID:", payload["job_run"]["parent_job_id"])
    print("EXECUTE_AUTO_EXIT_CODE:", payload["subagent_result"]["detail"]["exit_code"])
    print("EXECUTE_AUTO_REQUIRED_SKILLS:", ",".join(payload["execution_plan"]["manifest"]["required_skills"]))
    print("EXECUTE_AUTO_REQUIRED_TOOLS:", ",".join(payload["execution_plan"]["required_tools"]))
    print("EXECUTE_AUTO_RESOLVED_SKILL_COUNT:", len(payload["execution_plan"]["resolved_skills"]))
    print("EXECUTE_AUTO_SKILL_EVIDENCE_COUNT:", len(payload["skill_evidence"]))
    print("EXECUTE_AUTO_SCRIPT_LINES:", len(payload["execution_plan"]["script"].splitlines()))
    print("EXECUTE_AUTO_SCRIPT_TEXT:", payload["execution_plan"]["script"].replace("\n", " | "))
    print("EXECUTE_AUTO_STDOUT:", payload["subagent_result"]["detail"]["stdout"].replace("\n", " | "))
    print("EXECUTE_AUTO_EVIDENCE_COUNT:", evidence_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
