from packages.project_service import (
    create_project_record,
    plan_project_record,
    execute_project_record,
    validate_project_record,
    get_project_record,
    get_project_report,
)


def main() -> int:
    project = create_project_record(
        name="smoke-project",
        request_text="run smoke",
        mode="one_shot",
    )
    project_id = project["id"]
    # initial get
    loaded = get_project_record(project_id)
    # plan stage
    planned = plan_project_record(project_id)
    # execute stage
    executed = execute_project_record(project_id)
    # validate stage
    validated = validate_project_record(project_id)
    # final report
    report = get_project_report(project_id)

    print("PROJECT_ID:", project_id)
    print("PROJECT_STATUS:", loaded["status"])
    print("PLAN_STAGE:", planned["current_stage"])
    print("EXECUTE_STAGE:", executed["project"]["current_stage"])
    print("VALIDATE_STAGE:", validated["project"]["current_stage"])
    print("REPORT_ID:", report["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
