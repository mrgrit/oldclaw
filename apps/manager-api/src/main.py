from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.pi_adapter.runtime import PiRuntimeClient, PiRuntimeConfig
from packages.project_service import (
    ProjectNotFoundError,
    ProjectServiceError,
    ProjectStageError,
    close_project,
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

    @router.post("/{project_id}/execute")
    def execute_project(project_id: str) -> dict[str, Any]:
        try:
            result = execute_project_record(project_id)
            return {"status": "ok", "result": result}
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
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectStageError as exc:
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


def create_app() -> FastAPI:
    app = FastAPI(
        title="OldClaw Manager API",
        version="0.3.0-m3",
        description="Manager API with minimal lifecycle, evidence, asset, target, and playbook routes.",
    )

    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_project_router())
    app.include_router(create_asset_router())
    app.include_router(create_target_router())
    app.include_router(create_playbook_router())

    return app


app = create_app()
