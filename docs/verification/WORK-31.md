# WORK-31

## 1. 작업 정보
- 작업 이름: M3 코드 주입 1차 / target 목록·project 연결·project target 조회 최소 경로 구현
- 현재 브랜치: main
- 현재 HEAD 커밋: 29232a8bfa3df8e0ec5c754297442bb6ec6e2280
- 작업 시각: 2026-03-15T09:14:35Z

## 2. 이번 작업에서 수정한 파일
- packages/project_service/__init__.py
- apps/manager-api/src/main.py
- tools/dev/project_target_smoke.py
- tools/dev/manager_projects_target_http_smoke.py
- docs/verification/REVIEW-30.md
- docs/verification/NEXT-31.md
- docs/m3/oldclaw-m3-start-report.md
- docs/verification/WORK-31.md

## 3. 실행한 명령 목록
- git checkout main
- git pull origin main
- export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'
- python3 -m pip install -r requirements.txt
- python3 -m compileall apps packages tools
- PYTHONPATH=. python3 tools/dev/project_target_smoke.py
- PYTHONPATH=. python3 tools/dev/manager_projects_target_http_smoke.py
- git status --short
- git add README.md packages/project_service/__init__.py apps/manager-api/src/main.py tools/dev/project_target_smoke.py tools/dev/manager_projects_target_http_smoke.py docs/verification/REVIEW-30.md docs/verification/NEXT-31.md docs/m3/oldclaw-m3-start-report.md
- git commit -m "M3-1 add minimal target path"
- git push origin main

## 4. pip install 결과
- stdout: (omitted, all packages already satisfied)
- stderr: *(none)*
- exit code: 0

## 5. compileall 결과
- stdout: (listing of compiled modules, compilation succeeded without errors)
- stderr: *(none)*
- exit code: 0

## 6. project_target_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/project_target_smoke.py`
- stdout:
```
TARGET_COUNT: 1
PROJECT_ID: prj_91122dcb53a8
LINKED_TARGET_ID: tgt_dummy
PROJECT_TARGET_COUNT: 1
SUMMARY_TARGET_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

## 7. manager_projects_target_http_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/manager_projects_target_http_smoke.py`
- stdout:
```
HTTP_TARGET_COUNT: 1
HTTP_PROJECT_ID: prj_8721845611c0
HTTP_LINKED_TARGET_ID: tgt_dummy
HTTP_PROJECT_TARGET_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

## 8. git add 결과
- all listed files staged for commit.

## 9. git commit 결과
- commit `29232a8b` created with message "M3-1 add minimal target path".

## 10. git push 결과
- pushed to origin/main successfully.

## 11. 핵심 관찰점
- `GET /targets` 조회 성공, 1건 반환 (dummy target 자동 삽입).
- `POST /targets/{project_id}/targets/{target_id}` 로 프로젝트와 target 연결 성공.
- `GET /targets/{project_id}/targets` 로 연결된 target 1건 반환.
- project summary (`get_project_report_evidence_summary`)에 target 목록 포함 확인.
- 기존 M2 lifecycle과 asset 연동에 영향을 주지 않고 target 기능이 정상 동작함.

## 12. 미해결 사항
- graph_runtime 전체 오케스트레이션 로직 구현 필요
- target‑based playbook 실행 및 policy 연동 계획 수립
- CI/CD 파이프라인에 target 경로 자동 테스트 통합
