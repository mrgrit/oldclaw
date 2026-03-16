# OldClaw API

## Manager API

Source: `apps/manager-api/src/main.py`

Current version string: `0.3.0-m3`

## Implemented Routes

### Health

- `GET /health`

### Runtime

- `POST /runtime/invoke`

Request body:

```json
{
  "prompt": "summarize current project state",
  "role": "manager"
}
```

### Projects

- `POST /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/plan`
- `POST /projects/{project_id}/execute`
- `GET /projects/{project_id}/execute/plan`
- `POST /projects/{project_id}/execute/run`
- `POST /projects/{project_id}/execute/auto`
- `POST /projects/{project_id}/run/auto`
- `GET /projects/{project_id}/policy-check`
- `GET /projects/{project_id}/approvals`
- `POST /projects/{project_id}/approvals/{approval_id}/approve`
- `POST /projects/{project_id}/validate`
- `POST /projects/{project_id}/report/finalize`
- `GET /projects/{project_id}/report`
- `POST /projects/{project_id}/evidence/minimal`
- `GET /projects/{project_id}/evidence`
- `POST /projects/{project_id}/close`

### Project Associations

- `POST /projects/{project_id}/assets/{asset_id}`
- `GET /projects/{project_id}/assets`
- `POST /projects/{project_id}/targets/{target_id}`
- `GET /projects/{project_id}/targets`
- `POST /projects/{project_id}/playbooks/{playbook_id}`
- `GET /projects/{project_id}/playbooks`
- `POST /projects/{project_id}/dispatch/subagent`

### Registry-style Lookup

- `GET /assets`
- `GET /targets`
- `GET /playbooks`

## Current Semantics

- lifecycle is strictly linear
- `close` is only allowed from `report`
- evidence creation is minimal row insertion, not a full artifact pipeline
- project-playbook linkage is currently a single `projects.playbook_id` binding
- project-target linkage uses a runtime-created `project_targets` table
- `execute/plan` previews the resolved target/playbook/skill/tool/script bundle
- `execute/auto` builds a script from linked target/playbook seed metadata
- `run/auto` performs `plan -> execute/auto -> validate -> report -> close` in one call
- `validate` now records a `validation_runs` row based on evidence exit codes
- validation status is `passed`, `failed`, or `inconclusive`
- sensitive playbooks, high-risk projects, and continuous mode are blocked before execution
- blocked execution creates an approval request record
- approved requests allow rerun through the same execution endpoints

## Not Yet Implemented

- approval endpoints
- policy endpoints
- actual playbook execution endpoints
- target resolution endpoints
- scheduler or watch control endpoints
- master review workflow integration

## Other Service APIs

### Master Service

Source: `apps/master-service/src/main.py`

- `GET /health`
- `POST /runtime/invoke`
- `POST /projects/{project_id}/review` returns `501`
- `POST /projects/{project_id}/replan` returns `501`
- `POST /projects/{project_id}/escalate` returns `501`

### SubAgent Runtime

Source: `apps/subagent-runtime/src/main.py`

- `GET /health`
- `GET /capabilities`
- `POST /runtime/invoke`
- `POST /a2a/run_script` returns `501`
