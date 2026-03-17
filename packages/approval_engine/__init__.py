import json
import uuid
from typing import Any

from psycopg2.extras import RealDictCursor

from packages.policy_engine import PolicyDecision
from packages.project_service import ProjectNotFoundError, get_connection, get_project_record


def _ensure_approvals_table(database_url: str | None = None) -> None:
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    policy_name TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    approver_id TEXT,
                    risk_level TEXT NOT NULL,
                    playbook_name TEXT,
                    mode TEXT NOT NULL,
                    target_count INTEGER NOT NULL DEFAULT 0,
                    decision_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    approved_at TIMESTAMPTZ,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CHECK (status IN ('approval_required', 'approved', 'rejected', 'expired'))
                )
                """
            )


def build_approval_request(project_id: str, decision: PolicyDecision) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "required": True,
        "reason": decision.reason,
        "policy_name": decision.policy_name,
        "risk_level": decision.risk_level,
        "playbook_name": decision.playbook_name,
        "mode": decision.mode,
        "target_count": decision.target_count,
        "status": "approval_required",
    }


def is_approval_override_active(approval: dict[str, Any] | None) -> bool:
    return bool(approval and approval.get("status") == "approved")


def create_approval_request_record(
    project_id: str,
    decision: PolicyDecision,
    requested_by: str = "manager-api",
    database_url: str | None = None,
) -> dict[str, Any]:
    get_project_record(project_id, database_url=database_url)
    _ensure_approvals_table(database_url=database_url)

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM approvals
                WHERE project_id = %s
                  AND policy_name = %s
                  AND status = 'approval_required'
                ORDER BY requested_at DESC, id DESC
                LIMIT 1
                """,
                (project_id, decision.policy_name),
            )
            existing = cur.fetchone()
            if existing is not None:
                return dict(existing)

            approval_id = f"apr_{uuid.uuid4().hex[:12]}"
            payload = build_approval_request(project_id, decision)
            cur.execute(
                """
                INSERT INTO approvals (
                    id, project_id, policy_name, reason, status, requested_by,
                    approver_id, risk_level, playbook_name, mode, target_count,
                    decision_payload, requested_at, approved_at, updated_at
                ) VALUES (
                    %(id)s, %(project_id)s, %(policy_name)s, %(reason)s, %(status)s, %(requested_by)s,
                    NULL, %(risk_level)s, %(playbook_name)s, %(mode)s, %(target_count)s,
                    %(decision_payload)s::jsonb, NOW(), NULL, NOW()
                )
                RETURNING *
                """,
                {
                    "id": approval_id,
                    "project_id": project_id,
                    "policy_name": decision.policy_name,
                    "reason": decision.reason,
                    "status": "approval_required",
                    "requested_by": requested_by,
                    "risk_level": decision.risk_level,
                    "playbook_name": decision.playbook_name,
                    "mode": decision.mode,
                    "target_count": decision.target_count,
                    "decision_payload": json.dumps(payload, sort_keys=True),
                },
            )
            return dict(cur.fetchone())


def list_project_approvals(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    get_project_record(project_id, database_url=database_url)
    _ensure_approvals_table(database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM approvals
                WHERE project_id = %s
                ORDER BY requested_at ASC, id ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def get_latest_project_approval(
    project_id: str,
    policy_name: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any] | None:
    get_project_record(project_id, database_url=database_url)
    _ensure_approvals_table(database_url=database_url)
    sql = """
    SELECT *
    FROM approvals
    WHERE project_id = %s
    """
    params: list[Any] = [project_id]
    if policy_name is not None:
        sql += " AND policy_name = %s"
        params.append(policy_name)
    sql += " ORDER BY requested_at DESC, id DESC LIMIT 1"
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
            return dict(row) if row is not None else None


def approve_project_approval(
    project_id: str,
    approval_id: str,
    approver_id: str = "human-reviewer",
    database_url: str | None = None,
) -> dict[str, Any]:
    get_project_record(project_id, database_url=database_url)
    _ensure_approvals_table(database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE approvals
                SET status = 'approved',
                    approver_id = %s,
                    approved_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                  AND project_id = %s
                RETURNING *
                """,
                (approver_id, approval_id, project_id),
            )
            row = cur.fetchone()
            if row is None:
                raise ProjectNotFoundError(
                    f"Approval not found for project {project_id}: {approval_id}"
                )
            return dict(row)


def has_project_approval(
    project_id: str,
    policy_name: str,
    database_url: str | None = None,
) -> bool:
    latest = get_latest_project_approval(
        project_id,
        policy_name=policy_name,
        database_url=database_url,
    )
    return is_approval_override_active(latest)
