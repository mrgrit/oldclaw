# WORK-33

## 작업 정보
- 작업 이름: M3-3 레포 정합성 복구 + M3 minimal playbook path 구현
- 현재 브랜치: main
- 현재 HEAD 커밋: 3da1679c4bac69e5b9d37634894d95ce572a95a7
- 작업 시각: 2026-03-15T12:18:13Z

## 수정한 파일 목록
- packages/graph_runtime/__init__.py
- packages/pi_adapter/runtime/__init__.py
- packages/project_service/__init__.py
- apps/manager-api/src/main.py
- tools/dev/manager_projects_target_http_smoke.py
- tools/dev/project_playbook_smoke.py
- tools/dev/manager_projects_playbook_http_smoke.py
- tools/dev/m3_integrated_smoke.py
- docs/verification/WORK-33.md

## 실행한 명령 목록
- git checkout main
- git pull origin main
- export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'
- python3 -m pip install -r requirements.txt
- python3 -m compileall apps packages tools
- PYTHONPATH=. python3 tools/dev/project_target_smoke.py
- PYTHONPATH=. python3 tools/dev/manager_projects_target_http_smoke.py
- PYTHONPATH=. python3 tools/dev/project_playbook_smoke.py
- PYTHONPATH=. python3 tools/dev/manager_projects_playbook_http_smoke.py
- PYTHONPATH=. python3 tools/dev/m2_integrated_smoke.py
- PYTHONPATH=. python3 tools/dev/m3_integrated_smoke.py
- git status --short
- git add .
- git status --short
- git commit -m "M3-3 reconcile repo and add minimal playbook path"
- git push origin main

## pip install 결과
- stdout: (omitted, all packages already satisfied)
- stderr: *(none)*
- exit code: 0

## compileall 결과
- stdout: (listing of compiled modules, compilation succeeded without errors)
- stderr: *(none)*
- exit code: 0

## 각 smoke 결과
### target service smoke
- 명령: `PYTHONPATH=. python3 tools/dev/project_target_smoke.py`
- stdout:
```
TARGET_COUNT: 1
PROJECT_ID: prj_e250e08f5bba
LINKED_TARGET_ID: tgt_dummy
PROJECT_TARGET_COUNT: 1
SUMMARY_TARGET_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

### target HTTP smoke
- 명령: `PYTHONPATH=. python3 tools/dev/manager_projects_target_http_smoke.py`
- stdout:
```
HTTP_TARGET_COUNT: 1
HTTP_PROJECT_ID: prj_cae9d1b6227a
HTTP_LINKED_TARGET_ID: tgt_dummy
HTTP_PROJECT_TARGET_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

### playbook service smoke
- 명령: `PYTHONPATH=. python3 tools/dev/project_playbook_smoke.py`
- stdout:
```
PLAYBOOK_COUNT: 1
PROJECT_ID: prj_b1dfd0dce54d
LINKED_PLAYBOOK_ID: pb_dummy
PROJECT_PLAYBOOK_COUNT: 1
SUMMARY_PLAYBOOK_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

### playbook HTTP smoke
- 명령: `PYTHONPATH=. python3 tools/dev/manager_projects_playbook_http_smoke.py`
- stdout:
```
HTTP_PLAYBOOK_COUNT: 1
HTTP_PROJECT_ID: prj_e200a335c2f9
HTTP_LINKED_PLAYBOOK_ID: pb_dummy
HTTP_PROJECT_PLAYBOOK_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

### M2 integrated smoke
- 명령: `PYTHONPATH=. python3 tools/dev/m2_integrated_smoke.py`
- stdout:
```
M2_PROJECT_ID: prj_6b6eb1da1a23
M2_ASSET_COUNT: 1
M2_EVIDENCE_COUNT: 1
M2_LINKED_ASSET_ID: ast_dummy
M2_PROJECT_ASSET_COUNT: 1
M2_FINAL_STAGE: close
M2_FINAL_STATUS: completed
M2_REPORT_ID: rpt_523c240c2bb7
```
- stderr: *(none)*
- exit code: 0

### M3 integrated smoke
- 명령: `PYTHONPATH=. python3 tools/dev/m3_integrated_smoke.py`
- stdout:
```
M3_PROJECT_ID: prj_383a25b056ea
M3_ASSET_COUNT: 1
M3_TARGET_COUNT: 1
M3_PLAYBOOK_COUNT: 1
M3_LINKED_ASSET_ID: ast_dummy
M3_LINKED_TARGET_ID: tgt_dummy
M3_LINKED_PLAYBOOK_ID: pb_dummy
M3_SUMMARY_ASSET_COUNT: 1
M3_SUMMARY_TARGET_COUNT: 1
M3_SUMMARY_PLAYBOOK_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

## git add 결과
- `git add .` performed, all modified files staged.

## git commit 결과
- 커밋 `3da1679` 생성, 메시지 "M3-3 reconcile repo and add minimal playbook path"

## git push 결과
- 원격 `origin/main`에 성공적으로 푸시됨.

## 핵심 관찰점
- `packages/graph_runtime/__init__.py`에 `GraphRuntimeError`, `require_transition` 구현이 정상적으로 반영돼 import mismatch 해결.
- `packages/pi_adapter/runtime/__init__.py`에서 존재하지 않던 `PiRuntime` export를 제거하고 `RuntimeError`만 export함.
- playbook 목록 응답에서 `enabled`가 `status` 로, `created_at`이 `updated_at` 로 매핑된 것이 확인됨.
- project‑playbook 연결이 `projects.playbook_id` 컬럼을 업데이트하는 방식으로 구현되어 있음.
- target HTTP 엔드포인트를 `/projects/{project_id}/targets/{target_id}` 로 바로 잡아 호출 성공.
- 모든 smoke 테스트가 기대 출력과 exit code 0을 반환, 기존 M2 경로도 깨지지 않음.

## 미해결 사항
- 실제 playbook 실행 로직(런타임 연동) 아직 구현되지 않음.
- 정책/approval 연동 및 그래프 고도화 계획 수립 필요.
- CI 파이프라인에 전체 M3 통합 smoke 자동 테스트 추가 필요.
