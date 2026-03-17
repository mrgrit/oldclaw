from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.approval_engine import list_project_approvals
from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig
from packages.project_service import (
    ProjectNotFoundError,
    ProjectServiceError,
    create_master_review_record,
    get_evidence_for_project,
    get_master_reviews_for_project,
    get_project_record,
    get_project_report,
    get_validation_runs_for_project,
)


class ReviewReq(BaseModel):
    project_id: str
    reviewer_id: str
    comments: str | None = None


class ReplanReq(BaseModel):
    reviewer_id: str = "master-service"
    comments: str | None = None


class EscalateReq(BaseModel):
    level: int = 1
    reviewer_id: str = "master-service"
    reason: str | None = None


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "master"


def _build_review_context(project_id: str) -> dict[str, Any]:
    project = get_project_record(project_id)
    try:
        report = get_project_report(project_id)
    except ProjectNotFoundError:
        report = None
    evidence = get_evidence_for_project(project_id)
    validations = get_validation_runs_for_project(project_id)
    approvals = list_project_approvals(project_id)
    latest_validation = validations[-1] if validations else None
    latest_approval = approvals[-1] if approvals else None
    return {
        "project": project,
        "report": report,
        "evidence": evidence,
        "validations": validations,
        "approvals": approvals,
        "latest_validation": latest_validation,
        "latest_approval": latest_approval,
    }


def _decide_review_status(context: dict[str, Any], comments: str | None = None) -> tuple[str, str, dict[str, Any]]:
    project = context["project"]
    evidence = context["evidence"]
    latest_validation = context["latest_validation"]
    latest_approval = context["latest_approval"]

    findings = {
        "project_stage": project["current_stage"],
        "project_status": project["status"],
        "evidence_count": len(evidence),
        "validation_status": latest_validation["status"] if latest_validation else None,
        "approval_status": latest_approval["status"] if latest_approval else None,
        "reviewer_comments": comments,
    }

    if latest_approval and latest_approval["status"] == "approval_required":
        return (
            "needs_replan",
            "Approval is still pending; manager must wait for approval before completion.",
            findings,
        )

    if latest_validation is None:
        return (
            "needs_replan",
            "Validation evidence is missing; manager must produce validation before review.",
            findings,
        )

    if latest_validation["status"] == "failed":
        return (
            "rejected",
            "Validation failed; manager must replan and rerun execution.",
            findings,
        )

    if latest_validation["status"] == "inconclusive":
        return (
            "needs_replan",
            "Validation is inconclusive; manager must gather more evidence.",
            findings,
        )

    if project["current_stage"] != "close":
        return (
            "needs_replan",
            "Project is not closed yet; manager must complete report and close stages.",
            findings,
        )

    return (
        "approved",
        "Master review approved the completed project.",
        findings,
    )


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "master-service"}

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig(default_role="master"))

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("master-service-runtime", role=payload.role)
            result = client.invoke_model(
                payload.prompt,
                {"session_id": session_id, "role": payload.role},
            )
            client.close_session(session_id)
            return {"status": "ok", "session_id": session_id, "result": result}
        except PiAdapterError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "pi adapter invocation failed",
                    "error": exc.error.message,
                    "stdout": exc.error.stdout,
                    "stderr": exc.error.stderr,
                    "exit_code": exc.error.exit_code,
                },
            ) from exc

    return router


def create_review_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["review"])

    @router.post("/{project_id}/review")
    def review_project(project_id: str, req: ReviewReq) -> dict[str, Any]:
        try:
            context = _build_review_context(project_id)
            review_status, summary, findings = _decide_review_status(context, req.comments)
            review = create_master_review_record(
                project_id=project_id,
                reviewer_agent_id=req.reviewer_id,
                status=review_status,
                review_summary=summary,
                findings=findings,
            )
            return {
                "status": "ok",
                "project_id": project_id,
                "review": review,
                "context": {
                    "evidence_count": len(context["evidence"]),
                    "validation_count": len(context["validations"]),
                    "approval_count": len(context["approvals"]),
                },
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/reviews")
    def get_reviews(project_id: str) -> dict[str, Any]:
        try:
            items = get_master_reviews_for_project(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/replan")
    def replan_project(project_id: str, payload: ReplanReq) -> dict[str, Any]:
        try:
            context = _build_review_context(project_id)
            latest_validation = context["latest_validation"]
            latest_approval = context["latest_approval"]
            actions: list[str] = []
            if latest_approval and latest_approval["status"] == "approval_required":
                actions.append("wait_for_approval")
            if latest_validation is None:
                actions.append("produce_validation_evidence")
            elif latest_validation["status"] == "failed":
                actions.append("rerun_execution_with_fix")
            elif latest_validation["status"] == "inconclusive":
                actions.append("collect_additional_evidence")
            if not actions:
                actions.append("review_completion_summary")
            return {
                "status": "ok",
                "project_id": project_id,
                "reviewer_id": payload.reviewer_id,
                "actions": actions,
                "comments": payload.comments,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/escalate")
    def escalate_project(project_id: str, payload: EscalateReq) -> dict[str, Any]:
        try:
            context = _build_review_context(project_id)
            review = create_master_review_record(
                project_id=project_id,
                reviewer_agent_id=payload.reviewer_id,
                status="needs_replan",
                review_summary=f"Escalated to level {payload.level}",
                findings={
                    "level": payload.level,
                    "reason": payload.reason,
                    "latest_validation": context["latest_validation"]["status"] if context["latest_validation"] else None,
                    "latest_approval": context["latest_approval"]["status"] if context["latest_approval"] else None,
                },
            )
            return {
                "status": "ok",
                "project_id": project_id,
                "review": review,
                "escalation_level": payload.level,
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    return router


def create_app() -> FastAPI:
    app = FastAPI(title="OldClaw Master Service", version="0.2.0-m3")
    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_review_router())
    return app


app = create_app()
