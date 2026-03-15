from packages.project_service import (
    create_project_record,
    get_assets,
    get_connection,
    get_playbooks,
    get_project_report_evidence_summary,
    get_targets,
    link_asset_to_project,
    link_playbook_to_project,
    link_target_to_project,
)


def ensure_dummy_asset() -> str:
    assets = get_assets()
    if assets:
        return assets[0]["id"]

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
                    "ast_dummy",
                    "dummy_asset",
                    "dummy_type",
                    "dummy_platform",
                    "dev",
                    "127.0.0.1",
                    "[]",
                    "unknown",
                ),
            )
        conn.commit()

    return "ast_dummy"


def ensure_dummy_target(asset_id: str) -> str:
    targets = get_targets()
    if targets:
        return targets[0]["id"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO targets (
                    id, asset_id, base_url, resolved_at, health, metadata
                ) VALUES (
                    %s, %s, %s, NOW(), %s, '{}'::jsonb
                )
                ON CONFLICT DO NOTHING
                """,
                ("tgt_dummy", asset_id, "http://dummy", "unknown"),
            )
        conn.commit()

    return "tgt_dummy"


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
    asset_id = ensure_dummy_asset()
    target_id = ensure_dummy_target(asset_id)
    playbook_id = ensure_dummy_playbook()

    assets = get_assets()
    targets = get_targets()
    playbooks = get_playbooks()

    project = create_project_record(
        name="m3-integrated",
        request_text="m3 integrated smoke",
        mode="one_shot",
    )
    project_id = project["id"]

    link_asset_to_project(project_id, asset_id)
    link_target_to_project(project_id, target_id)
    link_playbook_to_project(project_id, playbook_id)

    summary = get_project_report_evidence_summary(project_id)

    print("M3_PROJECT_ID:", project_id)
    print("M3_ASSET_COUNT:", len(assets))
    print("M3_TARGET_COUNT:", len(targets))
    print("M3_PLAYBOOK_COUNT:", len(playbooks))
    print("M3_LINKED_ASSET_ID:", asset_id)
    print("M3_LINKED_TARGET_ID:", target_id)
    print("M3_LINKED_PLAYBOOK_ID:", playbook_id)
    print("M3_SUMMARY_ASSET_COUNT:", len(summary.get("assets", [])))
    print("M3_SUMMARY_TARGET_COUNT:", len(summary.get("targets", [])))
    print("M3_SUMMARY_PLAYBOOK_COUNT:", len(summary.get("playbooks", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
