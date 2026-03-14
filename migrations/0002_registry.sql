-- 0002_registry.sql
-- Registry schema for Tools, Skills and Playbooks (M0)

CREATE TABLE tools (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    runtime_type TEXT,
    risk_level TEXT,
    input_schema_ref TEXT,
    output_schema_ref TEXT,
    policy_tags JSONB,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_tools_name_version UNIQUE (name, version)
);

CREATE TABLE skills (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    supported_modes JSONB,
    input_schema_ref TEXT,
    output_schema_ref TEXT,
    required_tools JSONB,
    optional_tools JSONB,
    default_validation JSONB,
    policy_hint JSONB,
    evidence_expectations JSONB,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_skills_name_version UNIQUE (name, version)
);

CREATE TABLE skill_tools (
    skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    tool_id TEXT NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    usage_mode TEXT,
    order_hint INTEGER,
    PRIMARY KEY (skill_id, tool_id)
);

CREATE TABLE playbooks (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    execution_mode TEXT CHECK (execution_mode IN ('one_shot','batch','continuous')),
    default_risk_level TEXT,
    input_schema_ref TEXT,
    output_schema_ref TEXT,
    dry_run_supported BOOLEAN DEFAULT false,
    explain_supported BOOLEAN DEFAULT false,
    required_asset_roles JSONB,
    failure_policy JSONB,
    policy_bindings JSONB,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_playbooks_name_version UNIQUE (name, version)
);

CREATE TABLE playbook_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    playbook_id TEXT NOT NULL REFERENCES playbooks(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    step_type TEXT NOT NULL,
    ref_id TEXT,
    name TEXT,
    condition_expr TEXT,
    retry_policy JSONB,
    on_failure_action TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE playbook_bindings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    playbook_id TEXT NOT NULL REFERENCES playbooks(id) ON DELETE CASCADE,
    binding_type TEXT NOT NULL,
    binding_ref TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
