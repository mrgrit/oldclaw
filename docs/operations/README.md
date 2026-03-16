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

## Basic Verification

Syntax-level verification:

```bash
python3 -m compileall apps packages tools
```

DB-backed smoke examples:

```bash
PYTHONPATH=. python3 tools/dev/project_service_smoke.py
PYTHONPATH=. python3 tools/dev/m2_integrated_smoke.py
PYTHONPATH=. python3 tools/dev/m3_integrated_smoke.py
PYTHONPATH=. python3 tools/dev/project_close_smoke.py
PYTHONPATH=. python3 tools/dev/subagent_run_script_smoke.py
PYTHONPATH=. python3 tools/dev/manager_execute_plan_smoke.py
PYTHONPATH=. python3 tools/dev/manager_execute_auto_smoke.py
PYTHONPATH=. python3 tools/dev/manager_execute_run_smoke.py
PYTHONPATH=. python3 tools/dev/manager_execute_failure_smoke.py
PYTHONPATH=. python3 tools/dev/manager_policy_gate_smoke.py
PYTHONPATH=. python3 tools/dev/manager_approval_flow_smoke.py
PYTHONPATH=. python3 tools/dev/manager_run_auto_smoke.py
```

## Operational Reality

- manager is the only service with meaningful business endpoints today
- master and subagent are partial boundaries, not complete workers
- scheduler and watch workers should be treated as placeholders
- no deployment automation or health orchestration is wired end-to-end yet

## Immediate Ops Risks

- README and milestone docs are more trustworthy than placeholder service assumptions
- Make targets and older verification logs may reference historical paths
- runtime invoke success depends on external pi and model provider availability
- many smoke scripts assume the database already contains or can accept seed rows
- manager auto execution paths derive skills/tools from `seed/playbooks` and `seed/skills`
- manager execution paths are subject to policy gate checks before dispatch
- denied executions persist approval requests and can be retried after approval
