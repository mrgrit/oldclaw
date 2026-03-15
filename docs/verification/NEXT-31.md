# NEXT-31

## 작업 이름
M3 코드 주입 1차 / target 목록·project 연결·project target 조회 최소 경로 구현

## 수정 파일 목록
- packages/project_service/__init__.py
- apps/manager-api/src/main.py
- tools/dev/project_target_smoke.py
- tools/dev/manager_projects_target_http_smoke.py
- docs/verification/REVIEW-30.md
- docs/verification/NEXT-31.md
- docs/m3/oldclaw-m3-start-report.md
- docs/verification/WORK-31.md

## 구현 요구사항
- `packages/project_service`에 target 목록 조회, project‑target 연결, project‑target 조회 함수 추가
- `apps/manager-api/src/main.py`에 `GET /targets`, `POST /projects/{project_id}/targets/{target_id}`, `GET /projects/{project_id}/targets` 엔드포인트 추가
- smoke test 2종(`project_target_smoke.py`, `manager_projects_target_http_smoke.py`) 작성 및 검증

## 테스트 요구사항
- `tools/dev/project_target_smoke.py`가 target 목록, 프로젝트 생성, target 연결, 연결 조회, summary 확인을 수행하고 stdout에 지정된 항목을 출력
- `tools/dev/manager_projects_target_http_smoke.py`가 HTTP 레벨에서 동일 흐름을 검증하고 stdout에 지정된 항목을 출력

## M3 시작 보고서 작성 요구사항
- `docs/m3/oldclaw-m3-start-report.md`에 M2 종료 상태, target 최소 경로 도입 이유, 이번 WORK‑31 범위, 아직 구현되지 않은 항목, 대표 테스트 항목 등을 포함

## WORK-31 작성 규칙
- 현재 브랜치, HEAD 커밋, 작업 시각(UTC) 등을 실제 값으로 기록
- 수정 파일 목록, 실행 명령, pip install·compileall·각 smoke 테스트 결과를 상세히 기록
- 핵심 관찰점과 미해결 사항(3개 이내) 포함

## 실행 순서 (반드시 1개씩)
1. `git checkout main`
2. `git pull origin main`
3. 필요한 파일 수정
4. `export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'`
5. `python3 -m pip install -r requirements.txt`
6. `python3 -m compileall apps packages tools`
7. project target smoke 실행
8. manager‑api target HTTP smoke 실행
9. `git status --short`
10. 결과를 `docs/verification/WORK-31.md`에 정리
