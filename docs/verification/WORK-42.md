# WORK-42

## 1. 작업 정보
- 작업 이름: manager incident acknowledge / close API 구현
- 현재 브랜치: main
- 작업 시작 기준 HEAD: `cc8df9d`

## 2. 목적
- watch worker가 생성한 incident를 manager-api 에서 상태 전이할 수 있게 한다.
- observation 경로를 `observe -> acknowledge -> close`까지 닫는다.

## 3. 반영 파일
- `apps/manager-api/src/main.py`
- `docs/api/README.md`
- `docs/operations/README.md`
- `docs/verification/WORK-42.md`
- `packages/scheduler_service/__init__.py`
- `tests/contract/test_manager_scheduler_watch_contract.py`
- `tests/integration/test_manager_scheduler_watch.py`

## 4. 핵심 구현
- `POST /projects/{project_id}/incidents/{incident_id}/acknowledge`
- `POST /projects/{project_id}/incidents/{incident_id}/close`
- `scheduler_service`
  - incident status update
  - 허용 상태: `acknowledged`, `closed`

## 5. 검증
실행 명령:

```bash
python3 -m compileall apps packages tests
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.contract.test_manager_scheduler_watch_contract -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.integration.test_manager_scheduler_watch -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
```

핵심 결과:
- scheduler/watch contract `Ran 6 tests`, `OK`
- scheduler/watch integration `Ran 4 tests`, `OK`
- 전체 스위트 통과

## 6. 남은 과제
- incident reassignment / severity update
- incident filtering / pagination
- manager aggregated worker status API
