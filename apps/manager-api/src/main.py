from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig
from packages.project_service import (
    ProjectNotFoundError,
    ProjectServiceError,
    create_minimal_evidence_record,
    create_project_record,
    execute_project_record,
    finalize_report_stage_record,
    get_project_record,
    get_project_report,
    plan_project_record,
    validate_project_record,
)


class ProjectCreateRequest(BaseModel):
    name: str
    request_text: str
    mode: str = "one_shot"


class AssetCreateRequest(BaseModel):
    name: str
    asset_type: str
    platform: str
    mgmt_ip: str
    env: str


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "manager"


class MinimalEvidenceRequest(BaseModel):
    command: str
    stdout: str
    stderr: str = ""
    exit_code: int = 0


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "manager-api"}

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig(default_role="manager"))

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("manager-api-runtime", role=payload.role)
            result = client.invoke_model(
                payload.prompt,
                {
                    "session_id": session_id,
                    "role": payload.role,
                },
            )
            client.close_session(session_id)
            return {
                "status": "ok",
                "session_id": session_id,
                "result": result,
            }
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


def create_project_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["projects"])

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": str(exc)},
            ) from exc
        except ProjectServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(exc)},
            ) from exc

    @router.get("/{project_id}")
    def get_project(project_id: str) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": str(exc)},
            ) from exc

    @router.post("/{project_id}/execute")
    def execute_project(project_id: str) -> dict[str, Any]:
        try:
            result = execute_project_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": str(exc)},
            ) from exc
        except ProjectServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(exc)},
            ) from exc

    @router.post("/{project_id}/validate")
    def validate_project(project_id: str) -> dict[str, Any]:
        try:
            result = validate_project_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": str(exc)},
            ) from exc
        except ProjectServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(exc)},
            ) from exc

    @router.post("/{project_id}/report/finalize")
    def finalize_report(project_id: str) -> dict[str, Any]:
        try:
            result = finalize_report_stage_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": str(exc)},
            ) from exc
        except ProjectServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(exc)},
            ) from exc

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(exc)},
            ) from exc

    @router.get("/{project_id}/report")
    def get_project_report_endpoint(project_id: str) -> dict[str, Any]:
        try:
            report = get_project_report(project_id)
            return {"status": "ok", "report": report}
        except ProjectNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": str(exc)},
            ) from exc

    return router


def create_asset_router() -> APIRouter:
    router = APIRouter(prefix="/assets", tags=["assets"])

    @router.post("")
    def create_asset(payload: AssetCreateRequest) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Asset registry service is not implemented in M0.",
                "next_milestone": "M4",
                "payload": payload.model_dump(),
            },
        )

    @router.get("/{asset_id}")
    def get_asset(asset_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Asset query service is not implemented in M0.",
                "next_milestone": "M4",
                "asset_id": asset_id,
            },
        )

    @router.post("/{asset_id}/resolve")
    def resolve_asset(asset_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Asset resolve flow is not implemented in M0.",
                "next_milestone": "M4",
                "asset_id": asset_id,
            },
        )

    return router


def create_playbook_router() -> APIRouter:
    router = APIRouter(prefix="/playbooks", tags=["playbooks"])

    @router.get("")
    def list_playbooks() -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Playbook registry query is not implemented in M0.",
                "next_milestone": "M6",
            },
        )

    @router.post("/{playbook_id}/run")
    def run_playbook(playbook_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Playbook execution is not implemented in M0.",
                "next_milestone": "M6",
                "playbook_id": playbook_id,
            },
        )

    return router


def create_evidence_router() -> APIRouter:
    router = APIRouter(prefix="/evidence", tags=["evidence"])

    @router.get("/projects/{project_id}")
    def get_project_evidence(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Evidence query is not implemented in M0.",
                "next_milestone": "M5",
                "project_id": project_id,
            },
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OldClaw Manager API",
        version="0.2.2-m2",
        description="M2 manager API with minimal DB-backed lifecycle, report finalize, and evidence routes.",
    )

    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_project_router())
    app.include_router(create_asset_router())
    app.include_router(create_playbook_router())
    app.include_router(create_evidence_router())

    return app


app = create_app()
