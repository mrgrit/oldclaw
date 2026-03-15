BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    schedule_type TEXT NOT NULL,
    cron_expr TEXT,
    next_run TIMESTAMPTZ,
    last_run TIMESTAMPTZ,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_schedules_project_id ON schedules(project_id);
CREATE INDEX idx_schedules_next_run ON schedules(next_run);

CREATE TABLE watch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    watch_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_watch_jobs_project_id ON watch_jobs(project_id);
CREATE INDEX idx_watch_jobs_status ON watch_jobs(status);

CREATE TABLE watch_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watch_job_id UUID NOT NULL REFERENCES watch_jobs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_watch_events_watch_job_id ON watch_events(watch_job_id);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    severity TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_incidents_project_id ON incidents(project_id);
CREATE INDEX idx_incidents_status ON incidents(status);

COMMIT;
