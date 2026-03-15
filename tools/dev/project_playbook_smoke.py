from packages.project_service import (
    create_project_record,
    get_connection,
    get_playbooks,
    get_project_playbooks,
    get_project_report_evidence_summary,
    link_playbook_to_project,
)


def ensure_dummy_playbook() -> str:
    playbooks = get_playbooks()
    if playbooks:
        return playbooks[0]["id"]

    with get_connection() as conn:
        with conn.cursor() as cur:
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
                ON CONFLICT DO NOTHING
                """,
                (
                    "pb_dummy",
                    "1.0.0",
                    "dummy-playbook",
                    "test",
                    "dummy playbook for smoke",
                    "one_shot",
                    "medium",
                ),
            )
        conn.commit()

    return "pb_dummy"


def main() -> int:
    playbook_id = ensure_dummy_playbook()
    playbooks = get_playbooks()
    playbook_count = len(playbooks)

    project = create_project_record(
        name="playbook-smoke",
        request_text="playbook smoke",
        mode="one_shot",
    )
    project_id = project["id"]

    link_playbook_to_project(project_id, playbook_id)

    linked = get_project_playbooks(project_id)
    summary = get_project_report_evidence_summary(project_id)

    print("PLAYBOOK_COUNT:", playbook_count)
    print("PROJECT_ID:", project_id)
    print("LINKED_PLAYBOOK_ID:", playbook_id)
    print("PROJECT_PLAYBOOK_COUNT:", len(linked))
    print("SUMMARY_PLAYBOOK_COUNT:", len(summary.get("playbooks", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
