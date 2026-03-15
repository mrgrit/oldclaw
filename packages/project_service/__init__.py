import os
import uuid
from dataclasses import dataclass
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from packages.graph_runtime import GraphRuntimeError, require_transition

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw",
)


class ProjectServiceError(Exception):
    pass


class ProjectNotFoundError(ProjectServiceError):
    pass


class ProjectStageError(ProjectServiceError):
    pass


@dataclass(frozen=True)
class ProjectServiceConfig:
    database_url: str = DEFAULT_DATABASE_URL


def get_connection(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def create_project_record(
    name: str,
    request_text: str,
    mode: str = "one_shot",
    database_url: str | None = None,
) -> dict[str, Any]:
    project_id = f"prj_{uuid.uuid4().hex[:12]}"
    sql = """
    INSERT INTO projects (
        id, name, request_text, requester_type, status, current_stage,
        mode, priority, risk_level, summary
    ) VALUES (
        %(id)s, %(name)s, %(request_text)s, %(requester_type)s, %(status)s,
        %(current_stage)s, %(mode)s, %(priority)s, %(risk_level)s, %(summary)s
    )
    RETURNING *
    """
    params = {
        "id": project_id,
        "name": name,
        "request_text": request_text,
        "requester_type": "human",
        "status": "created",
        "current_stage": "intake",
        "mode": mode,
        "priority": "normal",
        "risk_level": "medium",
        "summary": None,
    }

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row)


def get_project_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    sql = "SELECT * FROM projects WHERE id = %s"
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            row = cur.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Project not found: {project_id}")
            return dict(row)


def _update_project_stage(
    project_id: str,
    next_stage: str,
    next_status: str,
    summary: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    project = get_project_record(project_id, database_url=database_url)
    try:
        require_transition(project["current_stage"], next_stage)
    except GraphRuntimeError as exc:
        raise ProjectStageError(str(exc)) from exc

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE projects
                SET status = %s,
                    current_stage = %s,
                    summary = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (next_status, next_stage, summary, project_id),
            )
            row = cur.fetchone()
            return dict(row)


def plan_project_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    return _update_project_stage(
        project_id=project_id,
        next_stage="plan",
        next_status="planned",
        summary="Project moved to plan stage",
        database_url=database_url,
    )


def execute_project_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    project = get_project_record(project_id, database_url=database_url)
    try:
        require_transition(project["current_stage"], "execute")
    except GraphRuntimeError as exc:
        raise ProjectStageError(str(exc)) from exc

    job_run_id = f"job_{uuid.uuid4().hex[:12]}"
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE projects
                SET status = %s,
                    current_stage = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                ("running", "execute", project_id),
            )
            updated_project = dict(cur.fetchone())

            cur.execute(
                """
                INSERT INTO job_runs (
                    id, project_id, parent_job_id, playbook_id, skill_id,
                    asset_id, target_id, assigned_agent_role, assigned_agent_id,
                    status, stage, started_at, finished_at, retry_count,
                    input_ref, output_ref
                ) VALUES (
                    %(id)s, %(project_id)s, NULL, NULL, NULL,
                    NULL, NULL, %(assigned_agent_role)s, %(assigned_agent_id)s,
                    %(status)s, %(stage)s, NOW(), NOW(), %(retry_count)s,
                    NULL, NULL
                )
                RETURNING *
                """,
                {
                    "id": job_run_id,
                    "project_id": project_id,
                    "assigned_agent_role": "manager",
                    "assigned_agent_id": "manager-api",
                    "status": "completed",
                    "stage": "execute",
                    "retry_count": 0,
                },
            )
            job_run = dict(cur.fetchone())

            cur.execute(
                """
                INSERT INTO reports (
                    id, project_id, report_type, body_ref, summary, created_by
                ) VALUES (
                    %(id)s, %(project_id)s, %(report_type)s, %(body_ref)s, %(summary)s, %(created_by)s
                )
                RETURNING *
                """,
                {
                    "id": report_id,
                    "project_id": project_id,
                    "report_type": "intermediate",
                    "body_ref": f"inline://projects/{project_id}/execute",
                    "summary": "Project moved to execute stage",
                    "created_by": "manager-api",
                },
            )
            report = dict(cur.fetchone())

    return {
        "project": updated_project,
        "job_run": job_run,
        "report": report,
    }


def validate_project_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    project = _update_project_stage(
        project_id=project_id,
        next_stage="validate",
        next_status="completed",
        summary="Project moved to validate stage",
        database_url=database_url,
    )

    report_id = f"rpt_{uuid.uuid4().hex[:12]}"

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO reports (
                    id, project_id, report_type, body_ref, summary, created_by
                ) VALUES (
                    %(id)s, %(project_id)s, %(report_type)s, %(body_ref)s, %(summary)s, %(created_by)s
                )
                RETURNING *
                """,
                {
                    "id": report_id,
                    "project_id": project_id,
                    "report_type": "intermediate",
                    "body_ref": f"inline://projects/{project_id}/validate",
                    "summary": "Project moved to validate stage",
                    "created_by": "manager-api",
                },
            )
            report = dict(cur.fetchone())

    return {
        "project": project,
        "report": report,
    }


def finalize_report_stage_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    project = _update_project_stage(
        project_id=project_id,
        next_stage="report",
        next_status="completed",
        summary="Project moved to report stage",
        database_url=database_url,
    )

    report_id = f"rpt_{uuid.uuid4().hex[:12]}"

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO reports (
                    id, project_id, report_type, body_ref, summary, created_by
                ) VALUES (
                    %(id)s, %(project_id)s, %(report_type)s, %(body_ref)s, %(summary)s, %(created_by)s
                )
                RETURNING *
                """,
                {
                    "id": report_id,
                    "project_id": project_id,
                    "report_type": "final",
                    "body_ref": f"inline://projects/{project_id}/report",
                    "summary": "Project moved to report stage",
                    "created_by": "manager-api",
                },
            )
            report = dict(cur.fetchone())

    return {
        "project": project,
        "report": report,
    }


def create_minimal_evidence_record(
    project_id: str,
    command: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    database_url: str | None = None,
) -> dict[str, Any]:
    evidence_id = f"ev_{uuid.uuid4().hex[:12]}"
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO evidence (
                    id, project_id, agent_role, asset_id, target_id, tool_name,
                    command_text, input_payload_ref, stdout_ref, stderr_ref, exit_code, evidence_type
                ) VALUES (
                    %(id)s, %(project_id)s, %(agent_role)s, NULL, NULL, %(tool_name)s,
                    %(command)s, %(input_payload)s, %(stdout_ref)s, %(stderr_ref)s, %(exit_code)s, 'command'
                )
                RETURNING *
                """,
                {
                    "id": evidence_id,
                    "project_id": project_id,
                    "agent_role": "manager",
                    "tool_name": "run_command",
                    "command": command,
                    "input_payload": "{}",
                    "stdout_ref": f"inline://stdout/{evidence_id}:{stdout}",
                    "stderr_ref": f"inline://stderr/{evidence_id}:{stderr}",
                    "exit_code": exit_code,
                },
            )
            conn.commit()
            row = cur.fetchone()
            return dict(row)


def get_assets(database_url: str | None = None) -> list[dict[str, Any]]:
    """Return list of assets with selected fields."""
    sql = """
    SELECT id,
           type AS asset_type,
           name,
           subagent_status AS status,
           NULL::text AS importance,
           agent_id AS owner_ref,
           created_at,
           updated_at
    FROM assets
    ORDER BY created_at ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def link_asset_to_project(project_id: str, asset_id: str, role: str = "primary", database_url: str | None = None) -> dict[str, Any]:
    """Link an asset to a project. Idempotent."""
    # Verify existence
    get_project_record(project_id, database_url=database_url)
    # verify asset exists
    sql_check = "SELECT id FROM assets WHERE id = %s"
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_check, (asset_id,))
            if cur.fetchone() is None:
                raise ProjectNotFoundError(f"Asset not found: {asset_id}")
    # Insert with idempotency
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO project_assets (project_id, asset_id, scope_role)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING project_id, asset_id, scope_role
                """,
                (project_id, asset_id, role),
            )
            row = cur.fetchone()
            if row is None:
                # Already exists, fetch existing
                cur.execute(
                    """
                    SELECT project_id, asset_id, scope_role FROM project_assets
                    WHERE project_id = %s AND asset_id = %s
                    """,
                    (project_id, asset_id),
                )
                row = cur.fetchone()
            return dict(row)


def get_project_assets(project_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    """Return assets linked to a project with asset details."""
    sql = """
    SELECT pa.project_id,
           pa.asset_id,
           pa.scope_role AS role,
           a.id,
           a.type AS asset_type,
           a.name,
           a.subagent_status AS status,
           NULL::text AS importance
    FROM project_assets pa
    JOIN assets a ON pa.asset_id = a.id
    WHERE pa.project_id = %s
    ORDER BY a.id ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            rows = cur.fetchall()
            # Build nested asset dict
            result = []
            for row in rows:
                row_dict = dict(row)
                asset = {
                    "id": row_dict.pop("id"),
                    "asset_type": row_dict.pop("asset_type"),
                    "name": row_dict.pop("name"),
                    "status": row_dict.pop("status"),
                    "importance": row_dict.pop("importance"),
                }
                row_dict["asset"] = asset
                result.append(row_dict)
            return result


def close_project(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    """Transition a project from report stage to close (completed). Idempotent."""
    project = get_project_record(project_id, database_url=database_url)
    if project["current_stage"] == "close":
        return project
    if project["current_stage"] != "report":
        raise ProjectStageError(f"Project not in report stage: {project_id}")
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE projects
                SET current_stage = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                ("close", "completed", project_id),
            )
            row = cur.fetchone()
            return dict(row)


def get_project_report(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    sql = """
    SELECT *
    FROM reports
    WHERE project_id = %s
    ORDER BY created_at DESC
    LIMIT 1
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            row = cur.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Report not found for project: {project_id}")
            return dict(row)


    # stray block removed


def get_evidence_for_project(project_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    """Return a list of evidence rows for a project, sorted by id ASC."""
    sql = """
    SELECT id, project_id, evidence_type, agent_role AS producer_type, tool_name AS producer_id,
           command_text AS body_ref, stdout_ref, stderr_ref, exit_code, started_at AS created_at
    FROM evidence
    WHERE project_id = %s
    ORDER BY id ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]



def get_targets(database_url: str | None = None) -> list[dict[str, Any]]:
    """Return list of targets with selected fields (mapped to required output)."""
    sql = """
    SELECT id,
           asset_id,
           base_url AS endpoint,
           health AS status,
           NULL::text AS kind,
           NULL::text AS name,
           resolved_at AS created_at,
           resolved_at AS updated_at
    FROM targets
    ORDER BY created_at ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def link_target_to_project(project_id: str, target_id: str, role: str = "primary", database_url: str | None = None) -> dict[str, Any]:
    """Link a target to a project. Creates linking table if needed. Idempotent."""
    # Verify existence of project and target
    get_project_record(project_id, database_url=database_url)
    # verify target exists
    sql_check = "SELECT id FROM targets WHERE id = %s"
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_check, (target_id,))
            if cur.fetchone() is None:
                raise ProjectNotFoundError(f"Target not found: {target_id}")
    # Ensure linking table exists
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS project_targets (
                    project_id text NOT NULL,
                    target_id text NOT NULL,
                    scope_role text NOT NULL DEFAULT 'primary',
                    created_at timestamp with time zone NOT NULL DEFAULT now(),
                    PRIMARY KEY (project_id, target_id),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE CASCADE,
                    CHECK (scope_role = ANY (ARRAY['primary','dependent','observer']))
                )
                """
            )
    # Insert link idempotently
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO project_targets (project_id, target_id, scope_role)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING project_id, target_id, scope_role
                """,
                (project_id, target_id, role),
            )
            row = cur.fetchone()
            if row is None:
                # already exists, fetch existing
                cur.execute(
                    """
                    SELECT project_id, target_id, scope_role FROM project_targets
                    WHERE project_id = %s AND target_id = %s
                    """,
                    (project_id, target_id),
                )
                row = cur.fetchone()
            return dict(row)


def get_project_targets(project_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    """Return targets linked to a project with target details."""
    sql = """
    SELECT pt.project_id,
           pt.target_id,
           pt.scope_role AS role,
           t.id,
           NULL::text AS kind,
           NULL::text AS name,
           t.base_url AS endpoint,
           t.health AS status,
           t.asset_id,
           t.resolved_at AS created_at,
           t.resolved_at AS updated_at
    FROM project_targets pt
    JOIN targets t ON pt.target_id = t.id
    WHERE pt.project_id = %s
    ORDER BY t.id ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            rows = cur.fetchall()
            result = []
            for row in rows:
                row_dict = dict(row)
                target = {
                    "id": row_dict.pop("id"),
                    "kind": row_dict.pop("kind"),
                    "name": row_dict.pop("name"),
                    "endpoint": row_dict.pop("endpoint"),
                    "status": row_dict.pop("status"),
                    "asset_id": row_dict.pop("asset_id"),
                    "created_at": row_dict.pop("created_at"),
                    "updated_at": row_dict.pop("updated_at"),
                }
                row_dict["target"] = target
                result.append(row_dict)
            return result


def get_project_report_evidence_summary(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    """Return a summary containing project, latest report, evidence list, linked assets, and linked targets."""
    project = get_project_record(project_id, database_url=database_url)
    try:
        report = get_project_report(project_id, database_url=database_url)
    except ProjectNotFoundError:
        report = None
    evidence = get_evidence_for_project(project_id, database_url=database_url)
    assets = get_project_assets(project_id, database_url=database_url)
    targets = get_project_targets(project_id, database_url=database_url)
    return {"project": project, "report": report, "evidence": evidence, "assets": assets, "targets": targets}

