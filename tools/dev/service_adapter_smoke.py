from apps.manager_api import create_app as create_manager_app
from apps.master_service import create_app as create_master_app
from apps.subagent_runtime import create_app as create_subagent_app


def main() -> int:
    manager_app = create_manager_app()
    master_app = create_master_app()
    subagent_app = create_subagent_app()

    print("MANAGER_TITLE:", manager_app.title)
    print("MASTER_TITLE:", master_app.title)
    print("SUBAGENT_TITLE:", subagent_app.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
