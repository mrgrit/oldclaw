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

    # GET targets
    targets_resp = client.get("/targets")
    targets_resp.raise_for_status()
    targets = targets_resp.json().get("items", [])
    target_count = len(targets)
    if target_count == 0:
        raise SystemExit(1)
    target_id = targets[0]["id"]

    # create project
    create_resp = client.post(
        "/projects",
        json={"name": "target-http", "request_text": "target http", "mode": "one_shot"},
    )
    create_resp.raise_for_status()
    project_id = create_resp.json()["project"]["id"]

    # link target
    link_resp = client.post(f"/targets/{project_id}/targets/{target_id}")
    link_resp.raise_for_status()

    # get project targets
    proj_targets_resp = client.get(f"/targets/{project_id}/targets")
    proj_targets_resp.raise_for_status()
    proj_targets = proj_targets_resp.json().get("items", [])
    proj_target_count = len(proj_targets)

    print("HTTP_TARGET_COUNT:", target_count)
    print("HTTP_PROJECT_ID:", project_id)
    print("HTTP_LINKED_TARGET_ID:", target_id)
    print("HTTP_PROJECT_TARGET_COUNT:", proj_target_count)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
