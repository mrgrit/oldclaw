from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status


@dataclass
class ProjectCreateRequest:
    name: str
    request_text: str
    mode: str = "one_shot"


@dataclass
class AssetCreateRequest:
    name: str
    asset_type: str
    platform: str
    mgmt_ip: str
    env: str


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "manager-api"}

    return router


def create_project_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["projects"])

    @router.post("")
    def create_project(payload: ProjectCreateRequest) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project creation service is not implemented in M0.",
                "next_milestone": "M2",
                "payload": asdict(payload),
            },
        )

    @router.get("/{project_id}")
    def get_project(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project query service is not implemented in M0.",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/execute")
    def execute_project(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project execution orchestration is not implemented in M0.",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.get("/{project_id}/report")
    def get_project_report(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project report pipeline is not implemented in M0.",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

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
                "payload": asdict(payload),
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
        version="0.1.0-m0",
        description="M0 skeleton for manager-facing API contracts and routing boundaries.",
    )

    app.include_router(create_health_router())
    app.include_router(create_project_router())
    app.include_router(create_asset_router())
    app.include_router(create_playbook_router())
    app.include_router(create_evidence_router())

    return app


app = create_app()
