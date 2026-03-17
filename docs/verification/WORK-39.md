# WORK-39

## 1. 작업 정보
- 작업 이름: manager scheduler/watch control-plane 최소 API 구현
- 현재 브랜치: main
- 작업 시작 기준 HEAD: `6693e85`

## 2. 목적
- manager-api 에서 schedule / watch job 을 생성하고 조회할 수 있게 한다.
- worker run-once 구현과 control-plane table 생성 경로를 한 묶음으로 닫는다.
- contract / integration 검증을 추가한다.

## 3. 반영 파일
- `apps/manager-api/src/main.py`
- `docs/api/README.md`
- `docs/operations/README.md`
- `docs/verification/WORK-39.md`
- `packages/scheduler_service/__init__.py`
- `tests/contract/test_manager_scheduler_watch_contract.py`
- `tests/integration/test_manager_scheduler_watch.py`

## 4. 핵심 구현
- `POST /projects/{project_id}/schedules`
- `GET /projects/{project_id}/schedules`
- `POST /projects/{project_id}/watch-jobs`
- `GET /projects/{project_id}/watch-jobs`
- `scheduler_service`
  - schedule row 생성/조회
  - watch job row 생성/조회

## 5. 검증
실행 명령:

```bash
python3 -m compileall apps packages tests
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.contract.test_manager_scheduler_watch_contract -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest tests.integration.test_manager_scheduler_watch -v
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
```

핵심 결과:
- manager scheduler/watch contract `Ran 2 tests`, `OK`
- manager scheduler/watch integration `Ran 2 tests`, `OK`
- 전체 스위트 통과

## 6. 남은 과제
- schedule / watch update / pause / resume / delete
- manager -> scheduler/watch worker run trigger
- watch event / incident 조회 API
