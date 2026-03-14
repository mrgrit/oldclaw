# WORK-16

## 1. 작업 정보
- 작업 이름: M1 코드 주입 준비 / 교체 대상 파일 현행 본문 고정
- 현재 브랜치: main
- 현재 HEAD 커밋: 5500d8b6381886ad097bdc8eba6a8dd83a615a48
- 작업 시각: 2026-03-15 02:05:12 UTC

## 2. 이번 작업에서 수정한 파일
- docs/verification/WORK-16.md
- 그 외 수정 파일이 있으면 추가
- 없으면 “없음” 명시

## 3. 현재 Ollama 성공 설정 요약
- settings path: `~/.pi/agent/models.json`
- provider: `ollama`
- baseUrl: `http://<IP>:<PORT>/v1`
- api: `openai-completions`
- apiKey: `ollama`
- model: `gpt-oss:120b`
- 성공 명령: `pi --provider ollama --model gpt-oss:120b -p "Reply with exactly: OK"`
- 성공 응답: `OK`

## 4. 교체 대상 파일 목록
- packages/pi_adapter/runtime/client.py
- packages/pi_adapter/runtime/__init__.py
- packages/pi_adapter/tools/__init__.py
- packages/pi_adapter/tools/tool_bridge.py
- packages/pi_adapter/sessions/__init__.py
- packages/pi_adapter/model_profiles/__init__.py
- packages/pi_adapter/translators/__init__.py
- packages/pi_adapter/contracts/__init__.py
- .env.example
- docs/m1/oldclaw-m1-plan.md (없음 명시)
- docs/m1/oldclaw-m1-completion-report.md (없음 명시)
- tests/integration/ (없음 명시)
- tools/dev/ (없음 명시)

## 5. 교체 대상 파일 현재 본문
--- packages/pi_adapter/runtime/client.py ---
```python
from dataclasses import dataclass
from typing import Any


@dataclass
class PiRuntimeConfig:
    model_profile: str
    session_mode: str
    timeout_s: int


class PiRuntimeClient:
    """
    Boundary adapter between OldClaw and the external pi runtime.

    This class exists to make the integration point explicit.
    OldClaw orchestration logic must not be implemented here.
    Asset, project, policy, evidence, and validation domain logic must stay
    outside the pi adapter layer.
    """

    def __init__(self, config: PiRuntimeConfig) -> None:
        self.config = config

    def open_session(self, session_name: str) -> str:
        raise NotImplementedError(
            "pi runtime session integration is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )

    def invoke_model(self, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(
            "pi runtime model invocation is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )

    def close_session(self, session_id: str) -> None:
        raise NotImplementedError(
            "pi runtime session closing is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )
```
--- packages/pi_adapter/runtime/__init__.py ---
```python
# packages/pi_adapter/runtime/__init__.py
from .client import PiRuntime

class RuntimeError(NotImplementedError):
    pass
```
--- packages/pi_adapter/tools/__init__.py ---
```python
# packages/pi_adapter/tools/__init__.py
"""Tool Bridge definitions.

Each concrete tool class should implement `execute(**kwargs)` and return a
standard result dict compatible with OldClaw evidence schema.
"""

class BaseTool:
    def __init__(self, runtime):
        self.runtime = runtime

    def execute(self, **kwargs):
        raise NotImplementedError("Tool execution not implemented for M0")
```
--- packages/pi_adapter/tools/tool_bridge.py ---
```python
# packages/pi_adapter/tools/tool_bridge.py
"""Concrete tool bridge implementations.

Each tool class should inherit from `BaseTool` and implement `execute`.
In M0 they raise NotImplementedError.
"""

from . import BaseTool

class RunCommandTool(BaseTool):
    def execute(self, command: str, timeout: int = 60):
        raise NotImplementedError("RunCommandTool execution not implemented in M0")

# Additional tool classes can be added here following the same pattern.
```
--- packages/pi_adapter/sessions/__init__.py ---
```python
# packages/pi_adapter/sessions/__init__.py
"""Session management for pi runtime.

`PiSession` encapsulates a model‑specific chat session.
"""

class PiSession:
    def __init__(self, model_name: str):
        self.model_name = model_name
        # Placeholder – actual SDK integration pending
        raise NotImplementedError("PiSession not available in M0")
```
--- packages/pi_adapter/model_profiles/__init__.py ---
```python
# packages/pi_adapter/model_profiles/__init__.py
"""Model profile definitions.

A profile declares which model, temperature, and system prompt to use for a
given OldClaw role (manager, master, subagent, etc.).
"""

MODEL_PROFILES = {
    "manager": {"model": "gpt-4o-mini", "temperature": 0.2},
    "master": {"model": "gpt-4o", "temperature": 0.1},
    "subagent": {"model": "gpt-4o-mini", "temperature": 0.3},
}

# In M0 these are static; M1 may load from config or DB.
```
--- packages/pi_adapter/translators/__init__.py ---
```python
# packages/pi_adapter/translators/__init__.py
"""Translation layer between OldClaw types and pi runtime types.

Functions here convert OldClaw request/response structures to the format
expected by the pi SDK and vice‑versa.
"""

def to_pi_message(oldclaw_obj: dict) -> dict:
    """Translate an OldClaw dict to a pi SDK message payload.
    """
    # Placeholder implementation – in M0 we simply forward the dict.
    return oldclaw_obj

def from_pi_message(pi_msg: dict) -> dict:
    """Translate a pi SDK response back to OldClaw format.
    """
    return pi_msg
```
--- packages/pi_adapter/contracts/__init__.py ---
```python
# packages/pi_adapter/contracts/__init__.py
"""Contract definitions for data exchanged with pi runtime.

These define the JSON schema for tool invocation requests and responses.
"""

TOOL_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"type": "string"},
        "args": {"type": "object"},
    },
    "required": ["tool", "args"]
}

TOOL_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {},
        "status": {"type": "string"}
    },
    "required": ["result"]
}
```
--- .env.example ---
```dotenv
# Environment variables example
# DATABASE_URL=postgresql://oldclaw:password@localhost:5432/oldclaw
# PI_MODEL=default
# pi adapter settings (M1)
OLDCLAW_PI_PROVIDER=pi
OLDCLAW_PI_BASE_URL=
OLDCLAW_PI_API_KEY=
OLDCLAW_PI_MANAGER_MODEL=
OLDCLAW_PI_MASTER_MODEL=
OLDCLAW_PI_SUBAGENT_MODEL=
OLDCLAW_PI_DEFAULT_TIMEOUT_S=120
OLDCLAW_PI_SESSION_MODE=service
```
--- apps/manager-api/src/main.py ---
```python
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
```
--- apps/master-service/src/main.py ---
```python
from fastapi import FastAPI, APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Any

class ReviewReq(BaseModel):
    project_id: str
    reviewer_id: str
    comments: str | None = None


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health():
        return {"status": "master ok"}

    return router


def create_review_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["review"])

    @router.post("/{project_id}/review")
    def review_project(project_id: str, req: ReviewReq):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "review not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/replan")
    def replan_project(project_id: str, plan: Any):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "replan not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/escalate")
    def escalate_project(project_id: str, level: int = 1):
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
    app = FastAPI(title="OldClaw Master Service", version="0.1.0-m0")
    app.include_router(create_health_router())
    app.include_router(create_review_router())
    return app


app = create_app()
```
--- apps/subagent-runtime/src/main.py ---
```python
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
```
## 6. 관련 디렉터리 트리
- `find packages/pi_adapter -maxdepth 3 -type f | sort`
```
packages/pi_adapter/contracts/__init__.py
packages/pi_adapter/__init__.py
packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/runtime/client.py
packages/pi_adapter/runtime/__init__.py
packages/pi_adapter/sessions/__init__.py
packages/pi_adapter/tools/__init__.py
packages/pi_adapter/tools/tool_bridge.py
packages/pi_adapter/translators/__init__.py
```
- `find apps -maxdepth 3 -type f | sort`
```
apps/manager-api/src/main.py
apps/master-service/src/main.py
apps/scheduler-worker/src/main.py
apps/subagent-runtime/src/main.py
apps/watch-worker/src/main.py
```
- `find docs/m1 -maxdepth 3 -type f | sort 2>/dev/null || true`
```
docs/m1/README.md
```
- `find tests -maxdepth 3 -type f | sort 2>/dev/null || true`
```
tests/contract/__init__.py
tests/e2e/__init__.py
tests/integration/__init__.py
tests/unit/__init__.py
```
- `find tools -maxdepth 3 -type f | sort 2>/dev/null || true`
```
(no output)
```

## 7. M1 코드 주입 시 꼭 유지해야 할 사실
- `pi` 성공 설정 경로: `~/.pi/agent/models.json`
- 성공 모델: `gpt-oss:120b`
- 비대화형 호출 방식: `-p` 플래그 사용
- wrapper가 직접 호출할 권장 실행 경로: `pi`
- 조사 완료된 항목: provider, baseUrl, api, apiKey, 모델 리스트, 성공 호출 검증
- 아직 미구현인 항목: 실제 pi runtime 연동 로직, 세션 관리, 도구 구현, 모델 프로파일 로드

## 8. 미해결 사항
1. Ollama 서버가 인증을 요구하지 않으므로 현재 `apiKey`는 더미값이지만, 다른 환경에서는 필요할 수 있다.
2. `models.json`에 추가 Ollama 모델을 넣을 경우 동일 포맷 유지가 필요하다.
3. `pi`가 향후 `OLLAMA_API_KEY` 같은 환경변수를 지원할지 여부는 미확정.
