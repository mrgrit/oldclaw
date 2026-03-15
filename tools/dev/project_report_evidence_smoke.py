from packages.project_service import (
    create_minimal_evidence_record,
    create_project_record,
    execute_project_record,
    finalize_report_stage_record,
    get_project_report,
    plan_project_record,
    validate_project_record,
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
    validate_project_record(project_id)
    finalized = finalize_report_stage_record(project_id)
    evidence = create_minimal_evidence_record(
        project_id=project_id,
        command="echo OK",
        stdout="OK",
        stderr="",
        exit_code=0,
    )
    report = get_project_report(project_id)

    print("PROJECT_ID:", project_id)
    print("FINAL_STAGE:", finalized["project"]["current_stage"])
    print("FINAL_REPORT_ID:", report["id"])
    print("EVIDENCE_ID:", evidence["id"])
    print("EVIDENCE_EXIT_CODE:", evidence["exit_code"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
