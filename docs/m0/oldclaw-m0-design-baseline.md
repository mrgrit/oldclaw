# OldClaw M0 Design Baseline

## 1. 문서 목적

이 문서는 OldClaw의 **M0 설계 고정 기준 문서**다.  
이 문서의 목적은 이후 M1~M9 구현에서 설계 방향이 흔들리지 않도록, 용어·책임·경계·저장 전략·확장 원칙을 명시적으로 고정하는 것이다.

이 문서는 “개요 메모”가 아니라, 구현자가 다음 단계 코드를 작성할 때 참조해야 하는 **최상위 설계 기준 문서**다.  
구현 중 코드와 이 문서가 충돌하면, 기존 편의보다 이 문서의 구조적 의도를 우선한다.

---

## 2. 시스템 한 줄 정의

OldClaw는 **pi runtime을 실행 엔진으로 재사용하되**, 그 위에 다음 control-plane 계층을 올리는 정보시스템 운영 오케스트레이션 플랫폼이다.

- Master–Manager–SubAgent 역할 분리
- Asset Registry
- Policy / Approval
- Evidence / Validation
- Skill / Playbook Registry
- Batch / Continuous Execution
- History / Experience / Retrieval

즉 OldClaw는 pi를 포크해 이름만 바꾸는 프로젝트가 아니라, **pi를 embedded executor로 사용하는 운영 오케스트레이션 시스템**이다.

---

## 3. 이번 M0에서 확정하는 것

M0에서 반드시 고정하는 항목은 다음과 같다.

### 3.1 역할 분리
- **Master**
  - 고비용 추론
  - 계획 품질 보정
  - replan
  - 최종 검수
- **Manager**
  - project lifecycle 관리
  - orchestration
  - asset 선택
  - target resolve
  - playbook 실행 중재
  - evidence 수집
  - validation 연결
  - human communication
- **SubAgent**
  - 실제 시스템 작업 수행
  - 로컬 명령 실행
  - 파일 조작
  - health / capabilities 제공
  - evidence 반환

### 3.2 개념 분리
- **Tool** = 가장 작은 원자 기능
- **Skill** = 재사용 가능한 능력
- **Playbook** = skill/tool을 묶은 절차

### 3.3 관리 기준
- 등록, 정책, 상태, 기억, 이력의 기준은 **asset**
- 실행 시점에만 asset으로부터 **target**을 resolve
- target은 장기 정체성이 아니라 **파생 실행 객체**

### 3.4 완료 판정 원칙
완료는 “잘 됐다”는 문장으로 인정하지 않는다.  
다음이 모두 있어야 한다.

- 어떤 asset에 대해
- 어떤 명령/도구를
- 어떤 입력으로
- 언제 실행했고
- stdout / stderr / exit code가 무엇이며
- 어떤 검증을 수행했고
- 결과가 무엇인지

### 3.5 확장 원칙
신규 업무가 생겨도 코어를 뜯지 않는다.  
가능하면 아래 순서로 확장한다.

1. 기존 tool 재사용
2. 새 skill 추가
3. 새 playbook 추가
4. policy binding 추가

---

## 4. 이번 M0에서 확정하는 구조 경계

### 4.1 pi와 OldClaw의 경계
- pi는 실행 런타임이다.
- OldClaw는 orchestration, registry, evidence, validation, history를 담당한다.
- pi 내부에 asset/project/evidence/policy 로직을 넣지 않는다.
- OldClaw 비즈니스 로직을 pi_adapter 바깥으로 새지 않게 한다.

### 4.2 서비스 경계
- `apps/manager-api`
  - human/UI/API 진입점
  - project / asset / playbook / evidence 조회 및 요청
- `apps/master-service`
  - review / replan / escalation
- `apps/subagent-runtime`
  - health / capabilities / execution request handling
- `apps/scheduler-worker`
  - batch schedule 처리
- `apps/watch-worker`
  - continuous watch 처리

### 4.3 패키지 경계
- `packages/project_service`
  - project lifecycle
- `packages/graph_runtime`
  - LangGraph 기반 상태 전이 정의
- `packages/asset_registry`
  - asset 등록, 상태, resolve
- `packages/registry_service`
  - tool / skill / playbook registry
- `packages/evidence_service`
  - evidence 저장 및 조회
- `packages/validation_service`
  - validation execution / completion criteria
- `packages/history_service`
  - raw history
- `packages/experience_service`
  - semantic experience promotion
- `packages/retrieval_service`
  - retrieval orchestration
- `packages/pi_adapter`
  - pi runtime 연동 경계

---

## 5. 의존 방향

M0 기준 의존 방향은 아래를 따른다.

- `apps/*` → `packages/*`
- `packages/project_service` → `packages/asset_registry`, `packages/registry_service`, `packages/evidence_service`, `packages/validation_service`
- `packages/graph_runtime` → `packages/project_service`, `packages/approval_engine`, `packages/policy_engine`
- `packages/retrieval_service` → `packages/history_service`, `packages/experience_service`
- `packages/pi_adapter` → pi runtime
- `packages/*` → `packages/pi_adapter` 는 허용 가능
- `packages/pi_adapter` → `packages/project_service` 같은 역방향 의존은 금지

즉, **pi_adapter는 하부 연동 계층이지 상위 orchestration 계층이 아니다.**

---

## 6. M0에서 확정하는 데이터 저장 전략

### 6.1 PostgreSQL
구조화 저장

- assets
- targets
- projects
- job_runs
- approvals
- policies
- evidence
- validation_runs
- master_reviews
- reports
- messages
- audit_logs
- task_memories
- experiences
- retrieval_documents
- schedules
- watch_jobs
- incidents
- registry tables

### 6.2 Blob/Object Store
원본 보관

- stdout
- stderr
- generated scripts
- reports
- diff
- evidence pack

### 6.3 Vector Search
의미 검색

- playbook docs
- task memory
- experience
- reports
- precedents

---

## 7. M0에서 확정하는 history 4층 구조

OldClaw는 전체 히스토리를 context에 밀어 넣지 않는다.  
대신 아래 4층으로 다룬다.

### 7.1 Raw History
원본 이벤트/메시지/실행 로그/evidence

### 7.2 Structured Task Memory
프로젝트 종료 후 생성된 구조화 요약

### 7.3 Semantic Experience
재사용 가치 있는 패턴만 승격한 지식

### 7.4 Working Context
현재 project에 필요한 memory/experience/policy precedent를 retrieval로 조합한 작업 문맥

DB에는 Raw History, Task Memory, Experience, Retrieval Document 메타데이터를 저장한다.  
Working Context는 DB에 장기 저장되는 정체성보다, **현재 작업에서 구성되는 실행 문맥**으로 본다.

---

## 8. M0에서 확정하는 금지사항

다음은 금지한다.

- `run_stub`, `execute_stub` 같은 임시 계약을 장기 구조로 유지
- planning / execution / validation / reporting 혼합
- target-first 회귀
- evidence 없는 완료 주장
- history 전체를 context에 넣는 방식
- 신규 업무마다 코어에 예외 분기 추가
- pi 내부를 과도하게 포크
- fake success 반환
- placeholder를 장기 구조처럼 포장

---

## 9. 이번 M0에서 아직 하지 않는 것

아래는 M1 이후에 구현한다.

- pi runtime 실제 SDK 연동
- LangGraph 실제 state machine 구현
- policy parsing / evaluation 엔진 구현
- real scheduler / watch DB integration
- validation engine 실제 실행기
- A2A end-to-end 실제 통신
- vector retrieval 연동

단, 위 항목들을 **나중에 구현할 수 있도록 경계와 계약은 이번 M0에서 고정**한다.

---

## 10. 임의 적용

이번 M0에서 다음은 임의 적용으로 명시한다.

- `watch_events`를 `watch_jobs`와 별도로 둘지 여부는 운영 관찰 로그 분리를 위해 유지할 수 있다.
- 상태 컬럼의 enum 전용 타입 대신 CHECK 기반 초안을 쓸 수 있다.
- Python 앱 엔트리는 현재 FastAPI skeleton을 기준으로 두되, 이후 서비스 분리는 `routes/`, `services/`, `wiring/`으로 이동 가능하게 설계한다.

임의 적용은 구조 원칙을 깨기 위한 것이 아니라, **M0 기준선 고정을 위한 구현 편의**다.

---

## 11. M0 완료 기준

M0 완료로 인정하려면 최소 아래가 충족되어야 한다.

1. repo 구조 고정
2. 서비스/패키지 책임 경계 고정
3. DB migration 초안 존재
4. registry spec / seed 존재
5. API contract 존재
6. pi_adapter boundary 존재
7. docs/m0 기준 문서가 구현 가능한 수준으로 작성됨
8. 다음 단계 M1 범위가 문서화됨

이 문서가 유지되는 한, 이후 구현은 이 기준선 위에서만 진행한다.
