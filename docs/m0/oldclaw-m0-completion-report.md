# docs/m0/oldclaw-m0-completion-report.md

# M0 Completion Report (v0.3)

## 이번 보강 작업 내용
- **문서**: `design-baseline`, `repo-and-service-structure`, `db-schema`, `registry-spec` 를 기준 문서 수준으로 확장 (구조·목표·제약·경계 명시).
- **서비스 스켈레톤**: `manager-api`, `master-service`, `subagent-runtime`, `scheduler-worker`, `watch-worker` 에서 TODO/placeholder 를 `NotImplementedError` 혹은 HTTP 501 응답으로 교체하고 라우터/핸들러 구조를 명시.
- **pi_adapter**: `runtime/`, `tools/`, `sessions/`, `model_profiles/`, `translators/`, `contracts/` 로 디렉터리 분리, 인터페이스와 예외 기반 경계 구현.
- **마이그레이션**: `0001_init_core.sql`, `0002_registry.sql`, `0003_history_and_experience.sql`, `0004_scheduler_and_watch.sql` 를 가독성 높게 재작성, 모든 FK·CHECK·INDEX 포함.
- **History/Experience 모델**: 4‑계층 기억 구조(`histories` → `task_memories` → `experiences` → `retrieval_documents`) 를 DB 스키마와 문서에 명시.
- **Registry / API 계약**: Tool/Skill/Playbook 스키마와 seed 데이터를 실제 의미 있게 재작성, 중복 제거.
- **README**: 현재 단계가 “M0 설계 고정 + Skeleton 정식화”임을 명시.

## 아직 남은 작업 (M0 마감 전)
1. **인덱스 최적화** – 일부 복합 인덱스는 성능 테스트 후 추가 예정.
2. **정책 엔진 스텁** – `policy_engine` 패키지는 아직 구현되지 않음 (M1 로 이관).
3. **pi runtime 연동** – `pi_adapter.runtime.PiRuntime` 은 현재 `NotImplementedError` 로 남아 있음; 실제 SDK 연동은 M1 작업.

## 왜 M1 로 넘기는가
- 정책 평가, 고도화된 검증·리포팅, 모델 교체 등 **비즈니스 로직** 수준의 구현은 현재 골격을 넘어선다.
- 실제 pi SDK 연동은 **외부 의존성**이므로 별도 검증 및 CI 파이프라인이 필요.

## 임의 적용
- 일부 디렉터리 구조와 인덱스 정의는 M1 단계에서 조정될 수 있음을 명시 (위 1번 항목).

---
*본 보고서는 현재 브랜치(`m0-enhancement`) 기준이며, 다음 검수에서 M0 종료 여부를 판단한다.*
