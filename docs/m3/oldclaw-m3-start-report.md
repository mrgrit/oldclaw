# OldClaw M3 Start Report

## M2 종료 상태 요약
- M2 단계에서는 프로젝트 lifecycle (plan → execute → validate → report → close) 가 구현되었고,
- evidence 및 report 저장, asset 목록 조회·연결·조회가 정상 동작함을 smoke 테스트와 HTTP 검증을 통해 확인함.
- 통합 smoke (`tools/dev/m2_integrated_smoke.py`) 로 전체 흐름을 한 번에 검증했으며, README와 완료보고서가 정합성을 유지함.

## 왜 M3 첫 작업을 target 최소 경로로 시작하는가
- 운영에서는 **대상 시스템(Target)** 에 대한 정보와 접근 관리가 필수이며, 향후 playbook 실행, 정책 적용, 상태 모니터링 등 모든 상위 기능이 target 정보를 기반으로 작동한다.
- M2에서 asset과 evidence 흐름을 확보했으므로, target 개념을 도입해 **프로젝트 ↔ target** 연결을 최소화하고,
  이후 단계에서 target‑based playbook 바인딩 및 policy 연동을 자연스럽게 확장할 수 있다.

## 이번 WORK-31에서 추가한 범위
- `targets` 테이블 조회 (`GET /targets`)
- 프로젝트에 target 연결 (`POST /projects/{project_id}/targets/{target_id}`)
- 프로젝트에 연결된 target 목록 조회 (`GET /projects/{project_id}/targets`)
- project summary에 linked targets 리스트 포함 (`get_project_report_evidence_summary` 확장)

## 아직 하지 않은 것 (M3 이후 계획)
- 실제 runtime dispatch 를 통한 target 명령 실행
- playbook 와 target 매핑 / 실행
- approval / policy gate 연동
- graph_runtime 고도화 및 전체 오케스트레이션 로직
- CI/CD 파이프라인에 target 경로 테스트 자동화

## 대표 테스트 항목
- `tools/dev/project_target_smoke.py` 로 전체 흐름 검증 (target 조회 → project 생성 → 연결 → 조회 → summary)
- `tools/dev/manager_projects_target_http_smoke.py` 로 HTTP 레벨 검증 (GET /targets, POST /projects, POST /projects/{id}/targets/{tid}, GET /projects/{id}/targets)

## 현재 상태 (과장 없이)
- DB schema 에 `targets` 테이블이 존재하고, 최소 컬럼(`id, asset_id, base_url, resolved_at, health, metadata`)을 보유한다.
- 프로젝트‑target 연결을 위한 `project_targets` 테이블을 런타임에 생성하고, 기본적인 멱등 삽입을 지원한다.
- API 레이어에서 위 엔드포인트를 제공하며, 존재하지 않는 프로젝트/target 에는 404 응답을 반환한다.
- 아직 target‑specific playbook 실행이나 정책 적용 로직은 구현되지 않았다.
