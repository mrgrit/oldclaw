from packages.project_service import create_project_record, close_project, get_project_record

def main() -> int:
    project = create_project_record(
        name="close-smoke-project",
        request_text="close smoke",
        mode="one_shot",
    )
    project_id = project["id"]
    # progress through stages
    from packages.project_service import plan_project_record, execute_project_record, validate_project_record, finalize_report_stage_record
    plan_project_record(project_id)
    execute_project_record(project_id)
    validate_project_record(project_id)
    finalize_report_stage_record(project_id)
    # now close
    closed = close_project(project_id)
    loaded = get_project_record(project_id)

    print("CLOSE_PROJECT_ID:", project_id)
    print("CLOSE_STATUS:", closed.get("status"))
    print("LOADED_STATUS:", loaded.get("status"))
    print("LOADED_STAGE:", loaded.get("current_stage"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
