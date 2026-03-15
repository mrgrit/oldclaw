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

    playbooks_resp = client.get("/playbooks")
    playbooks_resp.raise_for_status()
    playbooks = playbooks_resp.json().get("items", [])
    if not playbooks:
        raise SystemExit(1)
    playbook_id = playbooks[0]["id"]

    create_resp = client.post(
        "/projects",
        json={"name": "playbook-http", "request_text": "playbook http", "mode": "one_shot"},
    )
    create_resp.raise_for_status()
    project_id = create_resp.json()["project"]["id"]

    link_resp = client.post(f"/projects/{project_id}/playbooks/{playbook_id}")
    link_resp.raise_for_status()

    proj_playbooks_resp = client.get(f"/projects/{project_id}/playbooks")
    proj_playbooks_resp.raise_for_status()
    proj_playbooks = proj_playbooks_resp.json().get("items", [])

    print("HTTP_PLAYBOOK_COUNT:", len(playbooks))
    print("HTTP_PROJECT_ID:", project_id)
    print("HTTP_LINKED_PLAYBOOK_ID:", playbook_id)
    print("HTTP_PROJECT_PLAYBOOK_COUNT:", len(proj_playbooks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
