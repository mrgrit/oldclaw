# OldClaw

OldClaw는 **pi runtime 기반 정보시스템 운영/보안 작업 오케스트레이션 플랫폼**이다. 
pi를 단순히 호출하는 보조 도구가 아니라, **pi를 실행 런타임으로 사용하고 OldClaw가 control‑plane을 담당하는 구조**를 목표로 한다.

프로젝트의 핵심 목적은 자연어 요청을 내부망 운영 작업으로 바로 흘려보내는 것이 아니라, 
그 요청을 **프로젝트 단위로 접수하고**, **단계별 상태 전이(plan → execute → validate → report → close)** 로 관리하며, 
결과를 **evidence/report 중심으로 기록 가능한 형태**로 남기는 것이다.

즉 OldClaw는 “한 번 실행하고 끝나는 스크립트 묶음”이 아니라, 
향후 asset, target, playbook, approval, policy, history를 포함하는 
**검증 가능하고 확장 가능한 운영 오케스트레이션 control‑plane**을 지향한다.

---

## 1. 시스템 소개

OldClaw는 다음 상황을 해결하기 위해 설계되었다.

- 내부망 또는 통제된 환경에서 운영/보안 작업을 구조화해서 수행하고 싶다.
- 자연어 요청을 바로 실행하지 않고, 프로젝트/단계/증빙 단위로 관리하고 싶다.
- 실행 결과를 stdout/stderr 감상이 아니라 evidence/report 로 남기고 싶다.
- 신규 업무를 코어 수정이 아니라 asset / skill / playbook 추가 중심으로 수용하고 싶다.
- 장기적으로 approval, policy, history‑aware retrieval, continuous watch 모드까지 확장하고 싶다.

OldClaw는 이 목표를 위해 다음 철학을 따른다.

- **pi는 실행 런타임 엔진**
- **OldClaw는 control‑plane**
- **asset‑first**
- **evidence‑first**
- **history‑aware, context‑light**
- **구조 우선**
- **신규 업무는 코어 수정이 아니라 skill / playbook 추가로 수용**

---

## 2. 시스템 컨셉

OldClaw의 기본 구조는 아래와 같다.

- **Master**: 고수준 판단, 정책, 승인, 향후 경험/지식 축적과 연결될 상위 오케스트레이션 계층
- **Manager**: 프로젝트 lifecycle, 상태 전이, API, registry 접근을 담당하는 중심 control‑plane
- **SubAgent / Runtime**: 실제 환경에서 명령을 수행하는 실행 계층
- **pi runtime**: 실제 작업 실행을 담당하는 런타임 엔진

현재 구현은 전체 비전 중 **M2 완료 + M3 핵심 control-plane 상당 부분 구현 상태**에 해당한다. 즉, 장기 계획 전체가 완성된 것은 아니지만, manager/subagent/master 중심의 핵심 동작 경로는 이미 usable 수준으로 확보됐다.

- DB‑backed project lifecycle
- evidence 기반 validation / report / close
- asset / target / playbook 연결
- subagent script execution + evidence persistence
- manager `execute/run`, `execute/auto`, `run/auto`
- policy gate / approval 저장 / 승인 후 재실행
- master review / replan / escalate
- close 시 history + task memory persistence
- scheduler / watch worker의 DB-backed minimal `run-once`

---

## 3. 개발 계획 개요

OldClaw의 개발은 마일스톤 기반으로 진행된다.

- **M0 설계 고정**
  - repo 구조
  - 문서/스키마/registry 기본 틀
- **M1 pi Runtime Adapter**
  - pi CLI wrapper 경로 정리
  - Ollama 연동 확인
  - 비대화형 호출 경로 검증
- **M2 Manager Core**
  - PostgreSQL 기반 project lifecycle
  - plan → execute → validate → report → close 최소 전이
  - report/evidence 최소 경로
  - asset 최소 경로
- **M3 이후**
  - target resolution
  - playbook step branching / execution 고도화
  - history / experience / retrieval 실제 활용
  - continuous / watch / scheduler 고도화
  - policy data-driven 일반화

---

## 4. 현재 구현 상태 (M2 완료 / M3 진행 중 기준)

현재 기준으로 실제 확인된 것은 아래와 같다.

### 구현 완료
- PostgreSQL 기반 최소 project lifecycle
- project create/get
- plan / execute / validate / report / close 최소 전이
- report finalize 최소 경로
- minimal evidence 생성
- project evidence 조회
- asset 목록 조회
- project에 asset 연결
- project linked assets 조회
- target 목록 조회
- project에 target 연결
- project linked targets 조회
- playbook 목록 조회
- project에 playbook 연결
- project linked playbooks 조회
- `execute/run`, `execute/auto`, `run/auto`, `run/auto/review`
- policy check, approval 생성/조회/승인
- subagent 로컬 스크립트 실행 및 evidence 저장
- master review / replan / escalate
- history event / task memory 생성
- scheduler-worker / watch-worker `run-once`
- unit / contract / integration / e2e 테스트 확보

### 아직 남아 있는 것
- target resolution pipeline
- playbook branching / step execution 고도화
- policy rule 의 seed/data 일반화
- retrieval / experience 실제 runtime 활용
- continuous watch / scheduler orchestration 고도화
- CI 확대 및 자동 검증 강화

---

## 5. 저장소 구조 개요

프로젝트는 크게 아래와 같이 구성된다.

- `apps/manager-api`
  - FastAPI 기반 manager control‑plane API
- `packages/project_service`
  - project lifecycle, report/evidence, asset 연결 등 최소 서비스 로직
- `packages/pi_adapter`
  - pi runtime 연동 계층
- `packages/graph_runtime`
  - 상태 전이/오케스트레이션 골격
- `migrations`
  - PostgreSQL 스키마
- `registry`
  - tool / skill / playbook / target / policy / asset seed/registry
- `tools/dev`
  - 개발용 smoke / verification 스크립트
- `docs`
  - 계획서, 마일스톤 보고서, 검수/다음작업 문서

---

## 6. 실행 및 검증

대표 검증은 `unittest` 계층과 개발용 smoke를 함께 사용한다.

```bash
python3 -m compileall apps packages tools tests
```

```bash
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
```

이 검증은 최소한 아래 범위를 확인해야 한다.

- contract / integration / e2e 회귀
- project 생성
- plan / execute / validate / report / close
- approval / review / history / scheduler / watch 최소 경로

---

## 7. 작업 운영 규칙

이 저장소의 작업은 아래 규칙을 따른다.

- main 브랜치만 사용
- 코어 설계와 코드 본문은 ChatGPT가 작성
- 에이전트는 반영 / 실행 / 테스트 / 결과 보고 담당
- 명령은 반드시 1개씩 따로 실행
- 검수 없는 완료 주장 금지
- 검수/지시/작업결과는 문서로 남김

문서 체계:

- `docs/verification/REVIEW-XX.md`
- `docs/verification/NEXT-XX.md`
- `docs/verification/WORK-XX.md`

---

## 8. 주의

README는 현재 구현 상태를 반영하는 대표 문서다.
없는 기능을 완성된 것처럼 적지 않는다.
특히 retrieval/experience 실제 활용, advanced playbook branching, continuous watch orchestration은 아직 **계획 범위**이며 현재 구현은 최소 usable control-plane 수준이다.
