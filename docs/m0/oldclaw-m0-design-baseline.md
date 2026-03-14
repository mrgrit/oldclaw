# docs/m0/oldclaw-m0-design-baseline.md

# OldClaw M0 Design Baseline (Reference Implementation)

## 1. 목표
- **OldClaw**는 **pi runtime** 위에 구축되는 **Control‑Plane Orchestration Platform**이다.
- 핵심 원칙: **Asset‑first**, **Evidence‑first**, **Tool < Skill < Playbook** 계층화.
- 서비스는 **Manager API**, **Master Service**, **SubAgent Runtime**, **Scheduler Worker**, **Watch Worker** 로 명확히 분리한다.

## 2. 핵심 설계 결정 (M0 고정)
| 영역 | 결정 사항 | 이유 |
|------|------------|------|
| 데이터 모델 | `assets`, `projects`, `job_runs`, `evidence` 등 핵심 테이블을 **UUID PK**, `created_at/updated_at` 타임스탬프 기본 제공 | 일관된 식별자와 추적 가능성 보장 |
| Tool/Skill/Playbook 경계 | Tool은 **저수준 시스템 호출**만 수행; Skill은 Tool 조합 + 검증; Playbook은 Skill 순차 실행 및 정책 바인딩 | 책임 분리, 검증 가능, 정책 적용 용이 |
| Service 책임 | Manager → 외부 API 제공, Project/Asset CRUD 및 Playbook 트리거<br>Master → Review, Re‑plan, Escalation 로직<br>SubAgent → Health, Capability 열람, A2A 스크립트 실행<br>Scheduler → `schedules` 기반 JobRun 생성<br>Watch → `watch_jobs` 모니터링 및 이벤트 처리 | 책임 명확화, 독립 배포 가능 |
| 모델 프로파일 | `packages/pi_adapter/model_profiles` 에 `manager`, `master`, `subagent` 각각의 모델·temperature 정의 | 향후 M1에서 모델 교체 용이 |

## 3. M1 로 넘기는 항목 (보강 후 이관)
- 정책 엔진 상세 구현 (policy_engine 패키지)
- 고도화된 검증/리포팅 파이프라인
- 실제 pi SDK 연동 및 세션 관리
- 복합 인덱스 및 성능 튜닝

---
*본 문서는 현재 M0 단계에서 확정된 설계와, 다음 마일스톤(M1)으로 이관될 항목을 구분해 기록합니다.*
