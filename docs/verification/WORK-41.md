# WORK-41

## 1. 작업 정보
- 작업 이름: manager watch event / incident 조회 API 구현
- 현재 브랜치: main
- 작업 시작 기준 HEAD: `a8c287b`

## 2. 목적
- watch worker 실행 결과를 manager-api 에서 project 단위로 조회할 수 있게 한다.
- observation 경로를 `create -> trigger -> observe`까지 닫는다.

## 3. 반영 파일
- `apps/manager-api/src/main.py`
- `docs/api/README.md`
- `docs/operations/README.md`
- `docs/verification/WORK-41.md`
- `packages/scheduler_service/__init__.py`
- `tests/contract/test_manager_scheduler_watch_contract.py`
- `tests/integration/test_manager_scheduler_watch.py`

## 4. 핵심 구현
- `GET /projects/{project_id}/watch-events`
- `GET /projects/{project_id}/incidents`
- `scheduler_service`
  - project watch event 조회
  - project incident 조회

## 5. 검증
실행 명령:

```bash
python3 -m compileall apps packages tests
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.contract.test_manager_scheduler_watch_contract -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.integration.test_manager_scheduler_watch -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
```

핵심 결과:
- scheduler/watch contract `Ran 4 tests`, `OK`
- scheduler/watch integration `Ran 3 tests`, `OK`
- 전체 스위트 통과

## 6. 남은 과제
- incident 상태 변경 / acknowledge / close
- watch event filtering / pagination
- manager aggregated worker status API
