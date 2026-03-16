# OldClaw Playbooks

## Current Status

Playbooks are present as registry data and project bindings.

Implemented today:

- `playbooks` table schema
- seed playbook YAML files
- `GET /playbooks`
- `POST /projects/{project_id}/playbooks/{playbook_id}`
- `GET /projects/{project_id}/playbooks`
- project summary inclusion of linked playbooks

Not implemented today:

- playbook step interpretation
- dispatch from playbook steps to skills/tools
- playbook-driven job graph generation
- retry / failure policy execution
- approval or policy gating around playbook runs

## Storage Model

Registry schema lives in `migrations/0002_registry.sql`.

Relevant tables:

- `playbooks`
- `playbook_steps`
- `playbook_bindings`

Current runtime code only reads `playbooks` directly and stores a single selected playbook on `projects.playbook_id`.

## Seed Data

Seed playbooks are stored under `seed/playbooks/`.

Current examples include:

- `diagnose_web_latency`
- `monitor_siem_and_raise_incident`
- `nightly_health_baseline_check`
- `onboard_new_linux_server`
- `tune_siem_noise`

These files are currently registry content, not executable workflows.

## Recommended Next Implementation Step

The next meaningful playbook milestone is:

1. load playbook definition from registry
2. expand ordered steps
3. map each step to skill/tool execution
4. persist job runs and evidence per step
5. enforce validation and failure policy
