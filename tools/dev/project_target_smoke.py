from packages.project_service import (
    get_targets,
    create_project_record,
    link_target_to_project,
    get_project_targets,
    get_project_report_evidence_summary,
)


def main() -> int:
    # 1. target list
    targets = get_targets()
    target_count = len(targets)
    if target_count == 0:
        # insert dummy target (requires an existing asset)
        # Ensure there is at least one asset
        from packages.project_service import get_assets, get_connection
        assets = get_assets()
        if not assets:
            # create dummy asset
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO assets (id, name, type, platform, env, mgmt_ip, roles, subagent_status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            'ast_dummy',
                            'dummy_asset',
                            'dummy_type',
                            'dummy_platform',
                            'dev',
                            '127.0.0.1',
                            '[]',
                            'unknown',
                        ),
                    )
                    conn.commit()
            assets = get_assets()
        asset_id = assets[0]["id"]
        # create dummy target linked to asset
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO targets (id, asset_id, base_url, resolved_at, health, metadata)
                    VALUES (%s, %s, %s, NOW(), %s, '{}'::jsonb)
                    ON CONFLICT DO NOTHING
                    """,
                    ('tgt_dummy', asset_id, 'http://dummy', 'unknown'),
                )
                conn.commit()
        targets = get_targets()
    first_target = targets[0]
    target_id = first_target["id"]

    # 2. create project
    project = create_project_record(name='target-smoke', request_text='target smoke', mode='one_shot')
    project_id = project['id']

    # 3. link target to project
    link_target_to_project(project_id, target_id)

    # 4. get linked targets
    linked = get_project_targets(project_id)
    linked_count = len(linked)

    # 5. summary includes targets
    summary = get_project_report_evidence_summary(project_id)
    summary_target_count = len(summary.get('targets', []))

    print('TARGET_COUNT:', len(targets))
    print('PROJECT_ID:', project_id)
    print('LINKED_TARGET_ID:', target_id)
    print('PROJECT_TARGET_COUNT:', linked_count)
    print('SUMMARY_TARGET_COUNT:', summary_target_count)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
