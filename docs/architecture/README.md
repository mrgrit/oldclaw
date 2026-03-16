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
- review / replan / escalate routes exist only as `501 Not Implemented`

### SubAgent Runtime

`apps/subagent-runtime/src/main.py`

- health and capabilities endpoints
- runtime invoke endpoint
- `a2a/run_script` boundary exists but execution engine is not implemented

### Scheduler Worker

`apps/scheduler-worker/src/main.py`

- placeholder loop only
- no schedule loading or job enqueue implementation

### Watch Worker

`apps/watch-worker/src/main.py`

- placeholder loop only
- no watch job processing or event generation implementation

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

## Known Gaps

- no approval engine wiring
- no policy enforcement
- no actual playbook execution
- no target resolution pipeline
- no distributed subagent execution
- no history/retrieval usage in runtime decisions
- no real scheduler/watch processing loop
- no integrated app factory / dependency injection layer

## Practical Development Baseline

When continuing development, treat the current system as:

- a working Manager API prototype
- a real PostgreSQL-backed lifecycle store
- a partial M3 start, not a complete M3 implementation
- documentation-in-progress with verification logs as historical context
