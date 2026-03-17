# OldClaw Architecture

## Current Reality

OldClaw is currently a DB-backed control-plane skeleton centered on the Manager API.

The implemented path is:

1. create project
2. move project through `plan -> execute -> validate -> report -> close`
3. store minimal evidence and reports
4. link assets, targets, and playbooks to a project
5. expose the state through FastAPI endpoints

This is not yet the full Master-Manager-SubAgent orchestration platform described in the long-term plan.

## Active Components

### Manager API

`apps/manager-api/src/main.py`

- primary user-facing control-plane
- owns project lifecycle endpoints
- exposes asset / target / playbook lookup and linking endpoints
- exposes a minimal pi runtime invoke endpoint

### Project Service

`packages/project_service/__init__.py`

- direct PostgreSQL access via `psycopg2`
- lifecycle transition logic
- report and evidence persistence
- asset / target / playbook association queries
- project summary assembly

### Graph Runtime

`packages/graph_runtime/__init__.py`

- minimal stage definition only
- validates the linear transition sequence
- not a full LangGraph runtime

### pi Adapter

`packages/pi_adapter/*`

- wraps external `pi` CLI execution
- provides in-memory session registry
- builds prompt text and optional `--tools` CLI flag
- used by manager, master, and subagent runtime endpoints

## Boundary Services

### Master Service

`apps/master-service/src/main.py`

- health endpoint
- runtime invoke endpoint
- review / replan / escalate routes implemented
- writes `master_reviews` and derives `approved` / `needs_replan` / `rejected`

### SubAgent Runtime

`apps/subagent-runtime/src/main.py`

- health and capabilities endpoints
- runtime invoke endpoint
- `a2a/run_script` executes local shell scripts and persists evidence

### Scheduler Worker

`apps/scheduler-worker/src/main.py`

- health endpoint
- `run-once` endpoint
- due schedule loading and `last_run` / `next_run` updates
- per-run history event creation

### Watch Worker

`apps/watch-worker/src/main.py`

- health endpoint
- `run-once` endpoint
- running watch job loading
- watch event creation
- optional incident creation from job metadata
- per-run history event creation

## Data Model Status

Migrations define the broader intended platform surface:

- core project / asset / target / job / evidence tables
- registry tables for tools / skills / playbooks
- history / experience / retrieval tables
- scheduler / watch / incident tables

Only a subset is actively exercised by application code today:

- `projects`
- `project_assets`
- `targets`
- runtime-created `project_targets`
- `assets`
- `playbooks`
- `job_runs`
- `evidence`
- `reports`
- `approvals`
- `master_reviews`
- `histories`
- `task_memories`
- `schedules`
- `watch_jobs`
- `watch_events`
- `incidents`

## Known Gaps

- no target resolution pipeline
- no advanced playbook branching/execution graph
- no target resolution pipeline
- no distributed subagent execution
- no history/retrieval usage in runtime decisions
- no long-running scheduler/watch orchestration loop with control API
- no integrated app factory / dependency injection layer

## Practical Development Baseline

When continuing development, treat the current system as:

- a working Manager API prototype
- a real PostgreSQL-backed lifecycle store
- an active M3 control-plane implementation, not a complete platform
- documentation-in-progress with verification logs as historical context
