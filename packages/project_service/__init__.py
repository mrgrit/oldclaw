import ast
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from packages.graph_runtime import GraphRuntimeError, require_transition

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw",
)
REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PLAYBOOK_DIR = REPO_ROOT / "seed" / "playbooks"
SEED_SKILL_DIR = REPO_ROOT / "seed" / "skills"


class ProjectServiceError(Exception):
    pass


class ProjectNotFoundError(ProjectServiceError):
    pass


class ProjectStageError(ProjectServiceError):
    pass


class JobRunNotFoundError(ProjectServiceError):
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


def get_job_run_record(job_run_id: str, database_url: str | None = None) -> dict[str, Any]:
    sql = "SELECT * FROM job_runs WHERE id = %s"
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (job_run_id,))
            row = cur.fetchone()
            if row is None:
                raise JobRunNotFoundError(f"Job run not found: {job_run_id}")
            return dict(row)


def get_latest_project_job_run(
    project_id: str,
    assigned_agent_role: str | None = None,
    stage: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any] | None:
    clauses = ["project_id = %s"]
    params: list[Any] = [project_id]
    if assigned_agent_role is not None:
        clauses.append("assigned_agent_role = %s")
        params.append(assigned_agent_role)
    if stage is not None:
        clauses.append("stage = %s")
        params.append(stage)

    sql = f"""
    SELECT *
    FROM job_runs
    WHERE {' AND '.join(clauses)}
    ORDER BY started_at DESC NULLS LAST, id DESC
    LIMIT 1
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
            return dict(row) if row is not None else None


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


def create_subagent_job_run(
    project_id: str,
    database_url: str | None = None,
    assigned_agent_id: str = "subagent-runtime",
) -> dict[str, Any]:
    project = get_project_record(project_id, database_url=database_url)
    if project["current_stage"] != "execute":
        raise ProjectStageError(
            f"Project must be in execute stage before subagent dispatch: {project_id}"
        )

    job_run_id = f"job_{uuid.uuid4().hex[:12]}"
    parent_job = get_latest_project_job_run(
        project_id,
        assigned_agent_role="manager",
        stage="execute",
        database_url=database_url,
    )
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO job_runs (
                    id, project_id, parent_job_id, playbook_id, skill_id,
                    asset_id, target_id, assigned_agent_role, assigned_agent_id,
                    status, stage, started_at, finished_at, retry_count,
                    input_ref, output_ref
                ) VALUES (
                    %(id)s, %(project_id)s, %(parent_job_id)s, %(playbook_id)s, NULL,
                    NULL, NULL, %(assigned_agent_role)s, %(assigned_agent_id)s,
                    %(status)s, %(stage)s, NOW(), NULL, %(retry_count)s,
                    NULL, NULL
                )
                RETURNING *
                """,
                {
                    "id": job_run_id,
                    "project_id": project_id,
                    "parent_job_id": parent_job["id"] if parent_job is not None else None,
                    "playbook_id": project.get("playbook_id"),
                    "assigned_agent_role": "subagent",
                    "assigned_agent_id": assigned_agent_id,
                    "status": "running",
                    "stage": "execute",
                    "retry_count": 0,
                },
            )
            row = cur.fetchone()
            return dict(row)


def create_validation_run_record(
    project_id: str,
    validator_name: str,
    validation_type: str,
    status: str,
    expected_result: dict[str, Any],
    actual_result: dict[str, Any],
    evidence_id: str | None = None,
    job_run_id: str | None = None,
    asset_id: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    validation_run_id = f"val_{uuid.uuid4().hex[:12]}"
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO validation_runs (
                    id, project_id, job_run_id, asset_id, validator_name,
                    validation_type, status, expected_result, actual_result,
                    evidence_id, executed_at
                ) VALUES (
                    %(id)s, %(project_id)s, %(job_run_id)s, %(asset_id)s, %(validator_name)s,
                    %(validation_type)s, %(status)s, %(expected_result)s::jsonb, %(actual_result)s::jsonb,
                    %(evidence_id)s, NOW()
                )
                RETURNING *
                """,
                {
                    "id": validation_run_id,
                    "project_id": project_id,
                    "job_run_id": job_run_id,
                    "asset_id": asset_id,
                    "validator_name": validator_name,
                    "validation_type": validation_type,
                    "status": status,
                    "expected_result": json_dumps(expected_result),
                    "actual_result": json_dumps(actual_result),
                    "evidence_id": evidence_id,
                },
            )
            return dict(cur.fetchone())


def get_validation_runs_for_project(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    get_project_record(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM validation_runs
                WHERE project_id = %s
                ORDER BY executed_at ASC, id ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def create_master_review_record(
    project_id: str,
    reviewer_agent_id: str,
    status: str,
    review_summary: str,
    findings: dict[str, Any],
    database_url: str | None = None,
) -> dict[str, Any]:
    get_project_record(project_id, database_url=database_url)
    review_id = f"mrv_{uuid.uuid4().hex[:12]}"
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO master_reviews (
                    id, project_id, reviewer_agent_id, status, review_summary, findings, created_at
                ) VALUES (
                    %(id)s, %(project_id)s, %(reviewer_agent_id)s, %(status)s, %(review_summary)s,
                    %(findings)s::jsonb, NOW()
                )
                RETURNING *
                """,
                {
                    "id": review_id,
                    "project_id": project_id,
                    "reviewer_agent_id": reviewer_agent_id,
                    "status": status,
                    "review_summary": review_summary,
                    "findings": json_dumps(findings),
                },
            )
            return dict(cur.fetchone())


def get_master_reviews_for_project(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    get_project_record(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM master_reviews
                WHERE project_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def json_dumps(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def summarize_validation_evidence(
    evidence: list[dict[str, Any]],
) -> tuple[str, str, dict[str, int], str | None]:
    failing = [item for item in evidence if item.get("exit_code") not in (None, 0)]
    if not evidence:
        validation_status = "inconclusive"
        validation_summary = "Validation completed with no evidence"
    elif failing:
        validation_status = "failed"
        validation_summary = f"Validation failed with {len(failing)} failing evidence item(s)"
    else:
        validation_status = "passed"
        validation_summary = f"Validation passed with {len(evidence)} evidence item(s)"

    latest_evidence_id = evidence[-1]["id"] if evidence else None
    actual_result = {
        "evidence_count": len(evidence),
        "failing_evidence_count": len(failing),
    }
    return validation_status, validation_summary, actual_result, latest_evidence_id


def summarize_project_report(
    project_id: str,
    playbook_name: str,
    target_name: str,
    asset_count: int,
    evidence: list[dict[str, Any]],
) -> str:
    skill_fragment_count = len(
        [item for item in evidence if item.get("evidence_type") == "report_fragment"]
    )
    return (
        f"Project {project_id} completed at report stage; "
        f"playbook={playbook_name}; target={target_name}; "
        f"assets={asset_count}; evidence={len(evidence)}; "
        f"skill_fragments={skill_fragment_count}"
    )


def validate_project_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    evidence = get_evidence_for_project(project_id, database_url=database_url)
    validation_status, validation_summary, actual_result, latest_evidence_id = summarize_validation_evidence(
        evidence
    )
    validation_run = create_validation_run_record(
        project_id=project_id,
        validator_name="manager-api",
        validation_type="evidence_exit_code_check",
        status=validation_status,
        expected_result={"exit_code": 0},
        actual_result=actual_result,
        evidence_id=latest_evidence_id,
        database_url=database_url,
    )

    project = _update_project_stage(
        project_id=project_id,
        next_stage="validate",
        next_status="completed",
        summary=validation_summary,
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
                    "summary": validation_summary,
                    "created_by": "manager-api",
                },
            )
            report = dict(cur.fetchone())

    return {
        "project": project,
        "report": report,
        "validation_run": validation_run,
    }


def build_project_report_summary(
    project_id: str,
    database_url: str | None = None,
) -> str:
    project = get_project_record(project_id, database_url=database_url)
    evidence = get_evidence_for_project(project_id, database_url=database_url)
    assets = get_project_assets(project_id, database_url=database_url)
    targets = get_project_targets(project_id, database_url=database_url)
    playbooks = get_project_playbooks(project_id, database_url=database_url)
    playbook_name = playbooks[0]["playbook"]["name"] if playbooks else "none"
    target_name = targets[0]["target"]["name"] if targets else "none"
    return summarize_project_report(
        project_id=project["id"],
        playbook_name=playbook_name,
        target_name=target_name,
        asset_count=len(assets),
        evidence=evidence,
    )


def finalize_report_stage_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    report_summary = build_project_report_summary(project_id, database_url=database_url)
    project = _update_project_stage(
        project_id=project_id,
        next_stage="report",
        next_status="completed",
        summary=report_summary,
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
                    "summary": report_summary,
                    "created_by": "manager-api",
                },
            )
            report = dict(cur.fetchone())

    return {
        "project": project,
        "report": report,
    }


def close_project(project_id: str, database_url: str | None = None) -> dict[str, Any]:
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
                    closed_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                ("close", "completed", project_id),
            )
            row = cur.fetchone()
            return dict(row)


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
                    command_text, input_payload_ref, stdout_ref, stderr_ref, exit_code,
                    started_at, finished_at, evidence_type
                ) VALUES (
                    %(id)s, %(project_id)s, %(agent_role)s, NULL, NULL, %(tool_name)s,
                    %(command)s, %(input_payload)s, %(stdout_ref)s, %(stderr_ref)s, %(exit_code)s,
                    NOW(), NOW(), 'command'
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
            row = cur.fetchone()
            return dict(row)


def create_skill_execution_evidence_records(
    project_id: str,
    job_run_id: str,
    resolved_skills: list[dict[str, Any]],
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    get_project_record(project_id, database_url=database_url)
    get_job_run_record(job_run_id, database_url=database_url)
    created: list[dict[str, Any]] = []
    if not resolved_skills:
        return created

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for skill in resolved_skills:
                evidence_id = f"ev_{uuid.uuid4().hex[:12]}"
                cur.execute(
                    """
                    INSERT INTO evidence (
                        id, project_id, job_run_id, asset_id, target_id, agent_role, agent_id,
                        tool_name, command_text, input_payload_ref, stdout_ref, stderr_ref,
                        exit_code, started_at, finished_at, evidence_type
                    ) VALUES (
                        %(id)s, %(project_id)s, %(job_run_id)s, NULL, NULL, %(agent_role)s, %(agent_id)s,
                        %(tool_name)s, %(command_text)s, %(input_payload_ref)s, %(stdout_ref)s, %(stderr_ref)s,
                        %(exit_code)s, NOW(), NOW(), %(evidence_type)s
                    )
                    RETURNING *
                    """,
                    {
                        "id": evidence_id,
                        "project_id": project_id,
                        "job_run_id": job_run_id,
                        "agent_role": "manager",
                        "agent_id": "manager-api",
                        "tool_name": ",".join(skill.get("required_tools", [])) or "run_command",
                        "command_text": f"skill:{skill['name']}",
                        "input_payload_ref": "{}",
                        "stdout_ref": f"inline://skill/{evidence_id}:{skill['name']}",
                        "stderr_ref": "",
                        "exit_code": 0,
                        "evidence_type": "report_fragment",
                    },
                )
                created.append(dict(cur.fetchone()))
    return created


def record_subagent_execution_result(
    project_id: str,
    job_run_id: str,
    command_text: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    database_url: str | None = None,
) -> dict[str, Any]:
    get_project_record(project_id, database_url=database_url)
    job_run = get_job_run_record(job_run_id, database_url=database_url)
    if job_run["project_id"] != project_id:
        raise ProjectServiceError(
            f"Job run {job_run_id} does not belong to project {project_id}"
        )

    evidence_id = f"ev_{uuid.uuid4().hex[:12]}"
    final_status = "completed" if exit_code == 0 else "failed"
    stdout_ref = f"inline://stdout/{evidence_id}:{stdout}"
    stderr_ref = f"inline://stderr/{evidence_id}:{stderr}"

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE job_runs
                SET status = %s,
                    stage = %s,
                    started_at = COALESCE(started_at, NOW()),
                    finished_at = NOW(),
                    output_ref = %s
                WHERE id = %s
                RETURNING *
                """,
                (final_status, "execute", stdout_ref, job_run_id),
            )
            updated_job_run = dict(cur.fetchone())

            cur.execute(
                """
                INSERT INTO evidence (
                    id, project_id, job_run_id, asset_id, target_id, agent_role, agent_id,
                    tool_name, command_text, input_payload_ref, stdout_ref, stderr_ref,
                    exit_code, started_at, finished_at, evidence_type
                ) VALUES (
                    %(id)s, %(project_id)s, %(job_run_id)s, %(asset_id)s, %(target_id)s,
                    %(agent_role)s, %(agent_id)s, %(tool_name)s, %(command_text)s,
                    %(input_payload_ref)s, %(stdout_ref)s, %(stderr_ref)s, %(exit_code)s,
                    NOW(), NOW(), %(evidence_type)s
                )
                RETURNING *
                """,
                {
                    "id": evidence_id,
                    "project_id": project_id,
                    "job_run_id": job_run_id,
                    "asset_id": job_run.get("asset_id"),
                    "target_id": job_run.get("target_id"),
                    "agent_role": "subagent",
                    "agent_id": "subagent-runtime",
                    "tool_name": "run_script",
                    "command_text": command_text,
                    "input_payload_ref": "{}",
                    "stdout_ref": stdout_ref,
                    "stderr_ref": stderr_ref,
                    "exit_code": exit_code,
                    "evidence_type": "command",
                },
            )
            evidence = dict(cur.fetchone())

    return {
        "job_run": updated_job_run,
        "evidence": evidence,
    }


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


def get_evidence_for_project(project_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    sql = """
    SELECT
        id,
        project_id,
        evidence_type,
        agent_role AS producer_type,
        tool_name AS producer_id,
        command_text AS body_ref,
        stdout_ref,
        stderr_ref,
        exit_code,
        started_at AS created_at
    FROM evidence
    WHERE project_id = %s
    ORDER BY id ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def get_assets(database_url: str | None = None) -> list[dict[str, Any]]:
    sql = """
    SELECT
        id,
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


def link_asset_to_project(
    project_id: str,
    asset_id: str,
    role: str = "primary",
    database_url: str | None = None,
) -> dict[str, Any]:
    get_project_record(project_id, database_url=database_url)
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM assets WHERE id = %s", (asset_id,))
            if cur.fetchone() is None:
                raise ProjectNotFoundError(f"Asset not found: {asset_id}")

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
                cur.execute(
                    """
                    SELECT project_id, asset_id, scope_role
                    FROM project_assets
                    WHERE project_id = %s AND asset_id = %s
                    """,
                    (project_id, asset_id),
                )
                row = cur.fetchone()
            return dict(row)


def get_project_assets(project_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    get_project_record(project_id, database_url=database_url)
    sql = """
    SELECT
        pa.project_id,
        pa.asset_id,
        pa.scope_role AS role,
        a.id AS nested_id,
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
            result: list[dict[str, Any]] = []
            for row in rows:
                row_dict = dict(row)
                asset = {
                    "id": row_dict.pop("nested_id"),
                    "asset_type": row_dict.pop("asset_type"),
                    "name": row_dict.pop("name"),
                    "status": row_dict.pop("status"),
                    "importance": row_dict.pop("importance"),
                }
                row_dict["asset"] = asset
                result.append(row_dict)
            return result


def get_targets(database_url: str | None = None) -> list[dict[str, Any]]:
    sql = """
    SELECT
        id,
        'http'::text AS kind,
        id AS name,
        base_url AS endpoint,
        health AS status,
        asset_id,
        resolved_at AS created_at,
        resolved_at AS updated_at
    FROM targets
    ORDER BY resolved_at ASC, id ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def _ensure_project_targets_table(database_url: str | None = None) -> None:
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS project_targets (
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    target_id TEXT NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
                    scope_role TEXT NOT NULL DEFAULT 'primary',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (project_id, target_id),
                    CHECK (scope_role IN ('primary', 'dependent', 'observer'))
                )
                """
            )


def link_target_to_project(
    project_id: str,
    target_id: str,
    role: str = "primary",
    database_url: str | None = None,
) -> dict[str, Any]:
    get_project_record(project_id, database_url=database_url)

    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM targets WHERE id = %s", (target_id,))
            if cur.fetchone() is None:
                raise ProjectNotFoundError(f"Target not found: {target_id}")

    _ensure_project_targets_table(database_url=database_url)

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
                cur.execute(
                    """
                    SELECT project_id, target_id, scope_role
                    FROM project_targets
                    WHERE project_id = %s AND target_id = %s
                    """,
                    (project_id, target_id),
                )
                row = cur.fetchone()
            return dict(row)


def get_project_targets(project_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    get_project_record(project_id, database_url=database_url)
    _ensure_project_targets_table(database_url=database_url)

    sql = """
    SELECT
        pt.project_id,
        pt.target_id,
        pt.scope_role AS role,
        t.id AS nested_id,
        'http'::text AS kind,
        t.id AS name,
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
            result: list[dict[str, Any]] = []
            for row in rows:
                row_dict = dict(row)
                target = {
                    "id": row_dict.pop("nested_id"),
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


def get_playbooks(database_url: str | None = None) -> list[dict[str, Any]]:
    sql = """
    SELECT
        id,
        name,
        COALESCE(description, '') AS description,
        CASE WHEN enabled THEN 'enabled' ELSE 'disabled' END AS status,
        created_at,
        created_at AS updated_at
    FROM playbooks
    ORDER BY created_at ASC, id ASC
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def link_playbook_to_project(
    project_id: str,
    playbook_id: str,
    role: str = "primary",
    database_url: str | None = None,
) -> dict[str, Any]:
    get_project_record(project_id, database_url=database_url)

    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM playbooks WHERE id = %s", (playbook_id,))
            if cur.fetchone() is None:
                raise ProjectNotFoundError(f"Playbook not found: {playbook_id}")

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE projects
                SET playbook_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                (playbook_id, project_id),
            )
            row = cur.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Project not found: {project_id}")

    return {
        "project_id": project_id,
        "playbook_id": playbook_id,
        "role": role,
    }


def get_project_playbooks(project_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    get_project_record(project_id, database_url=database_url)
    sql = """
    SELECT
        p.id AS project_id,
        pb.id AS playbook_id,
        'primary'::text AS role,
        pb.id AS nested_id,
        pb.name,
        COALESCE(pb.description, '') AS description,
        CASE WHEN pb.enabled THEN 'enabled' ELSE 'disabled' END AS status,
        pb.created_at,
        pb.created_at AS updated_at
    FROM projects p
    JOIN playbooks pb ON p.playbook_id = pb.id
    WHERE p.id = %s
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            rows = cur.fetchall()
            result: list[dict[str, Any]] = []
            for row in rows:
                row_dict = dict(row)
                playbook = {
                    "id": row_dict.pop("nested_id"),
                    "name": row_dict.pop("name"),
                    "description": row_dict.pop("description"),
                    "status": row_dict.pop("status"),
                    "created_at": row_dict.pop("created_at"),
                    "updated_at": row_dict.pop("updated_at"),
                }
                row_dict["playbook"] = playbook
                result.append(row_dict)
            return result


def load_seed_playbook_manifest(playbook_name: str) -> dict[str, Any] | None:
    manifest_path = SEED_PLAYBOOK_DIR / f"{playbook_name}.yaml"
    if not manifest_path.exists():
        return None

    manifest: dict[str, Any] = {
        "name": playbook_name,
        "required_skills": [],
    }
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "name":
            manifest["name"] = value.strip("'\"")
        elif key == "required_skills":
            try:
                parsed = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                parsed = []
            manifest["required_skills"] = parsed if isinstance(parsed, list) else []
    return manifest


def load_seed_skill_manifest(skill_name: str) -> dict[str, Any] | None:
    manifest_path = SEED_SKILL_DIR / f"{skill_name}.yaml"
    if not manifest_path.exists():
        return None

    manifest: dict[str, Any] = {
        "name": skill_name,
        "required_tools": [],
    }
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "name":
            manifest["name"] = value.strip("'\"")
        elif key == "required_tools":
            try:
                parsed = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                parsed = []
            manifest["required_tools"] = parsed if isinstance(parsed, list) else []
    return manifest


def _build_playbook_script_lines(
    playbook_name: str | None,
    target_endpoint: str | None,
    required_skills: list[str] | None = None,
) -> list[str]:
    endpoint = target_endpoint or "unbound-target"
    escaped_endpoint = endpoint.replace("'", "'\"'\"'")
    skills = required_skills or []
    lines: list[str] = []

    if skills:
        lines.append(f"printf '%s\\n' 'skills: {','.join(skills)}'")
    else:
        lines.append("printf '%s\\n' 'skills: none'")

    if playbook_name == "diagnose_web_latency":
        lines.extend([
            "printf '%s\\n' 'action: collect_web_latency_facts'",
            f"printf '%s\\n' 'curl-target: {escaped_endpoint}'",
        ])
        return lines

    if playbook_name == "nightly_health_baseline_check":
        lines.extend([
            "printf '%s\\n' 'action: nightly_health_baseline_check'",
            "printf '%s\\n' 'check: cpu memory disk baseline'",
        ])
        return lines

    if playbook_name == "monitor_siem_and_raise_incident":
        lines.extend([
            "printf '%s\\n' 'action: monitor_siem_and_raise_incident'",
            "printf '%s\\n' 'check: alert burst threshold'",
        ])
        return lines

    if playbook_name == "onboard_new_linux_server":
        lines.extend([
            "printf '%s\\n' 'action: onboard_new_linux_server'",
            "printf '%s\\n' 'check: host reachability and tls prerequisites'",
        ])
        return lines

    if playbook_name == "tune_siem_noise":
        lines.extend([
            "printf '%s\\n' 'action: tune_siem_noise'",
            "printf '%s\\n' 'check: noisy rule candidates'",
        ])
        return lines

    lines.append("printf '%s\\n' 'action: generic_project_execution'")
    return lines


def _build_skill_command_lines(
    skill_name: str,
    project: dict[str, Any],
    target: dict[str, Any] | None,
) -> list[str]:
    endpoint = str(target["endpoint"]) if target is not None else "http://127.0.0.1"
    escaped_endpoint = endpoint.replace("'", "'\"'\"'")
    project_id = str(project["id"]).replace("'", "'\"'\"'")

    if skill_name == "collect_web_latency_facts":
        return [
            "printf '%s\\n' 'skill-run: collect_web_latency_facts'",
            f"curl -I -sS --max-time 5 '{escaped_endpoint}' || true",
        ]

    if skill_name == "probe_linux_host":
        return [
            "printf '%s\\n' 'skill-run: probe_linux_host'",
            "uname -a",
            "df -h .",
        ]

    if skill_name == "monitor_disk_growth":
        return [
            "printf '%s\\n' 'skill-run: monitor_disk_growth'",
            "df -h .",
            "du -sh . 2>/dev/null || true",
        ]

    if skill_name == "analyze_wazuh_alert_burst":
        return [
            "printf '%s\\n' 'skill-run: analyze_wazuh_alert_burst'",
            "printf '%s\\n' 'alert_stream=sample threshold=default'",
        ]

    if skill_name == "summarize_incident_timeline":
        return [
            "printf '%s\\n' 'skill-run: summarize_incident_timeline'",
            f"printf '%s\\n' 'incident_ref={project_id}'",
        ]

    if skill_name == "check_tls_cert":
        return [
            "printf '%s\\n' 'skill-run: check_tls_cert'",
            f"openssl s_client -connect $(python3 - <<'PY'\nfrom urllib.parse import urlparse\nu = urlparse('{escaped_endpoint}')\nprint(u.netloc or u.path)\nPY\n) -servername $(python3 - <<'PY'\nfrom urllib.parse import urlparse\nu = urlparse('{escaped_endpoint}')\nhost = (u.hostname or u.path or 'localhost')\nprint(host)\nPY\n) </dev/null 2>/dev/null | openssl x509 -noout -dates || true",
        ]

    return [
        f"printf '%s\\n' 'skill-run: {skill_name}'",
    ]


def build_project_execution_script(
    project_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    project = get_project_record(project_id, database_url=database_url)
    targets = get_project_targets(project_id, database_url=database_url)
    playbooks = get_project_playbooks(project_id, database_url=database_url)

    target = targets[0]["target"] if targets else None
    playbook = playbooks[0]["playbook"] if playbooks else None
    manifest = (
        load_seed_playbook_manifest(playbook["name"])
        if playbook is not None
        else None
    )
    resolved_skills: list[dict[str, Any]] = []
    required_tools: list[str] = []
    if manifest is not None:
        for skill_name in manifest.get("required_skills", []):
            skill_manifest = load_seed_skill_manifest(skill_name)
            if skill_manifest is None:
                resolved_skills.append(
                    {
                        "name": skill_name,
                        "required_tools": [],
                    }
                )
                continue
            resolved_skills.append(skill_manifest)
            for tool_name in skill_manifest.get("required_tools", []):
                if tool_name not in required_tools:
                    required_tools.append(tool_name)

    lines = [
        "set -eu",
        f"printf '%s\\n' 'oldclaw project: {project['id']}'",
    ]

    if playbook is not None:
        lines.append(f"printf '%s\\n' 'playbook: {playbook['name']}'")
    else:
        lines.append("printf '%s\\n' 'playbook: none'")

    if target is not None:
        endpoint = str(target["endpoint"]).replace("'", "'\"'\"'")
        lines.append(f"printf '%s\\n' 'target: {endpoint}'")
    else:
        lines.append("printf '%s\\n' 'target: none'")

    request_text = str(project["request_text"]).replace("'", "'\"'\"'")
    lines.append(f"printf '%s\\n' 'request: {request_text}'")
    if required_tools:
        lines.append(f"printf '%s\\n' 'tools: {','.join(required_tools)}'")
    else:
        lines.append("printf '%s\\n' 'tools: none'")
    lines.extend(
        _build_playbook_script_lines(
            playbook["name"] if playbook is not None else None,
            target["endpoint"] if target is not None else None,
            manifest.get("required_skills", []) if manifest is not None else [],
        )
    )
    for skill in resolved_skills:
        lines.extend(_build_skill_command_lines(skill["name"], project, target))

    return {
        "project": project,
        "target": target,
        "playbook": playbook,
        "manifest": manifest,
        "resolved_skills": resolved_skills,
        "required_tools": required_tools,
        "script": "\n".join(lines),
    }


def get_project_report_evidence_summary(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    project = get_project_record(project_id, database_url=database_url)
    try:
        report = get_project_report(project_id, database_url=database_url)
    except ProjectNotFoundError:
        report = None

    evidence = get_evidence_for_project(project_id, database_url=database_url)
    assets = get_project_assets(project_id, database_url=database_url)
    targets = get_project_targets(project_id, database_url=database_url)
    playbooks = get_project_playbooks(project_id, database_url=database_url)

    return {
        "project": project,
        "report": report,
        "evidence": evidence,
        "assets": assets,
        "targets": targets,
        "playbooks": playbooks,
    }
