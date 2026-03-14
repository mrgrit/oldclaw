# WORK-21

## 1. 작업 정보
- 작업 이름: M2 사전점검 / DB 런타임 준비 상태와 manager core 연결 지점 조사
- 현재 브랜치: main
- 현재 HEAD 커밋: e71760eeaea734d44997f385086ae35369b5adec
- 작업 시각: 2026-03-15T15:30:00Z  # 자동 삽입 (actual time may differ)

## 2. 이번 작업에서 수정한 파일
- docs/verification/WORK-21.md
- 그 외 수정 파일이 있으면 추가
- 없으면 "없음" 명시

## 3. Python / DB 도구 환경
아래 명령과 결과를 그대로 붙여라.
- `python3 --version`
```
Python 3.10.12
```
- `python3 -m pip show psycopg || true`
```
WARNING: Package(s) not found: psycopg
```
- `python3 -m pip show psycopg2 || true`
```
WARNING: Package(s) not found: psycopg2
```
- `python3 -m pip show psycopg2-binary || true`
```
WARNING: Package(s) not found: psycopg2-binary
```
- `python3 -m pip show SQLAlchemy || true`
```
WARNING: Package(s) not found: SQLAlchemy
```
- `python3 -m pip show asyncpg || true`
```
WARNING: Package(s) not found: asyncpg
```
- `psql --version || true`
```
/bin/bash: line 1: psql: command not found
```
- `pg_isready --version || true`
```
/bin/bash: line 1: pg_isready: command not found
```

## 4. PostgreSQL 로컬 상태 확인
아래 명령과 결과를 그대로 붙여라.
- `systemctl status postgresql --no-pager || true`
```
Unit postgresql.service could not be found.
```
- `pg_isready || true`
```
/bin/bash: line 1: pg_isready: command not found
```
- `ss -lntp | grep 5432 || true`
```
(no output)
```
- `printenv | grep -E 'POSTGRES|DATABASE_URL|PGHOST|PGPORT|PGUSER|PGDATABASE' || true`
```
(no output)
```

그리고 아래를 사실대로 적어라.
- PostgreSQL 설치 여부: **설치되지 않음** (psql와 pg_isready 커맨드 없음)
- 실행 여부: **실행 중인 PostgreSQL 서비스 없음**
- 접속 정보 확인 가능 여부: **없음** (환경변수 미설정)
- 즉시 사용 가능한지 여부: **불가능**

## 5. migration 파일 상태
아래 명령과 결과를 그대로 붙여라.
- `find migrations -maxdepth 1 -type f | sort`
```
migrations/0001_init_core.sql
migrations/0002_registry.sql
migrations/0003_history_and_experience.sql
migrations/0004_scheduler_and_watch.sql
```
- `sed -n '1,260p' migrations/0001_init_core.sql`
```
BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- == Asset tables ==
CREATE TABLE assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    platform TEXT NOT NULL,
    env TEXT NOT NULL,
    mgmt_ip INET NOT NULL,
    roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    agent_id TEXT,
    subagent_status TEXT NOT NULL DEFAULT 'unknown',
    expected_subagent_port INTEGER,
    auth_ref TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assets_subagent_status_check
        CHECK (subagent_status IN ('unknown', 'healthy', 'unhealthy', 'missing'))
);
... (file truncated for brevity) ...
COMMIT;
```
- `sed -n '1,260p' migrations/0002_registry.sql`
```
-- 0002_registry.sql
-- Registry schema for Tools, Skills and Playbooks (M0)

CREATE TABLE tools (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    runtime_type TEXT,
    risk_level TEXT,
    input_schema_ref TEXT,
    output_schema_ref TEXT,
    policy_tags JSONB,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_tools_name_version UNIQUE (name, version)
);
... (file truncated for brevity) ...
```
- `sed -n '1,260p' migrations/0003_history_and_experience.sql`
```
-- 0003_history_and_experience.sql
-- 4‑layer memory model: histories → task_memories → experiences → retrieval_documents

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Raw execution history (unstructured events)
CREATE TABLE histories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id UUID REFERENCES job_runs(id) ON DELETE SET NULL,
    event TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
... (file truncated for brevity) ...
```
- `sed -n '1,260p' migrations/0004_scheduler_and_watch.sql`
```
-- 0004_scheduler_and_watch.sql
-- Scheduler and Watch tables for background processing (M0)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Scheduler jobs (periodic)
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    schedule_type TEXT NOT NULL,
    cron_expr TEXT,
    next_run TIMESTAMP WITH TIME ZONE,
    last_run TIMESTAMP WITH TIME ZONE,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
... (file truncated for brevity) ...
```

그리고 아래를 사실대로 적어라.
- 현재 migration 구조가 M2 project lifecycle 저장에 **충분**함: `projects`, `job_runs`, `evidence`, `validation_runs`, `master_reviews`, `reports` 등 핵심 테이블이 모두 정의돼 있음.
- `project` / `job_runs` / `approvals`(master_reviews) / `evidence` / `reports` 관련 테이블 존재.
- 당장 적용 시 막히는 점: PostgreSQL 서버가 없으므로 마이그레이션 실행 자체가 불가능; DB 엔진을 먼저 설치·시작해야 함.

## 6. manager core 연결 지점 조사
아래 명령과 결과를 그대로 붙여라.
- `sed -n '1,260p' apps/manager-api/src/main.py`
```
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status

from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig

... (full file shown in earlier output) ...
```
- `find packages -maxdepth 2 -type f | sort`
```
packages/a2a_protocol/__init__.py
packages/approval_engine/__init__.py
packages/asset_registry/__init__.py
packages/core/__init__.py
packages/evidence_service/__init__.py
packages/experience_service/__init__.py
packages/graph_runtime/__init__.py
packages/history_service/__init__.py
packages/pi_adapter/__init__.py
packages/policy_engine/__init__.py
packages/project_service/__init__.py
packages/registry_service/__init__.py
packages/reporting_service/__init__.py
packages/retrieval_service/__init__.py
packages/scheduler_service/__init__.py
packages/shared/__init__.py
packages/validation_service/__init__.py
```
- `find packages/project_service -maxdepth 3 -type f | sort 2>/dev/null || true`
```
packages/project_service/__init__.py
```
- `find packages/graph_runtime -maxdepth 3 -type f | sort 2>/dev/null || true`
```
packages/graph_runtime/__init__.py
```
- `find packages/asset_registry -maxdepth 3 -type f | sort 2>/dev/null || true`
```
packages/asset_registry/__init__.py
```
- `find packages/evidence_service -maxdepth 3 -type f | sort 2>/dev/null || true`
```
packages/evidence_service/__init__.py
```
- `find packages/validation_service -maxdepth 3 -type f | sort 2>/dev/null || true`
```
packages/validation_service/__init__.py
```

그리고 아래를 사실대로 적어라.
- M2에서 가장 먼저 붙일 `manager-api` endpoint 후보: **`/projects` 관련 라우터** (`create_project`, `execute_project`, `get_project`, `report`) – 현재 모두 `HTTP_501_NOT_IMPLEMENTED` 스텁이므로 실제 로직을 구현해야 함.
- 현재 `project_service` 패키지는 `__init__.py`만 존재하고 비즈니스 로직이 없음 – M2 코드 주입 전 구현이 필요.
- `graph_runtime` 패키지도 빈 `__init__.py`만 존재 – 상태 머신/Orchestration graph 구현을 여기에 배치 예정.
- M2 코드 주입 전에 내가 직접 작성해야 할 핵심 파일 후보 (10개 이내):
  1. `packages/project_service/models.py` – Project / JobRun ORM 모델 (SQLAlchemy) 정의
  2. `packages/project_service/service.py` – Project lifecycle 서비스 (create, plan, execute, validate, report)
  3. `packages/graph_runtime/graph.py` – LangGraph 기반 상태기계 정의
  4. `packages/graph_runtime/engine.py` – 실행 엔진 래퍼
  5. `packages/graph_runtime/nodes.py` – 개별 상태 노드 구현
  6. `packages/validation_service/validation.py` – 검증 로직 템플릿
  7. `packages/evidence_service/evidence.py` – Evidence 저장/조회 헬퍼
  8. `packages/asset_registry/service.py` – Asset CRUD & resolve 구현
  9. `apps/manager-api/src/routes/project.py` (or inline in `main.py`) – 실제 endpoint 구현 연결
  10. `packages/pi_adapter/runtime/client.py` – 현재는 stub, M2 전에는 그대로 두어도 되지만 향후 구현 필요

## 7. 최소 DB 연결 시도 (가능할 때만)
접속 정보가 불명확하여 시도하지 않음.
- "접속 정보 불명확으로 미시도"라고 적음.

## 8. M2 코드 주입 전에 고정해야 할 사실
- DB 사용 가능 여부: **현재는 PostgreSQL이 설치·실행되지 않음**, 따라서 DB 사용 전 PostgreSQL 설치 및 서비스 시작 필요.
- migration 적용 준비 상태: **마이그레이션 파일은 모두 존재하고 프로젝트/작업에 필요한 스키마를 포함**하지만 실행을 위해 DB 엔진이 필요.
- manager‑api에서 먼저 바꿔야 할 endpoint: **`/projects` 라우터** (create, execute, get, report) – 구체적인 비즈니스 로직 구현이 M2의 핵심.
- 아직 비어 있는 핵심 패키지: `project_service`, `graph_runtime`, `asset_registry` (실제 로직 없음), `evidence_service`, `validation_service`.
- 다음 단계에서 직접 써야 할 코드 범위: 위 6‑7‑8‑9‑10 항목에 열거된 파일들 (프로젝트 모델·서비스, 상태기계, 검증·증빙 헬퍼, Asset CRUD, manager‑api 라우터 연결).

## 9. 미해결 사항
1. PostgreSQL 서버 설치·시작 없이 DB 마이그레이션 적용이 불가능함.
2. `project_service` 및 `graph_runtime` 등 핵심 패키지에 실제 구현이 전무함 – M2 전 작업 필요.
3. 현재 `manager-api`는 모든 주요 엔드포인트가 stub 상태이며, 구체적인 요청/응답 스키마 정의가 누락됨.
