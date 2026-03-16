import subprocess
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig
from packages.project_service import (
    JobRunNotFoundError,
    ProjectNotFoundError,
    ProjectServiceError,
    record_subagent_execution_result,
)


class RunScriptRequest(BaseModel):
    project_id: str
    job_run_id: str
    script: str
    timeout_s: int = 120


class A2ARunResponse(BaseModel):
    status: str
    detail: dict[str, Any]


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "subagent"


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
                "run_script_execution",
                "evidence_persistence",
                "runtime_invoke_boundary",
            ],
            "note": "Local script execution and evidence persistence are available.",
        }

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig(default_role="subagent"))

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("subagent-runtime", role=payload.role)
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


def create_a2a_router() -> APIRouter:
    router = APIRouter(prefix="/a2a", tags=["a2a"])

    @router.post("/run_script")
    def run_script(payload: RunScriptRequest) -> A2ARunResponse:
        try:
            completed = subprocess.run(
                ["/bin/bash", "-lc", payload.script],
                text=True,
                capture_output=True,
                timeout=payload.timeout_s,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            try:
                recorded = record_subagent_execution_result(
                    project_id=payload.project_id,
                    job_run_id=payload.job_run_id,
                    command_text=payload.script,
                    stdout=stdout,
                    stderr=(stderr + "\nscript execution timed out").strip(),
                    exit_code=124,
                )
            except (ProjectNotFoundError, JobRunNotFoundError) as record_exc:
                raise HTTPException(status_code=404, detail={"message": str(record_exc)}) from record_exc
            except ProjectServiceError as record_exc:
                raise HTTPException(status_code=400, detail={"message": str(record_exc)}) from record_exc

            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "message": "script execution timed out",
                    "project_id": payload.project_id,
                    "job_run_id": payload.job_run_id,
                    "timeout_s": payload.timeout_s,
                    "job_run": recorded["job_run"],
                    "evidence": recorded["evidence"],
                },
            ) from exc

        try:
            recorded = record_subagent_execution_result(
                project_id=payload.project_id,
                job_run_id=payload.job_run_id,
                command_text=payload.script,
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
            )
        except (ProjectNotFoundError, JobRunNotFoundError) as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

        result_status = "ok" if completed.returncode == 0 else "failed"
        return A2ARunResponse(
            status=result_status,
            detail={
                "project_id": payload.project_id,
                "job_run_id": payload.job_run_id,
                "command": payload.script,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "exit_code": completed.returncode,
                "job_run": recorded["job_run"],
                "evidence": recorded["evidence"],
            },
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OldClaw SubAgent Runtime",
        version="0.2.0-m3",
        description="M3 subagent runtime with local script execution and evidence persistence.",
    )

    app.include_router(create_health_router())
    app.include_router(create_capabilities_router())
    app.include_router(create_runtime_router())
    app.include_router(create_a2a_router())

    return app


app = create_app()
