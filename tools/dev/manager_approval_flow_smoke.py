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
    subagent_module = load_module("oldclaw_subagent_main_for_approval", "apps/subagent-runtime/src/main.py")
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def ensure_sensitive_project_refs() -> tuple[str, str, str]:
    asset_id = "ast_approval_flow"
    target_id = "tgt_approval_flow"
    playbook_id = "pb_approval_flow"
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
                    asset_id,
                    "approval_flow_asset",
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
                (target_id, asset_id, "http://approval-target.local", "ok"),
            )
            cur.execute(
                "SELECT id FROM playbooks WHERE name = %s AND version = %s",
                ("onboard_new_linux_server", "1.0.0"),
            )
            row = cur.fetchone()
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
                        "onboard_new_linux_server",
                        "ops",
                        "approval flow smoke playbook",
                        "one_shot",
                        "medium",
                    ),
                )
                playbook_id = cur.fetchone()[0]
            else:
                playbook_id = row[0]
        conn.commit()
    return asset_id, target_id, playbook_id


def main() -> int:
    _, target_id, playbook_id = ensure_sensitive_project_refs()

    manager_module = load_module("oldclaw_manager_main_for_approval", "apps/manager-api/src/main.py")
    app = manager_module.create_app(subagent_runner=build_subagent_runner())
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "manager-approval-flow-smoke",
            "request_text": "approval flow smoke",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    client.post(f"/projects/{project_id}/targets/{target_id}").raise_for_status()
    client.post(f"/projects/{project_id}/playbooks/{playbook_id}").raise_for_status()

    denied_run = client.post(f"/projects/{project_id}/run/auto")
    approval_id = denied_run.json()["detail"]["approval_request"]["approval_id"]

    approvals_response = client.get(f"/projects/{project_id}/approvals")
    approvals_response.raise_for_status()
    approvals = approvals_response.json()["items"]

    approve_response = client.post(
        f"/projects/{project_id}/approvals/{approval_id}/approve",
        json={"approver_id": "ops-reviewer"},
    )
    approve_response.raise_for_status()

    rerun_response = client.post(f"/projects/{project_id}/run/auto")
    rerun_response.raise_for_status()
    rerun_payload = rerun_response.json()

    print("APPROVAL_FLOW_PROJECT_ID:", project_id)
    print("APPROVAL_FLOW_DENY_STATUS:", denied_run.status_code)
    print("APPROVAL_FLOW_APPROVAL_COUNT:", len(approvals))
    print("APPROVAL_FLOW_APPROVAL_ID:", approval_id)
    print("APPROVAL_FLOW_APPROVED_STATUS:", approve_response.json()["approval"]["status"])
    print("APPROVAL_FLOW_POLICY_REASON:", rerun_payload["policy"]["reason"])
    print("APPROVAL_FLOW_FINAL_STAGE:", rerun_payload["closed"]["current_stage"])
    print("APPROVAL_FLOW_FINAL_STATUS:", rerun_payload["closed"]["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
