# WORK-23

## 1. 작업 정보
- 작업 이름: M2 사전정비 / migration 0003·0004 외래키 타입 정합성 수정 및 재적용
- 현재 브랜치: main
- 현재 HEAD 커밋: 70272c529038521e84f7f35e1022f79f37e15230
- 작업 시각: 2026-03-15T00:31:48Z

## 2. 이번 작업에서 수정한 파일
- migrations/0003_history_and_experience.sql
- migrations/0004_scheduler_and_watch.sql
- docs/verification/WORK-23.md

## 3. 실행한 명령 목록
```
1. git checkout main
2. git pull origin main
3. export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'
4. psql "$DATABASE_URL" -c '\\conninfo'
5. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS watch_events CASCADE;'
6. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS watch_jobs CASCADE;'
7. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS schedules CASCADE;'
8. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS incidents CASCADE;'
9. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS histories CASCADE;'
10. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS task_memories CASCADE;'
11. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS experiences CASCADE;'
12. psql "$DATABASE_URL" -c 'DROP TABLE IF EXISTS retrieval_documents CASCADE;'
13. psql "$DATABASE_URL" -f migrations/0003_history_and_experience.sql
14. psql "$DATABASE_URL" -f migrations/0004_scheduler_and_watch.sql
15. psql "$DATABASE_URL" -c '\\dt'
16. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM histories;'
17. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM task_memories;'
18. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM experiences;'
19. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM retrieval_documents;'
20. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM schedules;'
21. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM watch_jobs;'
22. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM watch_events;'
23. psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM incidents;'
```

## 4. DROP 정리 결과
| Command | stdout | stderr | exit code |
|---------|--------|--------|-----------|
| DROP watch_events | NOTICE:  table "watch_events" does not exist, skipping\nDROP TABLE |  | 0 |
| DROP watch_jobs | NOTICE:  table "watch_jobs" does not exist, skipping\nDROP TABLE |  | 0 |
| DROP schedules | NOTICE:  table "schedules" does not exist, skipping\nDROP TABLE |  | 0 |
| DROP incidents | NOTICE:  table "incidents" does not exist, skipping\nDROP TABLE |  | 0 |
| DROP histories | NOTICE:  table "histories" does not exist, skipping\nDROP TABLE |  | 0 |
| DROP task_memories | NOTICE:  table "task_memories" does not exist, skipping\nDROP TABLE |  | 0 |
| DROP experiences | NOTICE:  table "experiences" does not exist, skipping\nDROP TABLE |  | 0 |
| DROP retrieval_documents | DROP TABLE |  | 0 |

## 5. migration 0003 재적용 결과
- **stdout:**
```
BEGIN
CREATE EXTENSION
psql:migrations/0003_history_and_experience.sql:3: NOTICE:  extension "uuid-ossp" already exists, skipping
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE TABLE
CREATE INDEX
COMMIT
```
- **stderr:** *(none)*
- **exit code:** 0

## 6. migration 0004 재적용 결과
- **stdout:**
```
BEGIN
CREATE EXTENSION
psql:migrations/0004_scheduler_and_watch.sql:3: NOTICE:  extension "uuid-ossp" already exists, skipping
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE TABLE
CREATE INDEX
CREATE TABLE
CREATE INDEX
CREATE INDEX
COMMIT
```
- **stderr:** *(none)*
- **exit code:** 0

## 7. 스키마 검증 결과
- **`\dt` 결과:**
```
               List of relations
 Schema |        Name         | Type  |  Owner  
--------+---------------------+-------+---------
 public | asset_endpoints     | table | oldclaw
 public | assets              | table | oldclaw
 public | audit_logs          | table | oldclaw
 public | evidence            | table | oldclaw
 public | experiences         | table | oldclaw
 public | histories           | table | oldclaw
 public | incidents           | table | oldclaw
 public | job_runs            | table | oldclaw
 public | master_reviews      | table | oldclaw
 public | messages            | table | oldclaw
 public | playbook_bindings   | table | oldclaw
 public | playbook_steps      | table | oldclaw
 public | playbooks           | table | oldclaw
 public | project_assets      | table | oldclaw
 public | projects            | table | oldclaw
 public | reports             | table | oldclaw
 public | retrieval_documents | table | oldclaw
 public | schedules           | table | oldclaw
 public | skill_tools         | table | oldclaw
 public | skills              | table | oldclaw
 public | targets             | table | oldclaw
 public | task_memories       | table | oldclaw
 public | tools               | table | oldclaw
 public | validation_runs     | table | oldclaw
 public | watch_events        | table | oldclaw
 public | watch_jobs          | table | oldclaw
(26 rows)
```
- **histories count:** 0
- **task_memories count:** 0
- **experiences count:** 0
- **retrieval_documents count:** 0
- **schedules count:** 0
- **watch_jobs count:** 0
- **watch_events count:** 0
- **incidents count:** 0

## 8. 핵심 관찰점
- UUID vs TEXT 외래키 타입 불일치 문제 **해소**됨 (FK 모두 TEXT와 일치).
- `histories`, `task_memories`, `experiences`, `retrieval_documents`, `schedules`, `watch_jobs`, `watch_events`, `incidents` 등 **전체 테이블이 정상 생성**됨.
- 기본 스키마가 완전하게 적용되어 M2 단계에서 실제 `project_service`·`graph_runtime` 구현을 진행할 수 있는 **준비 상태**.
- 현재 모든 신규 테이블은 비어 있으므로 데이터가 없어도 정상 동작 확인 가능.
- 남은 한계 (5개 이내):
  1. 기존 `0003`·`0004` 외에 다른 migration 파일이 존재한다면 타입 정합성 추가 검토 필요.
  2. `project_service`·`graph_runtime` 내부 로직 아직 구현되지 않음 (코드 작성 필요).
  3. `manager-api` `/projects` 엔드포인트 로직 구현 전까지 실제 프로젝트 흐름 테스트 불가.
  4. 외부 서비스(예: pi_adapter)와 연동 테스트는 아직 진행되지 않음.
  5. 테스트/CI 파이프라인에 migration 검증 단계 추가 필요.

## 9. 미해결 사항
1. `0003`·`0004` 외에 다른 migration 파일에서 동일한 UUID/TEXT 타입 충돌이 있는지 전역 검증 필요.
2. `manager-api` `/projects` 라우터 구현 전까지 엔드‑포인트 테스트가 불가능.
3. 실제 비즈니스 로직이 아직 없으므로 전체 워크플로우 테스트를 위한 추가 구현이 필요.
