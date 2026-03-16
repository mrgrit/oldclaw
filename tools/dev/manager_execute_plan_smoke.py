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
                    "ast_plan",
                    "plan_asset",
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
                ("tgt_plan", "ast_plan", "http://plan-target.local", "ok"),
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
                    "pb_plan",
                    "1.0.0",
                    "nightly_health_baseline_check",
                    "ops",
                    "execute plan smoke playbook",
                    "one_shot",
                    "medium",
                ),
            )
        conn.commit()
    return ("ast_plan", "tgt_plan", "pb_plan")


def main() -> int:
    _, target_id, playbook_id = ensure_dummy_asset_target_playbook()

    manager_module = load_module("oldclaw_manager_main_for_plan", "apps/manager-api/src/main.py")
    app = manager_module.create_app()
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "manager-execute-plan-smoke",
            "request_text": "preview auto execution plan",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    client.post(f"/projects/{project_id}/targets/{target_id}").raise_for_status()
    client.post(f"/projects/{project_id}/playbooks/{playbook_id}").raise_for_status()

    plan_response = client.get(f"/projects/{project_id}/execute/plan")
    plan_response.raise_for_status()
    payload = plan_response.json()

    execution_plan = payload["execution_plan"]
    print("EXECUTE_PLAN_PROJECT_ID:", project_id)
    print("EXECUTE_PLAN_PLAYBOOK:", execution_plan["playbook"]["name"])
    print("EXECUTE_PLAN_TARGET:", execution_plan["target"]["endpoint"])
    print("EXECUTE_PLAN_SKILLS:", ",".join(execution_plan["manifest"]["required_skills"]))
    print("EXECUTE_PLAN_TOOLS:", ",".join(execution_plan["required_tools"]))
    print("EXECUTE_PLAN_SCRIPT_LINES:", len(execution_plan["script"].splitlines()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
