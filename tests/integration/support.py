import importlib.util
import unittest
from pathlib import Path
from uuid import uuid4

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
    subagent_module = load_module(
        f"oldclaw_subagent_test_{uuid4().hex}",
        "apps/subagent-runtime/src/main.py",
    )
    subagent_app = subagent_module.create_app()
    subagent_client = TestClient(subagent_app)

    def runner(payload: dict):
        response = subagent_client.post("/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def build_master_runner():
    master_module = load_module(
        f"oldclaw_master_test_{uuid4().hex}",
        "apps/master-service/src/main.py",
    )
    master_app = master_module.create_app()
    master_client = TestClient(master_app)

    def runner(project_id: str, payload: dict):
        response = master_client.post(f"/projects/{project_id}/review", json=payload)
        response.raise_for_status()
        return response.json()

    return runner


def build_manager_client() -> TestClient:
    manager_module = load_module(
        f"oldclaw_manager_test_{uuid4().hex}",
        "apps/manager-api/src/main.py",
    )
    scheduler_module = load_module(
        f"oldclaw_scheduler_test_{uuid4().hex}",
        "apps/scheduler-worker/src/main.py",
    )
    watch_module = load_module(
        f"oldclaw_watch_test_{uuid4().hex}",
        "apps/watch-worker/src/main.py",
    )
    scheduler_client = TestClient(scheduler_module.create_app())
    watch_client = TestClient(watch_module.create_app())

    def scheduler_runner():
        response = scheduler_client.post("/run-once")
        response.raise_for_status()
        return response.json()

    def watch_runner():
        response = watch_client.post("/run-once")
        response.raise_for_status()
        return response.json()

    return TestClient(
        manager_module.create_app(
            subagent_runner=build_subagent_runner(),
            master_runner=build_master_runner(),
            scheduler_runner=scheduler_runner,
            watch_runner=watch_runner,
        )
    )


def ensure_refs(playbook_name: str, prefix: str) -> tuple[str, str, str]:
    asset_id = f"ast_{prefix}"
    target_id = f"tgt_{prefix}"
    playbook_id = f"pb_{prefix}"
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
                    f"{prefix}_asset",
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
                (target_id, asset_id, f"http://{prefix}.local", "ok"),
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
                        "integration test playbook",
                        "one_shot",
                        "medium",
                    ),
                )
                playbook_id = cur.fetchone()[0]
            else:
                playbook_id = row[0]
        conn.commit()
    return asset_id, target_id, playbook_id


class ManagerIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = build_manager_client()

    def create_project(self, name: str, request_text: str, mode: str = "one_shot") -> str:
        response = self.client.post(
            "/projects",
            json={"name": name, "request_text": request_text, "mode": mode},
        )
        response.raise_for_status()
        return response.json()["project"]["id"]

    def link_refs(self, project_id: str, target_id: str, playbook_id: str) -> None:
        self.client.post(f"/projects/{project_id}/targets/{target_id}").raise_for_status()
        self.client.post(f"/projects/{project_id}/playbooks/{playbook_id}").raise_for_status()

    def create_linked_project(
        self,
        *,
        prefix: str,
        playbook_name: str,
        request_text: str,
        mode: str = "one_shot",
    ) -> tuple[str, str, str, str]:
        _, target_id, playbook_id = ensure_refs(playbook_name, prefix)
        project_id = self.create_project(
            name=f"project-{prefix}",
            request_text=request_text,
            mode=mode,
        )
        self.link_refs(project_id, target_id, playbook_id)
        return project_id, target_id, playbook_id, prefix
