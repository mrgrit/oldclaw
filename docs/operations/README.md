# OldClaw Operations

## Local Development Baseline

OldClaw currently assumes:

- Python 3.11+
- PostgreSQL reachable through `DATABASE_URL`
- external `pi` CLI available in `PATH` when runtime invoke endpoints are used

## Environment

Primary variables used by the codebase:

- `DATABASE_URL`
- `OLDCLAW_PI_PROVIDER`
- `OLDCLAW_PI_BASE_URL`
- `OLDCLAW_PI_API_KEY`
- `OLDCLAW_PI_COMMAND`
- `OLDCLAW_PI_WORKING_DIR`
- `OLDCLAW_PI_DEFAULT_TIMEOUT_S`
- `OLDCLAW_PI_MANAGER_MODEL`
- `OLDCLAW_PI_MASTER_MODEL`
- `OLDCLAW_PI_SUBAGENT_MODEL`

## Practical Startup

### Manager API

```bash
python3 -m uvicorn --app-dir apps/manager-api/src main:app --reload
```

### Master Service

```bash
python3 -m uvicorn --app-dir apps/master-service/src main:app --reload
```

### SubAgent Runtime

```bash
python3 -m uvicorn --app-dir apps/subagent-runtime/src main:app --reload
```

### Scheduler Worker

```bash
python3 -m uvicorn --app-dir apps/scheduler-worker/src main:app --reload
```

### Watch Worker

```bash
python3 -m uvicorn --app-dir apps/watch-worker/src main:app --reload
```

## Basic Verification

Syntax-level verification:

```bash
python3 -m compileall apps packages tools
```

DB-backed smoke examples:

```bash
python3 -m compileall apps packages tools tests
DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw' PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Operational Reality

- manager is still the orchestration center
- master, subagent, scheduler, and watch now all have minimal executable boundaries
- scheduler/watch are usable for `run-once` style verification, not full orchestration loops yet
- no deployment automation or health orchestration is wired end-to-end yet

## Immediate Ops Risks

- README and milestone docs are more trustworthy than placeholder service assumptions
- Make targets and older verification logs may reference historical paths
- runtime invoke success depends on external pi and model provider availability
- many smoke scripts assume the database already contains or can accept seed rows
- manager auto execution paths derive skills/tools from `seed/playbooks` and `seed/skills`
- manager execution paths are subject to policy gate checks before dispatch
- denied executions persist approval requests and can be retried after approval
- `make` targets exist in the repository, but some environments may not have the `make` binary installed
- manager now exposes minimal schedule/watch control-plane APIs, while worker `run-once` endpoints consume those tables
- manager can also proxy one-off scheduler/watch execution through `/projects/scheduler/run-once` and `/projects/watch/run-once`
- watch outcomes can be observed through `/projects/{id}/watch-events` and `/projects/{id}/incidents`
- incident lifecycle can be updated through `/projects/{id}/incidents/{incident_id}/acknowledge` and `/close`
