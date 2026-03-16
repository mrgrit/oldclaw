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
    subagent_module = load_module("oldclaw_subagent_main_for_policy", "apps/subagent-runtime/src/main.py")
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def ensure_dummy_asset_target_playbook(playbook_id: str, playbook_name: str) -> tuple[str, str, str]:
    asset_id = f"ast_{playbook_id}"
    target_id = f"tgt_{playbook_id}"
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
                    f"{playbook_name}_asset",
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
                (target_id, asset_id, f"http://{playbook_name}.local", "ok"),
            )
            cur.execute(
                "SELECT id FROM playbooks WHERE name = %s AND version = %s",
                (playbook_name, "1.0.0"),
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
                        playbook_name,
                        "ops",
                        "policy gate smoke playbook",
                        "one_shot",
                        "medium",
                    ),
                )
                playbook_id = cur.fetchone()[0]
            else:
                playbook_id = row[0]
        conn.commit()
    return (asset_id, target_id, playbook_id)


def main() -> int:
    _, allow_target_id, allow_playbook_id = ensure_dummy_asset_target_playbook(
        "pb_policy_allow", "diagnose_web_latency"
    )
    _, deny_target_id, deny_playbook_id = ensure_dummy_asset_target_playbook(
        "pb_policy_deny", "onboard_new_linux_server"
    )

    manager_module = load_module("oldclaw_manager_main_for_policy", "apps/manager-api/src/main.py")
    app = manager_module.create_app(subagent_runner=build_subagent_runner())
    client = TestClient(app)

    allow_project = client.post(
        "/projects",
        json={"name": "policy-allow", "request_text": "policy allow", "mode": "one_shot"},
    ).json()["project"]["id"]
    client.post(f"/projects/{allow_project}/targets/{allow_target_id}").raise_for_status()
    client.post(f"/projects/{allow_project}/playbooks/{allow_playbook_id}").raise_for_status()
    allow_policy = client.get(f"/projects/{allow_project}/policy-check")
    allow_policy.raise_for_status()

    deny_project = client.post(
        "/projects",
        json={"name": "policy-deny", "request_text": "policy deny", "mode": "one_shot"},
    ).json()["project"]["id"]
    client.post(f"/projects/{deny_project}/targets/{deny_target_id}").raise_for_status()
    client.post(f"/projects/{deny_project}/playbooks/{deny_playbook_id}").raise_for_status()
    deny_policy = client.get(f"/projects/{deny_project}/policy-check")
    deny_policy.raise_for_status()
    deny_execute = client.post(f"/projects/{deny_project}/run/auto")

    print("POLICY_ALLOW_PROJECT_ID:", allow_project)
    print("POLICY_ALLOW_ALLOWED:", allow_policy.json()["policy"]["allowed"])
    print("POLICY_DENY_PROJECT_ID:", deny_project)
    print("POLICY_DENY_ALLOWED:", deny_policy.json()["policy"]["allowed"])
    print("POLICY_DENY_REQUIRES_APPROVAL:", deny_policy.json()["policy"]["requires_approval"])
    print("POLICY_DENY_EXECUTE_STATUS:", deny_execute.status_code)
    print("POLICY_DENY_APPROVAL_STATUS:", deny_execute.json()["detail"]["approval_request"]["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
