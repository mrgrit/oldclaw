# docs/m0/oldclaw-m0-db-schema.md

# Database Schema (M0 Draft)

## 공통 컬럼
All tables include:
- `id` **UUID** primary key (default `uuid_generate_v4()`)
- `created_at` TIMESTAMP WITH TIME ZONE default `now()`
- `updated_at` TIMESTAMP WITH TIME ZONE (optional, where mutable)

## 핵심 테이블 요약
| Table | 목적 | 주요 컬럼 | FK / 관계 | 인덱스(예시) |
|-------|------|-----------|-----------|-------------|
| **assets** | 관리 대상 인프라 자산 | `name`, `type`, `platform`, `metadata` | – | `UNIQUE(name, type)` |
| **asset_endpoints** | 자산이 제공하는 엔드포인트 | `asset_id`, `endpoint_type`, `value`, `is_primary` | `asset_id → assets(id)` | `INDEX(asset_id, endpoint_type)` |
| **targets** | 접근 대상 URL/Endpoint | `asset_id`, `base_url`, `health` | `asset_id → assets(id)` | `INDEX(asset_id)` |
| **projects** | 오케스트레이션 작업 단위 | `name`, `status`, `current_stage`, `mode` | – | `INDEX(status)`, `INDEX(current_stage)` |
| **project_assets** | 프로젝트 ↔ 자산 매핑 | `project_id`, `asset_id`, `scope_role` | `project_id → projects(id)`, `asset_id → assets(id)` | `PRIMARY KEY(project_id, asset_id)` |
| **job_runs** | Playbook·Skill 실행 인스턴스 | `project_id`, `playbook_id`, `skill_id`, `asset_id`, `target_id`, `status`, `stage` | 여러 FK ↔ 상위 엔티티 | `INDEX(project_id)`, `INDEX(status, stage)` |
| **evidence** | 실행 결과·로그 저장 | `project_id`, `job_run_id`, `tool_name`, `command_text`, `stdout_ref`, `stderr_ref`, `exit_code` | `project_id → projects(id)`, `job_run_id → job_runs(id)` | `INDEX(project_id, job_run_id)` |
| **validation_runs** | 검증 결과 기록 | `project_id`, `job_run_id`, `validator_name`, `status` | FK ↔ 프로젝트/JobRun | `INDEX(project_id, status)` |
| **master_reviews** | 검토·승인 기록 | `project_id`, `reviewer_agent_id`, `status` | `project_id → projects(id)` | `INDEX(project_id, status)` |
| **reports** | 최종 보고서 저장 | `project_id`, `report_type`, `body_ref` | `project_id → projects(id)` | `INDEX(project_id, report_type)` |
| **messages** | 시스템·사용자 메시지 | `project_id`, `job_run_id`, `sender`, `content` | FK ↔ 프로젝트/JobRun | `INDEX(project_id)` |
| **audit_logs** | 감사 로그 | `event_type`, `actor`, `target`, `outcome` | – | `INDEX(event_type, occurred_at)` |
| **schedules** | 주기적 작업 정의 | `project_id`, `schedule_type`, `cron_expr`, `next_run`, `enabled` | `project_id → projects(id)` | `INDEX(next_run)` |
| **histories** | 원시 실행 로그·이벤트 | `project_id`, `job_run_id`, `event`, `context` | FK ↔ 프로젝트/JobRun | `INDEX(project_id, created_at)` |
| **task_memories** | 작업 종료 후 구조화된 요약 | `job_run_id`, `memory_type`, `payload` | `job_run_id → job_runs(id)` | `INDEX(job_run_id)` |
| **experiences** | 재사용 가능한 지식/패턴 | `asset_id`, `skill_id`, `outcome`, `result` | FK ↔ assets/skills | `INDEX(asset_id, skill_id)` |
| **retrieval_documents** | 검색용 문서 저장 | `source`, `content`, `metadata` | – | `FULLTEXT(content)` |
| **watch_jobs** | Watch 엔진 잡 정의 | `project_id`, `job_type`, `schedule_id`, `status` | FK ↔ 프로젝트/스케줄 | `INDEX(status)` |
| **watch_events** | Watch 이벤트 기록 | `watch_job_id`, `event_type`, `payload` | `watch_job_id → watch_jobs(id)` | `INDEX(event_type, occurred_at)` |
| **incidents** | 인시던트 기록 | `project_id`, `severity`, `status`, `opened_at`, `closed_at` | `project_id → projects(id)` | `INDEX(severity, status)` |

## 설계 이유 요약
- **FK** 로 데이터 무결성을 강제하고, **인덱스** 로 조회 효율을 확보한다.
- `status`/`stage` 컬럼은 **CHECK** 로 열거형(enum)값 제한을 두어 일관성을 유지한다.
- 4‑계층 기억 구조(`histories` → `task_memories` → `experiences` → `retrieval_documents`) 를 명시적으로 반영했다.

---
*임의 적용*: 일부 복합 인덱스는 M1 단계에서 성능 테스트 후 조정될 수 있습니다.*
