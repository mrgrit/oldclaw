# WORK-38

## 1. 작업 정보
- 작업 이름: 테스트 계층 확장 및 scheduler/watch minimal worker 구현
- 현재 브랜치: main
- 작업 시작 기준 HEAD: `e95075e`

## 2. 목적
- unit / contract / integration / e2e 테스트 체계를 실제 운영 가능한 수준으로 확장한다.
- scheduler-worker, watch-worker 의 placeholder 를 DB-backed minimal worker 로 교체한다.
- 마일스톤 진행 상태를 현재 코드 기준으로 문서화한다.

## 3. 반영 파일
- `Makefile`
- `README.md`
- `apps/scheduler-worker/src/main.py`
- `apps/watch-worker/src/main.py`
- `docs/api/README.md`
- `docs/architecture/README.md`
- `docs/operations/README.md`
- `docs/verification/WORK-38.md`
- `packages/approval_engine/__init__.py`
- `packages/history_service/__init__.py`
- `packages/project_service/__init__.py`
- `packages/scheduler_service/__init__.py`
- `tests/contract/test_manager_api_contract.py`
- `tests/contract/test_master_service_contract.py`
- `tests/contract/test_subagent_runtime_contract.py`
- `tests/contract/test_worker_contract.py`
- `tests/e2e/test_http_service_flows.py`
- `tests/integration/support.py`
- `tests/integration/test_manager_execution.py`
- `tests/integration/test_manager_history.py`
- `tests/integration/test_manager_review.py`
- `tests/integration/test_worker_flows.py`
- `tests/unit/test_approval_engine.py`
- `tests/unit/test_history_summary.py`
- `tests/unit/test_master_review_decision.py`
- `tests/unit/test_policy_engine.py`
- `tests/unit/test_report_summary.py`
- `tests/unit/test_validation_summary.py`

## 4. 핵심 구현
- 테스트 체계
  - `tests/unit`
  - `tests/contract`
  - `tests/integration`
  - `tests/e2e`
- worker 구현
  - scheduler `POST /run-once`
  - watch `POST /run-once`
  - due schedule 로드 및 `last_run` / `next_run` 갱신
  - watch event / incident / history 생성
- helper 분리
  - validation summary
  - report summary
  - task memory summary
  - approval override 판정

## 5. 검증
실행 명령:

```bash
python3 -m compileall apps packages tools tests
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.contract.test_worker_contract -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.integration.test_worker_flows -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests/e2e -p 'test_*.py' -v
```

핵심 결과:
- 전체 스위트 `Ran 41 tests`, `OK`
- `tests/e2e` `Ran 5 tests`, `OK`
- worker contract `Ran 2 tests`, `OK`
- worker integration `Ran 2 tests`, `OK`

## 6. 남은 과제
- scheduler/watch CRUD control plane
- recurring schedule semantics 고도화
- watch 기반 incident escalation / project generation
- retrieval / experience runtime 활용
- playbook branching / distributed execution
