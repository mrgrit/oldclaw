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
    subagent_module = load_module("oldclaw_subagent_main_for_master", "apps/subagent-runtime/src/main.py")
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def ensure_project_refs(playbook_name: str, suffix: str) -> tuple[str, str, str]:
    asset_id = f"ast_master_{suffix}"
    target_id = f"tgt_master_{suffix}"
    playbook_id = f"pb_master_{suffix}"
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
                    f"master_{suffix}_asset",
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
                (target_id, asset_id, f"http://master-{suffix}.local", "ok"),
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
                        "master review smoke playbook",
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
    _, allow_target_id, allow_playbook_id = ensure_project_refs("diagnose_web_latency", "allow")
    _, deny_target_id, deny_playbook_id = ensure_project_refs("onboard_new_linux_server", "deny")

    manager_module = load_module("oldclaw_manager_main_for_master", "apps/manager-api/src/main.py")
    manager_app = manager_module.create_app(subagent_runner=build_subagent_runner())
    manager = TestClient(manager_app)

    master_module = load_module("oldclaw_master_main_for_review", "apps/master-service/src/main.py")
    master = TestClient(master_module.create_app())

    allow_project = manager.post(
        "/projects",
        json={"name": "master-allow", "request_text": "master allow", "mode": "one_shot"},
    ).json()["project"]["id"]
    manager.post(f"/projects/{allow_project}/targets/{allow_target_id}").raise_for_status()
    manager.post(f"/projects/{allow_project}/playbooks/{allow_playbook_id}").raise_for_status()
    allow_run = manager.post(f"/projects/{allow_project}/run/auto")
    allow_run.raise_for_status()

    allow_review = master.post(
        f"/projects/{allow_project}/review",
        json={"project_id": allow_project, "reviewer_id": "master-reviewer", "comments": "final review"},
    )
    allow_review.raise_for_status()

    deny_project = manager.post(
        "/projects",
        json={"name": "master-deny", "request_text": "master deny", "mode": "one_shot"},
    ).json()["project"]["id"]
    manager.post(f"/projects/{deny_project}/targets/{deny_target_id}").raise_for_status()
    manager.post(f"/projects/{deny_project}/playbooks/{deny_playbook_id}").raise_for_status()
    manager.post(f"/projects/{deny_project}/run/auto")

    deny_review = master.post(
        f"/projects/{deny_project}/review",
        json={"project_id": deny_project, "reviewer_id": "master-reviewer", "comments": "approval pending"},
    )
    deny_review.raise_for_status()
    deny_replan = master.post(
        f"/projects/{deny_project}/replan",
        json={"reviewer_id": "master-reviewer", "comments": "need approval"},
    )
    deny_replan.raise_for_status()
    deny_escalate = master.post(
        f"/projects/{deny_project}/escalate",
        json={"reviewer_id": "master-reviewer", "level": 2, "reason": "approval still pending"},
    )
    deny_escalate.raise_for_status()

    print("MASTER_REVIEW_ALLOW_PROJECT_ID:", allow_project)
    print("MASTER_REVIEW_ALLOW_STATUS:", allow_review.json()["review"]["status"])
    print("MASTER_REVIEW_DENY_PROJECT_ID:", deny_project)
    print("MASTER_REVIEW_DENY_STATUS:", deny_review.json()["review"]["status"])
    print("MASTER_REVIEW_REPLAN_ACTIONS:", ",".join(deny_replan.json()["actions"]))
    print("MASTER_REVIEW_ESCALATE_LEVEL:", deny_escalate.json()["escalation_level"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
