from packages.project_service import (
    create_minimal_evidence_record,
    create_project_record,
    execute_project_record,
    finalize_report_stage_record,
    get_project_report,
    plan_project_record,
    validate_project_record,
    get_evidence_for_project,
    close_project,
    get_project_report_evidence_summary,
)


def main() -> int:
    project = create_project_record(
        name="report-evidence-smoke",
        request_text="report evidence smoke",
        mode="one_shot",
    )
    project_id = project["id"]

    plan_project_record(project_id)
    execute_project_record(project_id)
    validated = validate_project_record(project_id)
    finalized = finalize_report_stage_record(project_id)
    evidence = create_minimal_evidence_record(
        project_id=project_id,
        command="echo OK",
        stdout="OK",
        stderr="",
        exit_code=0,
    )
    # Retrieve evidence list
    evidence_list = get_evidence_for_project(project_id)
    evidence_count = len(evidence_list)
    # Close project
    close_result = close_project(project_id)
    # Get summary (optional)
    summary = get_project_report_evidence_summary(project_id)

    print("PROJECT_ID:", project_id)
    print("VALIDATION_STATUS:", validated["validation_run"]["status"])
    print("FINAL_STAGE_BEFORE_CLOSE:", finalized["project"]["current_stage"])
    print("EVIDENCE_COUNT:", evidence_count)
    print("FINAL_STAGE_AFTER_CLOSE:", close_result["current_stage"])
    print("FINAL_STATUS_AFTER_CLOSE:", close_result["status"])
    print("LATEST_REPORT_ID:", summary["report"]["id"] if summary["report"] else "None")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
