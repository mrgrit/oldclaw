import time
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException

from packages.project_service import ProjectNotFoundError
from packages.scheduler_service import SchedulerServiceError, run_scheduler_once


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "scheduler-worker"}

    return router


def create_run_router() -> APIRouter:
    router = APIRouter(tags=["scheduler"])

    @router.post("/run-once")
    def run_once() -> dict[str, Any]:
        try:
            result = run_scheduler_once()
            return {"status": "ok", **result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except SchedulerServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    return router


def run_loop(poll_interval: int = 60) -> None:
    while True:
        try:
            run_scheduler_once()
        except Exception as exc:  # noqa: BLE001
            print(f"scheduler loop error: {exc}")
        time.sleep(poll_interval)


def create_app() -> FastAPI:
    app = FastAPI(title="OldClaw Scheduler Worker", version="0.2.0-m3")
    app.include_router(create_health_router())
    app.include_router(create_run_router())
    return app


app = create_app()


if __name__ == "__main__":
    run_loop()
