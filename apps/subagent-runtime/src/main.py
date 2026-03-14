from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status


@dataclass
class RunScriptRequest:
    project_id: str
    job_run_id: str
    script: str
    timeout_s: int = 120


@dataclass
class A2ARunResponse:
    status: str
    detail: dict[str, Any]


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "subagent-runtime"}

    return router


def create_capabilities_router() -> APIRouter:
    router = APIRouter(tags=["capabilities"])

    @router.get("/capabilities")
    def capabilities() -> dict[str, Any]:
        return {
            "service": "subagent-runtime",
            "capabilities": [
                "health",
                "capabilities",
                "run_script_request_boundary",
                "evidence_return_boundary",
            ],
            "note": "Actual execution engine is not implemented in M0.",
        }

    return router


def create_a2a_router() -> APIRouter:
    router = APIRouter(prefix="/a2a", tags=["a2a"])

    @router.post("/run_script")
    def run_script(payload: RunScriptRequest) -> A2ARunResponse:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "SubAgent execution engine is not implemented in M0.",
                "next_milestone": "M3",
                "request": asdict(payload),
                "reason": "M0 only fixes the boundary and request contract.",
            },
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OldClaw SubAgent Runtime",
        version="0.1.0-m0",
        description="M0 skeleton for subagent runtime boundaries and A2A request contracts.",
    )

    app.include_router(create_health_router())
    app.include_router(create_capabilities_router())
    app.include_router(create_a2a_router())

    return app


app = create_app()
