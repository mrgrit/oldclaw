import json
import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw",
)


class HistoryServiceError(Exception):
    pass


class HistoryProjectNotFoundError(HistoryServiceError):
    pass


def get_connection(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def _ensure_project_exists(project_id: str, database_url: str | None = None) -> None:
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM projects WHERE id = %s", (project_id,))
            if cur.fetchone() is None:
                raise HistoryProjectNotFoundError(f"Project not found: {project_id}")


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def summarize_task_memory(
    project: dict[str, Any],
    playbook_name: str | None,
    targets: list[dict[str, Any]],
    assets: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    validations: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_validation = validations[-1] if validations else None
    summary = (
        f"Project {project['id']} finished with status={project['status']} stage={project['current_stage']} "
        f"playbook={(playbook_name if playbook_name else 'none')} "
        f"targets={len(targets)} evidence={len(evidence)}"
    )
    metadata = {
        "goal": project["request_text"],
        "project_status": project["status"],
        "project_stage": project["current_stage"],
        "mode": project["mode"],
        "risk_level": project["risk_level"],
        "playbook_name": playbook_name,
        "assets": assets,
        "targets": targets,
        "evidence_count": len(evidence),
        "validation_status": latest_validation["status"] if latest_validation else None,
        "final_summary": project.get("summary"),
    }
    return {
        "summary": summary,
        "metadata": metadata,
    }


def record_history_event(
    project_id: str,
    event: str,
    context: dict[str, Any],
    job_run_id: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    _ensure_project_exists(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO histories (project_id, job_run_id, event, context, created_at)
                VALUES (%s, %s, %s, %s::jsonb, NOW())
                RETURNING *
                """,
                (project_id, job_run_id, event, _json_dumps(context)),
            )
            return dict(cur.fetchone())


def get_project_history(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    _ensure_project_exists(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM histories
                WHERE project_id = %s
                ORDER BY created_at ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def get_project_task_memories(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    _ensure_project_exists(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM task_memories
                WHERE project_id = %s
                ORDER BY created_at ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def create_task_memory(
    project_id: str,
    summary: str,
    metadata: dict[str, Any],
    job_run_id: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    _ensure_project_exists(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO task_memories (project_id, job_run_id, summary, metadata, created_at)
                VALUES (%s, %s, %s, %s::jsonb, NOW())
                RETURNING *
                """,
                (project_id, job_run_id, summary, _json_dumps(metadata)),
            )
            return dict(cur.fetchone())


def build_structured_task_memory(
    project_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    _ensure_project_exists(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = dict(cur.fetchone())

            cur.execute(
                """
                SELECT id, evidence_type, producer_type, producer_id, body_ref, exit_code
                FROM (
                    SELECT
                        id,
                        evidence_type,
                        agent_role AS producer_type,
                        tool_name AS producer_id,
                        command_text AS body_ref,
                        exit_code
                    FROM evidence
                    WHERE project_id = %s
                ) ev
                ORDER BY id ASC
                """,
                (project_id,),
            )
            evidence = [dict(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT *
                FROM validation_runs
                WHERE project_id = %s
                ORDER BY executed_at ASC, id ASC
                """,
                (project_id,),
            )
            validations = [dict(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT pb.name
                FROM projects p
                JOIN playbooks pb ON p.playbook_id = pb.id
                WHERE p.id = %s
                """,
                (project_id,),
            )
            playbook_row = cur.fetchone()

            cur.execute(
                """
                SELECT t.id, t.base_url
                FROM project_targets pt
                JOIN targets t ON pt.target_id = t.id
                WHERE pt.project_id = %s
                ORDER BY t.id ASC
                """,
                (project_id,),
            )
            targets = [dict(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT a.id, a.name
                FROM project_assets pa
                JOIN assets a ON pa.asset_id = a.id
                WHERE pa.project_id = %s
                ORDER BY a.id ASC
                """,
                (project_id,),
            )
            assets = [dict(row) for row in cur.fetchall()]

    return summarize_task_memory(
        project=project,
        playbook_name=playbook_row["name"] if playbook_row else None,
        targets=targets,
        assets=assets,
        evidence=evidence,
        validations=validations,
    )


def persist_project_closure_memory(
    project_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    memories = get_project_task_memories(project_id, database_url=database_url)
    if memories:
        history = get_project_history(project_id, database_url=database_url)
        return {
            "history": history[-1] if history else None,
            "task_memory": memories[-1],
            "created": False,
        }

    structured = build_structured_task_memory(project_id, database_url=database_url)
    history = record_history_event(
        project_id=project_id,
        event="project_closed",
        context=structured["metadata"],
        database_url=database_url,
    )
    task_memory = create_task_memory(
        project_id=project_id,
        summary=structured["summary"],
        metadata=structured["metadata"],
        database_url=database_url,
    )
    return {
        "history": history,
        "task_memory": task_memory,
        "created": True,
    }
