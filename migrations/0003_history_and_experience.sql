-- 0003_history_and_experience.sql
-- 4‑layer memory model: histories → task_memories → experiences → retrieval_documents

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Raw execution history (unstructured events)
CREATE TABLE histories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id UUID REFERENCES job_runs(id) ON DELETE SET NULL,
    event TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Structured task memory generated after a job run
CREATE TABLE task_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_run_id UUID NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    memory_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Semantic experiences extracted from task memories for reuse
CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE SET NULL,
    outcome TEXT,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Retrieval documents used by the LLM for context augmentation
CREATE TABLE retrieval_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
