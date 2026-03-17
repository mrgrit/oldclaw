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
    subagent_module = load_module("oldclaw_subagent_main_for_handoff", "apps/subagent-runtime/src/main.py")
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def build_master_runner():
    master_module = load_module("oldclaw_master_main_for_handoff", "apps/master-service/src/main.py")
    master_app = master_module.create_app()
    master_client = TestClient(master_app)

    def runner(project_id: str, payload: dict):
        response = master_client.post(f"/projects/{project_id}/review", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def ensure_project_refs() -> tuple[str, str, str]:
    asset_id = "ast_handoff"
    target_id = "tgt_handoff"
    playbook_id = "pb_handoff"
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
                    "handoff_asset",
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
                (target_id, asset_id, "http://handoff-target.local", "ok"),
            )
            cur.execute(
                "SELECT id FROM playbooks WHERE name = %s AND version = %s",
                ("diagnose_web_latency", "1.0.0"),
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
                        "diagnose_web_latency",
                        "ops",
                        "handoff smoke playbook",
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
    _, target_id, playbook_id = ensure_project_refs()

    manager_module = load_module("oldclaw_manager_main_for_handoff", "apps/manager-api/src/main.py")
    manager_app = manager_module.create_app(
        subagent_runner=build_subagent_runner(),
        master_runner=build_master_runner(),
    )
    client = TestClient(manager_app)

    create_response = client.post(
        "/projects",
        json={
            "name": "manager-run-auto-review-smoke",
            "request_text": "manager handoff smoke",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    project_id = create_response.json()["project"]["id"]

    client.post(f"/projects/{project_id}/targets/{target_id}").raise_for_status()
    client.post(f"/projects/{project_id}/playbooks/{playbook_id}").raise_for_status()

    run_response = client.post(
        f"/projects/{project_id}/run/auto/review",
        json={"reviewer_id": "master-reviewer", "comments": "auto handoff review"},
    )
    run_response.raise_for_status()
    payload = run_response.json()

    print("RUN_AUTO_REVIEW_PROJECT_ID:", project_id)
    print("RUN_AUTO_REVIEW_FINAL_STAGE:", payload["closed"]["current_stage"])
    print("RUN_AUTO_REVIEW_VALIDATION_STATUS:", payload["validated"]["validation_run"]["status"])
    print("RUN_AUTO_REVIEW_MASTER_STATUS:", payload["master_review"]["review"]["status"])
    print("RUN_AUTO_REVIEW_MASTER_EVIDENCE_COUNT:", payload["master_review"]["context"]["evidence_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
