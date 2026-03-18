import os
from typing import Any, Callable

from fastapi import APIRouter, FastAPI, HTTPException, status
import httpx
from pydantic import BaseModel

from packages.approval_engine import (
    approve_project_approval,
    build_approval_request,
    create_approval_request_record,
    has_project_approval,
    list_project_approvals,
)
from packages.history_service import (
    HistoryProjectNotFoundError,
    HistoryServiceError,
    get_project_history,
    get_project_task_memories,
    persist_project_closure_memory,
)
from packages.pi_adapter.runtime import PiRuntimeClient, PiRuntimeConfig
from packages.policy_engine import (
    PolicyDeniedError,
    evaluate_project_policy,
)
from packages.project_service import (
    build_project_execution_script,
    ProjectNotFoundError,
    ProjectServiceError,
    ProjectStageError,
    close_project,
    create_skill_execution_evidence_records,
    create_subagent_job_run,
    create_minimal_evidence_record,
    create_project_record,
    execute_project_record,
    finalize_report_stage_record,
    get_assets,
    get_evidence_for_project,
    get_playbooks,
    get_project_assets,
    get_project_playbooks,
    get_project_record,
    get_project_report,
    get_project_targets,
    get_targets,
    link_asset_to_project,
    link_playbook_to_project,
    link_target_to_project,
    plan_project_record,
    validate_project_record,
)
from packages.scheduler_service import (
    create_schedule_record,
    create_watch_job_record,
    get_project_incidents,
    get_project_schedules,
    get_project_watch_events,
    get_project_watch_jobs,
    SchedulerServiceError,
)


class ProjectCreateRequest(BaseModel):
    name: str
    request_text: str
    mode: str = "one_shot"


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "manager"


class MinimalEvidenceRequest(BaseModel):
    command: str
    stdout: str
    stderr: str = ""
    exit_code: int = 0


class SubagentDispatchRequest(BaseModel):
    script: str
    timeout_s: int = 120


class ExecuteRunRequest(BaseModel):
    script: str
    timeout_s: int = 120


class ApprovalDecisionRequest(BaseModel):
    approver_id: str = "human-reviewer"


class ReviewHandoffRequest(BaseModel):
    reviewer_id: str = "master-service"
    comments: str | None = None


class ScheduleCreateRequest(BaseModel):
    schedule_type: str
    cron_expr: str | None = None
    next_run: str | None = None
    enabled: bool = True
    metadata: dict[str, Any] = {}


class WatchJobCreateRequest(BaseModel):
    watch_type: str
    status: str = "running"
    metadata: dict[str, Any] = {}


def default_scheduler_runner() -> dict[str, Any]:
    scheduler_url = os.getenv(
        "OLDCLAW_SCHEDULER_URL",
        "http://127.0.0.1:8013",
    ).rstrip("/")
    with httpx.Client(timeout=30) as client:
        response = client.post(f"{scheduler_url}/run-once")
        response.raise_for_status()
        return response.json()


def default_watch_runner() -> dict[str, Any]:
    watch_url = os.getenv(
        "OLDCLAW_WATCH_URL",
        "http://127.0.0.1:8014",
    ).rstrip("/")
    with httpx.Client(timeout=30) as client:
        response = client.post(f"{watch_url}/run-once")
        response.raise_for_status()
        return response.json()


def default_subagent_runner(payload: dict[str, Any]) -> dict[str, Any]:
    subagent_url = os.getenv(
        "OLDCLAW_SUBAGENT_URL",
        "http://127.0.0.1:8012",
    ).rstrip("/")
    with httpx.Client(timeout=max(int(payload.get("timeout_s", 120)) + 5, 10)) as client:
        response = client.post(f"{subagent_url}/a2a/run_script", json=payload)
        response.raise_for_status()
        return response.json()


def default_master_runner(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    master_url = os.getenv(
        "OLDCLAW_MASTER_URL",
        "http://127.0.0.1:8011",
    ).rstrip("/")
    with httpx.Client(timeout=30) as client:
        response = client.post(f"{master_url}/projects/{project_id}/review", json=payload)
        response.raise_for_status()
        return response.json()


def _run_execute_auto_flow(
    project_id: str,
    runner: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    execution_plan = build_project_execution_script(project_id)
    execute_result = execute_project_record(project_id)
    job_run = create_subagent_job_run(project_id)
    subagent_result = runner(
        {
            "project_id": project_id,
            "job_run_id": job_run["id"],
            "script": execution_plan["script"],
            "timeout_s": 120,
        }
    )
    skill_evidence = create_skill_execution_evidence_records(
        project_id=project_id,
        job_run_id=job_run["id"],
        resolved_skills=execution_plan["resolved_skills"],
    )
    return {
        "execution_plan": execution_plan,
        "execute_result": execute_result,
        "job_run": job_run,
        "subagent_result": subagent_result,
        "skill_evidence": skill_evidence,
    }


def _require_execution_policy(project_id: str) -> dict[str, Any]:
    decision = evaluate_project_policy(project_id)
    if decision.allowed:
        return decision.to_dict()
    if decision.requires_approval and has_project_approval(project_id, decision.policy_name):
        approved = decision.to_dict()
        approved["allowed"] = True
        approved["requires_approval"] = False
        approved["reason"] = f"approved override for policy {decision.policy_name}"
        approved["approval_status"] = "approved"
        return approved
    raise PolicyDeniedError(decision)


def _build_policy_denial_detail(project_id: str, exc: PolicyDeniedError) -> dict[str, Any]:
    approval_request = None
    if exc.decision.requires_approval:
        approval_record = create_approval_request_record(project_id, exc.decision)
        approval_request = {
            **build_approval_request(project_id, exc.decision),
            "approval_id": approval_record["id"],
        }
    return {
        "message": exc.decision.reason,
        "policy": exc.decision.to_dict(),
        "approval_request": approval_request,
    }


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"]) 

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "manager-api"}

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig())

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("manager-api-runtime")
            result = client.invoke_model(
                payload.prompt,
                {
                    "session_id": session_id,
                    "role": payload.role,
                },
            )
            client.close_session(session_id)
            return {"status": "ok", "session_id": session_id, "result": result}
        except NotImplementedError as exc:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={"message": str(exc)},
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"runtime invocation failed: {exc}"},
            ) from exc

    return router


def create_project_router(
    subagent_runner: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    master_runner: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    scheduler_runner: Callable[[], dict[str, Any]] | None = None,
    watch_runner: Callable[[], dict[str, Any]] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["projects"])
    runner = subagent_runner or default_subagent_runner
    review_runner = master_runner or default_master_runner
    scheduler_once_runner = scheduler_runner or default_scheduler_runner
    watch_once_runner = watch_runner or default_watch_runner

    @router.post("")
    def create_project(payload: ProjectCreateRequest) -> dict[str, Any]:
        try:
            project = create_project_record(
                name=payload.name,
                request_text=payload.request_text,
                mode=payload.mode,
            )
            return {"status": "ok", "project": project}
        except ProjectServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": str(exc)},
            ) from exc

    @router.post("/{project_id}/plan")
    def plan_project(project_id: str) -> dict[str, Any]:
        try:
            project = plan_project_record(project_id)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}")
    def get_project(project_id: str) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/history")
    def get_project_history_endpoint(project_id: str) -> dict[str, Any]:
        try:
            history = get_project_history(project_id)
            task_memories = get_project_task_memories(project_id)
            return {
                "status": "ok",
                "project_id": project_id,
                "history": history,
                "task_memories": task_memories,
            }
        except HistoryProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except HistoryServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/execute")
    def execute_project(project_id: str) -> dict[str, Any]:
        try:
            result = execute_project_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/dispatch/subagent")
    def dispatch_subagent(project_id: str, payload: SubagentDispatchRequest) -> dict[str, Any]:
        try:
            policy = _require_execution_policy(project_id)
            job_run = create_subagent_job_run(project_id)
            result = runner(
                {
                    "project_id": project_id,
                    "job_run_id": job_run["id"],
                    "script": payload.script,
                    "timeout_s": payload.timeout_s,
                }
            )
            return {
                "status": "ok",
                "project_id": project_id,
                "policy": policy,
                "job_run": job_run,
                "subagent_result": result,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except PolicyDeniedError as exc:
            status_code = 403 if exc.decision.requires_approval else 400
            raise HTTPException(status_code=status_code, detail=_build_policy_denial_detail(project_id, exc)) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "subagent returned error response",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"subagent dispatch failed: {exc}"},
            ) from exc

    @router.post("/{project_id}/execute/run")
    def execute_project_run(project_id: str, payload: ExecuteRunRequest) -> dict[str, Any]:
        try:
            policy = _require_execution_policy(project_id)
            execute_result = execute_project_record(project_id)
            job_run = create_subagent_job_run(project_id)
            subagent_result = runner(
                {
                    "project_id": project_id,
                    "job_run_id": job_run["id"],
                    "script": payload.script,
                    "timeout_s": payload.timeout_s,
                }
            )
            return {
                "status": "ok",
                "project_id": project_id,
                "policy": policy,
                "execute_result": execute_result,
                "job_run": job_run,
                "subagent_result": subagent_result,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except PolicyDeniedError as exc:
            status_code = 403 if exc.decision.requires_approval else 400
            raise HTTPException(status_code=status_code, detail=_build_policy_denial_detail(project_id, exc)) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "subagent returned error response",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"subagent dispatch failed: {exc}"},
            ) from exc

    @router.post("/{project_id}/execute/auto")
    def execute_project_auto(project_id: str) -> dict[str, Any]:
        try:
            policy = _require_execution_policy(project_id)
            flow = _run_execute_auto_flow(project_id, runner)
            return {
                "status": "ok",
                "project_id": project_id,
                "policy": policy,
                **flow,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except PolicyDeniedError as exc:
            status_code = 403 if exc.decision.requires_approval else 400
            raise HTTPException(status_code=status_code, detail=_build_policy_denial_detail(project_id, exc)) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "subagent returned error response",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"subagent dispatch failed: {exc}"},
            ) from exc

    @router.post("/{project_id}/run/auto")
    def run_project_auto(project_id: str) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
            planned = None
            if project["current_stage"] == "intake":
                planned = plan_project_record(project_id)
            policy = _require_execution_policy(project_id)
            flow = _run_execute_auto_flow(project_id, runner)
            validated = validate_project_record(project_id)
            reported = finalize_report_stage_record(project_id)
            closed = close_project(project_id)
            memory = persist_project_closure_memory(project_id)
            return {
                "status": "ok",
                "project_id": project_id,
                "policy": policy,
                "planned": planned,
                **flow,
                "validated": validated,
                "reported": reported,
                "closed": closed,
                "memory": memory,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except PolicyDeniedError as exc:
            status_code = 403 if exc.decision.requires_approval else 400
            raise HTTPException(status_code=status_code, detail=_build_policy_denial_detail(project_id, exc)) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "subagent returned error response",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"subagent dispatch failed: {exc}"},
            ) from exc

    @router.post("/{project_id}/run/auto/review")
    def run_project_auto_with_review(project_id: str, payload: ReviewHandoffRequest) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
            planned = None
            if project["current_stage"] == "intake":
                planned = plan_project_record(project_id)
            policy = _require_execution_policy(project_id)
            flow = _run_execute_auto_flow(project_id, runner)
            validated = validate_project_record(project_id)
            reported = finalize_report_stage_record(project_id)
            closed = close_project(project_id)
            memory = persist_project_closure_memory(project_id)
            review = review_runner(
                project_id,
                {
                    "project_id": project_id,
                    "reviewer_id": payload.reviewer_id,
                    "comments": payload.comments,
                },
            )
            return {
                "status": "ok",
                "project_id": project_id,
                "policy": policy,
                "planned": planned,
                **flow,
                "validated": validated,
                "reported": reported,
                "closed": closed,
                "memory": memory,
                "master_review": review,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except PolicyDeniedError as exc:
            status_code = 403 if exc.decision.requires_approval else 400
            raise HTTPException(status_code=status_code, detail=_build_policy_denial_detail(project_id, exc)) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "handoff service returned error response",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"handoff dispatch failed: {exc}"},
            ) from exc

    @router.get("/{project_id}/execute/plan")
    def get_execute_plan(project_id: str) -> dict[str, Any]:
        try:
            execution_plan = build_project_execution_script(project_id)
            return {
                "status": "ok",
                "project_id": project_id,
                "execution_plan": execution_plan,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/policy-check")
    def get_policy_check(project_id: str) -> dict[str, Any]:
        try:
            decision = evaluate_project_policy(project_id)
            latest_approvals = list_project_approvals(project_id)
            latest_approval = latest_approvals[-1] if latest_approvals else None
            return {
                "status": "ok",
                "project_id": project_id,
                "policy": decision.to_dict(),
                "latest_approval": latest_approval,
                "approval_request": (
                    build_approval_request(project_id, decision)
                    if decision.requires_approval
                    else None
                ),
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/approvals")
    def get_project_approvals(project_id: str) -> dict[str, Any]:
        try:
            approvals = list_project_approvals(project_id)
            return {"status": "ok", "project_id": project_id, "items": approvals}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/approvals/{approval_id}/approve")
    def approve_project(project_id: str, approval_id: str, payload: ApprovalDecisionRequest) -> dict[str, Any]:
        try:
            approval = approve_project_approval(
                project_id=project_id,
                approval_id=approval_id,
                approver_id=payload.approver_id,
            )
            return {"status": "ok", "project_id": project_id, "approval": approval}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/validate")
    def validate_project(project_id: str) -> dict[str, Any]:
        try:
            result = validate_project_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/report/finalize")
    def finalize_report(project_id: str) -> dict[str, Any]:
        try:
            result = finalize_report_stage_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/evidence/minimal")
    def create_minimal_evidence(project_id: str, payload: MinimalEvidenceRequest) -> dict[str, Any]:
        try:
            evidence = create_minimal_evidence_record(
                project_id=project_id,
                command=payload.command,
                stdout=payload.stdout,
                stderr=payload.stderr,
                exit_code=payload.exit_code,
            )
            return {"status": "ok", "evidence": evidence}
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/report")
    def get_project_report_endpoint(project_id: str) -> dict[str, Any]:
        try:
            report = get_project_report(project_id)
            return {"status": "ok", "report": report}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/evidence")
    def get_project_evidence_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_evidence_for_project(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/close")
    def close_project_endpoint(project_id: str) -> dict[str, Any]:
        try:
            project = close_project(project_id)
            memory = persist_project_closure_memory(project_id)
            return {"status": "ok", "project": project, "memory": memory}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except HistoryServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/assets/{asset_id}")
    def link_project_asset(project_id: str, asset_id: str) -> dict[str, Any]:
        try:
            result = link_asset_to_project(project_id, asset_id)
            return {
                "status": "ok",
                "project_id": result["project_id"],
                "asset_id": result["asset_id"],
                "role": result["scope_role"],
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/assets")
    def get_project_assets_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_assets(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/targets/{target_id}")
    def link_project_target(project_id: str, target_id: str) -> dict[str, Any]:
        try:
            result = link_target_to_project(project_id, target_id)
            return {
                "status": "ok",
                "project_id": result["project_id"],
                "target_id": result["target_id"],
                "role": result["scope_role"],
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/targets")
    def get_project_targets_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_targets(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/playbooks/{playbook_id}")
    def link_project_playbook(project_id: str, playbook_id: str) -> dict[str, Any]:
        try:
            result = link_playbook_to_project(project_id, playbook_id)
            return {
                "status": "ok",
                "project_id": result["project_id"],
                "playbook_id": result["playbook_id"],
                "role": result["role"],
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/playbooks")
    def get_project_playbooks_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_playbooks(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/schedules")
    def create_project_schedule(project_id: str, payload: ScheduleCreateRequest) -> dict[str, Any]:
        try:
            schedule = create_schedule_record(
                project_id=project_id,
                schedule_type=payload.schedule_type,
                cron_expr=payload.cron_expr,
                next_run=payload.next_run,
                enabled=payload.enabled,
                metadata=payload.metadata,
            )
            return {"status": "ok", "project_id": project_id, "schedule": schedule}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except SchedulerServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/schedules")
    def get_project_schedules_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_schedules(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/watch-jobs")
    def create_project_watch_job(project_id: str, payload: WatchJobCreateRequest) -> dict[str, Any]:
        try:
            watch_job = create_watch_job_record(
                project_id=project_id,
                watch_type=payload.watch_type,
                status=payload.status,
                metadata=payload.metadata,
            )
            return {"status": "ok", "project_id": project_id, "watch_job": watch_job}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except SchedulerServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/watch-jobs")
    def get_project_watch_jobs_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_watch_jobs(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/watch-events")
    def get_project_watch_events_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_watch_events(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/incidents")
    def get_project_incidents_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_incidents(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/scheduler/run-once")
    def trigger_scheduler_run_once() -> dict[str, Any]:
        try:
            result = scheduler_once_runner()
            return {"status": "ok", "result": result}
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "scheduler worker returned error response",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"scheduler dispatch failed: {exc}"},
            ) from exc

    @router.post("/watch/run-once")
    def trigger_watch_run_once() -> dict[str, Any]:
        try:
            result = watch_once_runner()
            return {"status": "ok", "result": result}
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "watch worker returned error response",
                    "status_code": exc.response.status_code,
                    "body": exc.response.text,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"watch dispatch failed: {exc}"},
            ) from exc

    return router


def create_asset_router() -> APIRouter:
    router = APIRouter(prefix="/assets", tags=["assets"])

    @router.get("")
    def list_assets() -> dict[str, Any]:
        return {"items": get_assets()}

    return router


def create_target_router() -> APIRouter:
    router = APIRouter(prefix="/targets", tags=["targets"])

    @router.get("")
    def list_targets() -> dict[str, Any]:
        return {"items": get_targets()}

    return router


def create_playbook_router() -> APIRouter:
    router = APIRouter(prefix="/playbooks", tags=["playbooks"])

    @router.get("")
    def list_playbooks() -> dict[str, Any]:
        return {"items": get_playbooks()}

    return router


def create_app(
    subagent_runner: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    master_runner: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    scheduler_runner: Callable[[], dict[str, Any]] | None = None,
    watch_runner: Callable[[], dict[str, Any]] | None = None,
) -> FastAPI:
    app = FastAPI(
        title="OldClaw Manager API",
        version="0.3.0-m3",
        description="Manager API with minimal lifecycle, evidence, asset, target, and playbook routes.",
    )

    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(
        create_project_router(
            subagent_runner=subagent_runner,
            master_runner=master_runner,
            scheduler_runner=scheduler_runner,
            watch_runner=watch_runner,
        )
    )
    app.include_router(create_asset_router())
    app.include_router(create_target_router())
    app.include_router(create_playbook_router())

    return app


app = create_app()
