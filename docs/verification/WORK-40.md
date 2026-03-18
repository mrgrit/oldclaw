# WORK-40

## 1. 작업 정보
- 작업 이름: manager -> scheduler/watch worker trigger 최소 경로 구현
- 현재 브랜치: main
- 작업 시작 기준 HEAD: `7bd68df`

## 2. 목적
- manager-api 에서 scheduler-worker / watch-worker `run-once`를 직접 트리거할 수 있게 한다.
- 테스트 harness 에 worker in-process 주입을 추가한다.
- contract / integration 검증을 추가한다.

## 3. 반영 파일
- `apps/manager-api/src/main.py`
- `docs/api/README.md`
- `docs/operations/README.md`
- `docs/verification/WORK-40.md`
- `tests/contract/test_manager_worker_trigger_contract.py`
- `tests/integration/support.py`
- `tests/integration/test_manager_worker_dispatch.py`

## 4. 핵심 구현
- `POST /projects/scheduler/run-once`
- `POST /projects/watch/run-once`
- default HTTP dispatch
  - `OLDCLAW_SCHEDULER_URL`
  - `OLDCLAW_WATCH_URL`
- 테스트용 in-process worker runner 주입

## 5. 검증
실행 명령:

```bash
python3 -m compileall apps packages tests
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.contract.test_manager_worker_trigger_contract -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.integration.test_manager_worker_dispatch -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
```

핵심 결과:
- worker trigger contract `Ran 2 tests`, `OK`
- worker trigger integration `Ran 2 tests`, `OK`
- 전체 스위트 통과

## 6. 남은 과제
- manager -> worker health / status aggregation
- watch event / incident 조회 API
- schedule/watch update / pause / resume / delete
