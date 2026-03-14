-- 0004_scheduler_and_watch.sql
-- Scheduler and Watch tables for background processing (M0)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Scheduler jobs (periodic)
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

-- Watch jobs (event‑driven)
CREATE TABLE watch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL,
    schedule_id UUID REFERENCES schedules(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','running','completed','failed')),
    last_checked TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE watch_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watch_job_id UUID NOT NULL REFERENCES watch_jobs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Incidents (high‑level alerts triggered by watch jobs)
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    severity TEXT,
    description TEXT,
    status TEXT CHECK (status IN ('open','acknowledged','resolved')),
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
