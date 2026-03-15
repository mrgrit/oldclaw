BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE histories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id TEXT REFERENCES job_runs(id) ON DELETE SET NULL,
    event TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_histories_project_id ON histories(project_id);
CREATE INDEX idx_histories_job_run_id ON histories(job_run_id);

CREATE TABLE task_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id TEXT REFERENCES job_runs(id) ON DELETE SET NULL,
    summary TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_task_memories_project_id ON task_memories(project_id);
CREATE INDEX idx_task_memories_job_run_id ON task_memories(job_run_id);

CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    outcome TEXT,
    asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    linked_evidence_ids JSONB DEFAULT '[]'::jsonb,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_experiences_category ON experiences(category);
CREATE INDEX idx_experiences_asset_id ON experiences(asset_id);

CREATE TABLE retrieval_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type TEXT NOT NULL,
    ref_id TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_retrieval_documents_document_type ON retrieval_documents(document_type);

COMMIT;
