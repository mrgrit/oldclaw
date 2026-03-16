# WORK-37

## 1. 작업 정보
- 작업 이름: manager execute/auto, policy gate, approval flow 구현 및 검증
- 현재 브랜치: main
- 작업 시작 기준 HEAD: `c7268a8`
- 작업 기록 시각(UTC): 2026-03-16 16:22:31 UTC

## 2. 이번 작업의 목적
- manager 중심의 실제 실행 경로를 `execute/run`, `execute/auto`, `run/auto`까지 확장한다.
- subagent 실제 스크립트 실행과 evidence 저장을 연결한다.
- playbook/skill/tool seed 해석을 auto execution plan에 반영한다.
- evidence 기반 validation 과 final report summary 를 구현한다.
- policy gate 와 approval 저장/승인 후 재실행 경로를 추가한다.

## 3. 이번 작업에서 반영한 파일
- `Makefile`
- `README.md`
- `apps/manager-api/src/main.py`
- `apps/subagent-runtime/src/main.py`
- `docs/api/README.md`
- `docs/architecture/README.md`
- `docs/operations/README.md`
- `docs/playbooks/README.md`
- `packages/approval_engine/__init__.py`
- `packages/pi_adapter/runtime/__init__.py`
- `packages/policy_engine/__init__.py`
- `packages/project_service/__init__.py`
- `pyproject.toml`
- `tools/dev/project_report_evidence_smoke.py`
- `tools/dev/subagent_run_script_smoke.py`
- `tools/dev/manager_subagent_dispatch_smoke.py`
- `tools/dev/manager_execute_run_smoke.py`
- `tools/dev/manager_execute_plan_smoke.py`
- `tools/dev/manager_execute_auto_smoke.py`
- `tools/dev/manager_run_auto_smoke.py`
- `tools/dev/manager_execute_failure_smoke.py`
- `tools/dev/manager_policy_gate_smoke.py`
- `tools/dev/manager_approval_flow_smoke.py`

## 4. 핵심 구현 내용
- `subagent-runtime`
  - `/a2a/run_script` 구현
  - 로컬 `/bin/bash -lc` 실행
  - 실행 결과를 `job_runs`/`evidence`에 반영
- `project_service`
  - manager execute job + subagent child job 연결
  - playbook/skill seed 해석
  - auto execution script 생성
  - skill fragment evidence 생성
  - evidence 기반 validation run 기록
  - final report summary 집계
- `manager-api`
  - `/projects/{id}/dispatch/subagent`
  - `/projects/{id}/execute/run`
  - `/projects/{id}/execute/plan`
  - `/projects/{id}/execute/auto`
  - `/projects/{id}/run/auto`
  - `/projects/{id}/policy-check`
  - `/projects/{id}/approvals`
  - `/projects/{id}/approvals/{approval_id}/approve`
- `policy_engine`
  - sensitive playbook / high risk / continuous mode / target 존재 여부 기준 판정
- `approval_engine`
  - approval request 저장
  - approval 조회
  - 승인 처리
  - 승인된 policy override 허용

## 5. 실행 및 검증
실행 명령:

```bash
python3 -m compileall apps packages tools
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/subagent_run_script_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_subagent_dispatch_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_execute_run_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_execute_plan_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_execute_auto_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_run_auto_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/project_report_evidence_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_execute_failure_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_policy_gate_smoke.py
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 tools/dev/manager_approval_flow_smoke.py
```

핵심 결과:
- `subagent_run_script_smoke`
  - `SUBAGENT_HTTP_STATUS: ok`
  - `SUBAGENT_JOB_STATUS: completed`
  - `SUBAGENT_EVIDENCE_COUNT: 1`
- `manager_subagent_dispatch_smoke`
  - manager job과 subagent child job 연결 확인
- `manager_execute_run_smoke`
  - parent job linkage 확인
- `manager_execute_plan_smoke`
  - playbook/target/skill/tool preview 확인
- `manager_execute_auto_smoke`
  - `EXECUTE_AUTO_REQUIRED_SKILLS: collect_web_latency_facts`
  - `EXECUTE_AUTO_REQUIRED_TOOLS: run_command`
  - `EXECUTE_AUTO_SKILL_EVIDENCE_COUNT: 1`
- `manager_run_auto_smoke`
  - `RUN_AUTO_VALIDATION_STATUS: passed`
  - `RUN_AUTO_FINAL_STAGE: close`
- `project_report_evidence_smoke`
  - `VALIDATION_STATUS: inconclusive`
- `manager_execute_failure_smoke`
  - `EXECUTE_FAILURE_EXIT_CODE: 7`
  - `EXECUTE_FAILURE_VALIDATE_STATUS: failed`
- `manager_policy_gate_smoke`
  - sensitive playbook 차단
  - `POLICY_DENY_EXECUTE_STATUS: 403`
  - `POLICY_DENY_APPROVAL_STATUS: approval_required`
- `manager_approval_flow_smoke`
  - approval 생성
  - approval 승인
  - 승인 후 `run/auto` 재실행 성공
  - 최종 stage `close`

## 6. 제외한 파일
아래 파일은 이번 작업 범위 밖의 기존 dirty/untracked 상태로 판단하여 커밋에서 제외한다.
- `docs/verification/WORK-36.md`
- `docs/verification/NEXT-32.md`
- `docs/verification/NEXT-37.md`
- `docs/verification/REVIEW-31.md`
- `docs/verification/REVIEW-36.md`
- `get-pip.py`
- `tools/dev/project_close_smoke.py`

## 7. 남은 과제
- `master-service`를 approval/review 실제 경로에 연결
- approval 이력과 evidence/history 연동
- policy rule 을 asset/policy data 기반으로 일반화
- playbook step 실제 실행/branching 구조 고도화
