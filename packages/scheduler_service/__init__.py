import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from packages.project_service import ProjectNotFoundError, get_project_record


DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw",
)


class SchedulerServiceError(Exception):
    pass


def get_connection(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _ensure_project(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    return get_project_record(project_id, database_url=database_url)


def create_schedule_record(
    project_id: str,
    schedule_type: str,
    cron_expr: str | None = None,
    next_run: datetime | None = None,
    enabled: bool = True,
    metadata: dict[str, Any] | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    _ensure_project(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO schedules (
                    project_id, schedule_type, cron_expr, next_run, enabled, metadata, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s::jsonb, NOW()
                )
                RETURNING *
                """,
                (
                    project_id,
                    schedule_type,
                    cron_expr,
                    next_run,
                    enabled,
                    _json_dumps(metadata or {}),
                ),
            )
            return dict(cur.fetchone())


def get_project_schedules(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    _ensure_project(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM schedules
                WHERE project_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def load_due_schedules(
    database_url: str | None = None,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    now = as_of or datetime.now(timezone.utc)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM schedules
                WHERE enabled = true
                  AND (next_run IS NULL OR next_run <= %s)
                ORDER BY next_run ASC NULLS FIRST, created_at ASC
                """,
                (now,),
            )
            return [dict(row) for row in cur.fetchall()]


def process_schedule(
    schedule: dict[str, Any],
    database_url: str | None = None,
    processed_at: datetime | None = None,
) -> dict[str, Any]:
    project = _ensure_project(schedule["project_id"], database_url=database_url)
    now = processed_at or datetime.now(timezone.utc)
    metadata = schedule.get("metadata") or {}
    interval_seconds = int(metadata.get("interval_seconds", 300))
    next_run = now + timedelta(seconds=max(interval_seconds, 1))

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE schedules
                SET last_run = %s,
                    next_run = %s,
                    metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE id = %s
                RETURNING *
                """,
                (
                    now,
                    next_run,
                    _json_dumps(
                        {
                            "last_processed_stage": project["current_stage"],
                            "last_processed_status": project["status"],
                        }
                    ),
                    schedule["id"],
                ),
            )
            updated_schedule = dict(cur.fetchone())

            cur.execute(
                """
                INSERT INTO histories (project_id, job_run_id, event, context, created_at)
                VALUES (%s, NULL, %s, %s::jsonb, %s)
                RETURNING *
                """,
                (
                    schedule["project_id"],
                    "schedule_triggered",
                    _json_dumps(
                        {
                            "schedule_id": str(schedule["id"]),
                            "schedule_type": schedule["schedule_type"],
                            "processed_at": now.isoformat(),
                            "next_run": next_run.isoformat(),
                        }
                    ),
                    now,
                ),
            )
            history = dict(cur.fetchone())
    return {
        "schedule": updated_schedule,
        "history": history,
    }


def run_scheduler_once(
    database_url: str | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    schedules = load_due_schedules(database_url=database_url, as_of=as_of)
    processed: list[dict[str, Any]] = []
    for schedule in schedules:
        processed.append(process_schedule(schedule, database_url=database_url, processed_at=as_of))
    return {
        "loaded_count": len(schedules),
        "processed_count": len(processed),
        "items": processed,
    }


def load_active_watch_jobs(
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM watch_jobs
                WHERE status = 'running'
                ORDER BY created_at ASC, id ASC
                """
            )
            return [dict(row) for row in cur.fetchall()]


def create_watch_job_record(
    project_id: str,
    watch_type: str,
    status: str = "running",
    metadata: dict[str, Any] | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    _ensure_project(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO watch_jobs (
                    project_id, watch_type, status, metadata, created_at
                ) VALUES (
                    %s, %s, %s, %s::jsonb, NOW()
                )
                RETURNING *
                """,
                (
                    project_id,
                    watch_type,
                    status,
                    _json_dumps(metadata or {}),
                ),
            )
            return dict(cur.fetchone())


def get_project_watch_jobs(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    _ensure_project(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM watch_jobs
                WHERE project_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def get_project_watch_events(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    _ensure_project(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT we.*
                FROM watch_events we
                JOIN watch_jobs wj ON we.watch_job_id = wj.id
                WHERE wj.project_id = %s
                ORDER BY we.created_at ASC, we.id ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def get_project_incidents(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    _ensure_project(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM incidents
                WHERE project_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def process_watch_job(
    job: dict[str, Any],
    database_url: str | None = None,
    processed_at: datetime | None = None,
) -> dict[str, Any]:
    project = _ensure_project(job["project_id"], database_url=database_url)
    now = processed_at or datetime.now(timezone.utc)
    metadata = job.get("metadata") or {}
    event_type = str(metadata.get("event_type") or "watch_heartbeat")
    payload = {
        "watch_type": job["watch_type"],
        "project_stage": project["current_stage"],
        "project_status": project["status"],
        "processed_at": now.isoformat(),
    }

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO watch_events (watch_job_id, event_type, payload, created_at)
                VALUES (%s, %s, %s::jsonb, %s)
                RETURNING *
                """,
                (job["id"], event_type, _json_dumps(payload), now),
            )
            event = dict(cur.fetchone())

            incident = None
            if bool(metadata.get("create_incident")):
                cur.execute(
                    """
                    INSERT INTO incidents (project_id, severity, summary, status, metadata, created_at)
                    VALUES (%s, %s, %s, 'open', %s::jsonb, %s)
                    RETURNING *
                    """,
                    (
                        job["project_id"],
                        str(metadata.get("severity") or "medium"),
                        str(metadata.get("summary") or f"Watch incident for {job['watch_type']}"),
                        _json_dumps(
                            {
                                "watch_job_id": str(job["id"]),
                                "watch_event_id": str(event["id"]),
                                "event_type": event_type,
                            }
                        ),
                        now,
                    ),
                )
                incident = dict(cur.fetchone())

            cur.execute(
                """
                INSERT INTO histories (project_id, job_run_id, event, context, created_at)
                VALUES (%s, NULL, %s, %s::jsonb, %s)
                RETURNING *
                """,
                (
                    job["project_id"],
                    "watch_job_processed",
                    _json_dumps(
                        {
                            "watch_job_id": str(job["id"]),
                            "watch_event_id": str(event["id"]),
                            "incident_id": str(incident["id"]) if incident else None,
                            "processed_at": now.isoformat(),
                        }
                    ),
                    now,
                ),
            )
            history = dict(cur.fetchone())
    return {
        "watch_job": job,
        "watch_event": event,
        "incident": incident,
        "history": history,
    }


def run_watch_once(
    database_url: str | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    jobs = load_active_watch_jobs(database_url=database_url)
    processed: list[dict[str, Any]] = []
    for job in jobs:
        processed.append(process_watch_job(job, database_url=database_url, processed_at=as_of))
    return {
        "loaded_count": len(jobs),
        "processed_count": len(processed),
        "items": processed,
    }
