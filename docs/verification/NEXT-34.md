# NEXT-34

## 작업 이름
WORK-34 - 레포 정합성 복구 + manager-api 정상화 + minimal playbook path 실제 구현

## 목표
- `packages/graph_runtime/__init__.py` 정합성 복구
- `packages/pi_adapter/runtime/__init__.py` 정합성 복구
- `apps/manager-api/src/main.py` 정상 import 가능 상태 복구
- target 서비스 경로 `/projects/{project_id}/targets/{target_id}` 구현
- playbook 최소 경로 실제 구현 (조회, 연결, 조회)
- `tools/dev` smoke 스크립트 추가 및 검증
- README 및 문서 업데이트

## 범위
수정 파일:
- `packages/graph_runtime/__init__.py`
- `packages/pi_adapter/runtime/__init__.py`
- `packages/project_service/__init__.py`
- `apps/manager-api/src/main.py`
- `tools/dev/manager_projects_target_http_smoke.py`
- `tools/dev/project_playbook_smoke.py`
- `tools/dev/manager_projects_playbook_http_smoke.py`
- `tools/dev/m3_integrated_smoke.py`
- `README.md`
- `docs/m3/oldclaw-m3-start-report.md`
- `docs/verification/REVIEW-33.md`
- `docs/verification/NEXT-34.md`
- `docs/verification/WORK-34.md`
