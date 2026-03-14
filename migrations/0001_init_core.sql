BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- == Asset tables ==
CREATE TABLE assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    platform TEXT NOT NULL,
    env TEXT NOT NULL,
    mgmt_ip INET NOT NULL,
    roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    agent_id TEXT,
    subagent_status TEXT NOT NULL DEFAULT 'unknown',
    expected_subagent_port INTEGER,
    auth_ref TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assets_subagent_status_check
        CHECK (subagent_status IN ('unknown', 'healthy', 'unhealthy', 'missing'))
);

CREATE UNIQUE INDEX idx_assets_name ON assets (name);
CREATE INDEX idx_assets_env ON assets (env);
CREATE INDEX idx_assets_platform ON assets (platform);

CREATE TABLE asset_endpoints (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    endpoint_type TEXT NOT NULL,
    value TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_asset_endpoints_asset_id ON asset_endpoints (asset_id);
CREATE INDEX idx_asset_endpoints_type ON asset_endpoints (endpoint_type);

-- == Target tables ==
CREATE TABLE targets (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    base_url TEXT NOT NULL,
    resolved_at TIMESTAMPTZ NOT NULL,
    health TEXT NOT NULL,
    resolver_version TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ,
    CONSTRAINT targets_health_check
        CHECK (health IN ('ok', 'degraded', 'failed', 'unknown'))
);

CREATE INDEX idx_targets_asset_id ON targets (asset_id);
CREATE INDEX idx_targets_resolved_at ON targets (resolved_at);

-- == Project & association tables ==
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    request_text TEXT NOT NULL,
    requester_type TEXT NOT NULL DEFAULT 'human',
    status TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    mode TEXT NOT NULL,
    playbook_id TEXT,
    priority TEXT NOT NULL DEFAULT 'normal',
    risk_level TEXT NOT NULL DEFAULT 'medium',
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    CONSTRAINT projects_status_check
        CHECK (status IN ('created', 'planned', 'running', 'blocked', 'failed', 'completed', 'closed')),
    CONSTRAINT projects_mode_check
        CHECK (mode IN ('one_shot', 'batch', 'continuous')),
    CONSTRAINT projects_priority_check
        CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    CONSTRAINT projects_risk_level_check
        CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX idx_projects_status ON projects (status);
CREATE INDEX idx_projects_mode ON projects (mode);
CREATE INDEX idx_projects_created_at ON projects (created_at);

CREATE TABLE project_assets (
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    scope_role TEXT NOT NULL,
    selected_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (project_id, asset_id),
    CONSTRAINT project_assets_scope_role_check
        CHECK (scope_role IN ('primary', 'dependent', 'observer'))
);

CREATE INDEX idx_project_assets_asset_id ON project_assets (asset_id);

-- == JobRun & Evidence tables ==
CREATE TABLE job_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_job_id TEXT REFERENCES job_runs(id) ON DELETE SET NULL,
    playbook_id TEXT,
    skill_id TEXT,
    asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    target_id TEXT REFERENCES targets(id) ON DELETE SET NULL,
    assigned_agent_role TEXT NOT NULL,
    assigned_agent_id TEXT,
    status TEXT NOT NULL,
    stage TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,
    input_ref TEXT,
    output_ref TEXT,
    CONSTRAINT job_runs_agent_role_check
        CHECK (assigned_agent_role IN ('manager', 'subagent', 'master')),
    CONSTRAINT job_runs_status_check
        CHECK (status IN ('queued', 'running', 'blocked', 'failed', 'completed', 'cancelled'))
);

CREATE INDEX idx_job_runs_project_id ON job_runs (project_id);
CREATE INDEX idx_job_runs_asset_id ON job_runs (asset_id);
CREATE INDEX idx_job_runs_status ON job_runs (status);

CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id TEXT REFERENCES job_runs(id) ON DELETE SET NULL,
    asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    target_id TEXT REFERENCES targets(id) ON DELETE SET NULL,
    agent_role TEXT NOT NULL,
    agent_id TEXT,
    tool_name TEXT NOT NULL,
    command_text TEXT,
    input_payload_ref TEXT,
    stdout_ref TEXT,
    stderr_ref TEXT,
    exit_code INTEGER,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    evidence_type TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT evidence_agent_role_check
        CHECK (agent_role IN ('manager', 'subagent', 'master')),
    CONSTRAINT evidence_type_check
        CHECK (evidence_type IN ('command', 'file_diff', 'api_call', 'probe', 'report_fragment'))
);

CREATE INDEX idx_evidence_project_id ON evidence (project_id);
CREATE INDEX idx_evidence_job_run_id ON evidence (job_run_id);
CREATE INDEX idx_evidence_asset_id ON evidence (asset_id);

-- == Validation runs ==
CREATE TABLE validation_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id TEXT REFERENCES job_runs(id) ON DELETE SET NULL,
    asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    validator_name TEXT NOT NULL,
    validation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    expected_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    actual_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence_id TEXT REFERENCES evidence(id) ON DELETE SET NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT validation_runs_status_check
        CHECK (status IN ('passed', 'failed', 'inconclusive'))
);

CREATE INDEX idx_validation_runs_project_id ON validation_runs (project_id);
CREATE INDEX idx_validation_runs_status ON validation_runs (status);

-- == Master reviews ==
CREATE TABLE master_reviews (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    reviewer_agent_id TEXT NOT NULL,
    status TEXT NOT NULL,
    review_summary TEXT NOT NULL,
    findings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT master_reviews_status_check
        CHECK (status IN ('approved', 'rejected', 'needs_replan'))
);

CREATE INDEX idx_master_reviews_project_id ON master_reviews (project_id);

-- == Reports ==
CREATE TABLE reports (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,
    body_ref TEXT NOT NULL,
    summary TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT reports_type_check
        CHECK (report_type IN ('intermediate', 'final', 'handoff', 'audit_export'))
);

CREATE INDEX idx_reports_project_id ON reports (project_id);

-- == Messages ==
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    from_role TEXT NOT NULL,
    from_id TEXT NOT NULL,
    to_role TEXT NOT NULL,
    to_id TEXT NOT NULL,
    message_type TEXT NOT NULL,
    body_ref TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT messages_from_role_check
        CHECK (from_role IN ('human', 'manager', 'master', 'subagent')),
    CONSTRAINT messages_to_role_check
        CHECK (to_role IN ('human', 'manager', 'master', 'subagent'))
);

CREATE INDEX idx_messages_project_id ON messages (project_id);
CREATE INDEX idx_messages_created_at ON messages (created_at);

-- == Audit logs ==
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    ref_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_project_id ON audit_logs (project_id);
CREATE INDEX idx_audit_logs_asset_id ON audit_logs (asset_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs (created_at);

COMMIT;
