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
- `GET /projects/{project_id}/history`
- `POST /projects/{project_id}/plan`
- `POST /projects/{project_id}/execute`
- `GET /projects/{project_id}/execute/plan`
- `POST /projects/{project_id}/execute/run`
- `POST /projects/{project_id}/execute/auto`
- `POST /projects/{project_id}/run/auto`
- `POST /projects/{project_id}/run/auto/review`
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
- `POST /projects/{project_id}/schedules`
- `GET /projects/{project_id}/schedules`
- `POST /projects/{project_id}/watch-jobs`
- `GET /projects/{project_id}/watch-jobs`
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
- `run/auto/review` performs `plan -> execute/auto -> validate -> report -> close -> master review`
- closing a project persists one raw history event and one structured task memory record
- `validate` now records a `validation_runs` row based on evidence exit codes
- validation status is `passed`, `failed`, or `inconclusive`
- sensitive playbooks, high-risk projects, and continuous mode are blocked before execution
- blocked execution creates an approval request record
- approved requests allow rerun through the same execution endpoints
- schedules and watch jobs can now be created and listed from manager-api

## Not Yet Implemented

- target resolution endpoints
- advanced playbook branching / distributed execution
- retrieval / experience-backed runtime decisions
- full scheduler / watch CRUD control plane

## Other Service APIs

### Master Service

Source: `apps/master-service/src/main.py`

- `GET /health`
- `POST /runtime/invoke`
- `POST /projects/{project_id}/review`
- `GET /projects/{project_id}/reviews`
- `POST /projects/{project_id}/replan`
- `POST /projects/{project_id}/escalate`

Current behavior:

- review stores a `master_reviews` row
- approved projects return `approved`
- approval-pending or validation-missing projects return `needs_replan`
- failed validation projects return `rejected`

### SubAgent Runtime

Source: `apps/subagent-runtime/src/main.py`

- `GET /health`
- `GET /capabilities`
- `POST /runtime/invoke`
- `POST /a2a/run_script`

Current behavior:

- executes local shell script via `/bin/bash -lc`
- persists subagent evidence and updates `job_runs`

### Scheduler Worker

Source: `apps/scheduler-worker/src/main.py`

- `GET /health`
- `POST /run-once`

Current behavior:

- loads enabled schedules whose `next_run` is due
- updates `last_run` / `next_run`
- records one `schedule_triggered` history event per processed schedule

### Watch Worker

Source: `apps/watch-worker/src/main.py`

- `GET /health`
- `POST /run-once`

Current behavior:

- loads `watch_jobs` with `status='running'`
- records one `watch_events` row per processed job
- optionally creates an `incidents` row when metadata requests it
- records one `watch_job_processed` history event per processed job
