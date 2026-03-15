from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig


class ReviewReq(BaseModel):
    project_id: str
    reviewer_id: str
    comments: str | None = None


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "master"


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
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "review not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/replan")
    def replan_project(project_id: str, plan: Any) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "replan not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/escalate")
    def escalate_project(project_id: str, level: int = 1) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "escalate not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(title="OldClaw Master Service", version="0.1.0-m1")
    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_review_router())
    return app


app = create_app()
