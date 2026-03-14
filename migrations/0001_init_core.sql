-- 0001_init_core.sql
-- Core schema for OldClaw (M0)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================
-- Asset tables
-- ====================================
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    platform TEXT,
    env TEXT,
    mgmt_ip INET,
    roles JSONB,
    agent_id TEXT,
    subagent_status TEXT,
    expected_subagent_port INTEGER,
    auth_ref TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_assets_name_type UNIQUE (name, type)
);

CREATE TABLE asset_endpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    endpoint_type TEXT NOT NULL,
    value TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_asset_endpoints UNIQUE (asset_id, endpoint_type, value)
);

-- ====================================
-- Target tables
-- ====================================
CREATE TABLE targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    base_url TEXT NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    health TEXT,
    resolver_version TEXT,
    metadata JSONB,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ====================================
-- Project & association tables
-- ====================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    request_text TEXT NOT NULL,
    requester_type TEXT,
    status TEXT NOT NULL CHECK (status IN ('new','in_progress','completed','failed')),
    current_stage TEXT NOT NULL,
    mode TEXT CHECK (mode IN ('one_shot','batch','continuous')),
    playbook_id TEXT,
    priority INTEGER,
    risk_level TEXT,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    closed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE project_assets (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    scope_role TEXT,
    selected_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (project_id, asset_id)
);

-- ====================================
-- JobRun & Evidence tables
-- ====================================
CREATE TABLE job_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_job_id UUID REFERENCES job_runs(id),
    playbook_id TEXT,
    skill_id TEXT,
    asset_id UUID REFERENCES assets(id),
    target_id UUID REFERENCES targets(id),
    assigned_agent_role TEXT,
    assigned_agent_id TEXT,
    status TEXT CHECK (status IN ('queued','running','succeeded','failed')),
    stage TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    input_ref TEXT,
    output_ref TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id UUID REFERENCES job_runs(id) ON DELETE SET NULL,
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
    target_id UUID REFERENCES targets(id) ON DELETE SET NULL,
    agent_role TEXT,
    agent_id TEXT,
    tool_name TEXT,
    command_text TEXT,
    input_payload_ref TEXT,
    stdout_ref TEXT,
    stderr_ref TEXT,
    exit_code INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    evidence_type TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE validation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id UUID REFERENCES job_runs(id) ON DELETE SET NULL,
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
    validator_name TEXT,
    validation_type TEXT,
    status TEXT CHECK (status IN ('passed','failed','error')),
    expected_result JSONB,
    actual_result JSONB,
    evidence_id UUID REFERENCES evidence(id),
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE master_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    reviewer_agent_id TEXT,
    status TEXT,
    review_summary TEXT,
    findings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    report_type TEXT,
    body_ref TEXT,
    summary TEXT,
    created_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ====================================
-- Supporting tables (messages, audit_logs, schedules)
-- ====================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id UUID REFERENCES job_runs(id) ON DELETE SET NULL,
    sender TEXT NOT NULL,
    recipient TEXT,
    channel TEXT,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    actor TEXT,
    target TEXT,
    outcome TEXT,
    description TEXT,
    metadata JSONB,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    schedule_type TEXT NOT NULL,
    cron_expr TEXT,
    next_run TIMESTAMP WITH TIME ZONE,
    last_run TIMESTAMP WITH TIME ZONE,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
