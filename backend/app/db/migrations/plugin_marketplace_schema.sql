-- ============================================================================
-- ILLUSION AI: Supabase PostgreSQL Migration for Plugin Marketplace
-- ============================================================================

-- 1. Plugin Catalog Table
CREATE TABLE IF NOT EXISTS public.plugin_catalog (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'email', 'developer', 'productivity', 'communication', 'tools'
    icon VARCHAR(100) NOT NULL,     -- 'Mail', 'Github', 'HardDrive', 'MessageSquare', 'FileText', 'Cpu'
    auth_type VARCHAR(50) NOT NULL, -- 'oauth2', 'api_key', 'mcp', 'none'
    scopes JSONB DEFAULT '[]'::jsonb,
    features JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_plugin_catalog_category ON public.plugin_catalog(category);
CREATE INDEX IF NOT EXISTS idx_plugin_catalog_active ON public.plugin_catalog(is_active);

-- Enable RLS on catalog (Publicly readable)
ALTER TABLE public.plugin_catalog ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read plugin_catalog"
    ON public.plugin_catalog FOR SELECT
    USING (true);


-- 2. User Integrations Table (Connected Apps)
CREATE TABLE IF NOT EXISTS public.user_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL REFERENCES public.plugin_catalog(id) ON DELETE CASCADE,
    account_id VARCHAR(255),
    account_email VARCHAR(255),
    account_username VARCHAR(255),
    avatar_url TEXT,
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    scopes JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'connected', -- 'connected', 'expired', 'revoked', 'error'
    metadata JSONB DEFAULT '{}'::jsonb,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_plugin UNIQUE (user_id, plugin_id)
);

CREATE INDEX IF NOT EXISTS idx_user_integrations_user_id ON public.user_integrations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_integrations_plugin_id ON public.user_integrations(plugin_id);
CREATE INDEX IF NOT EXISTS idx_user_integrations_status ON public.user_integrations(status);

ALTER TABLE public.user_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own integrations"
    ON public.user_integrations FOR SELECT
    USING (auth.uid()::text = user_id OR user_id = 'default_user' OR user_id LIKE 'guest_%');

CREATE POLICY "Users insert own integrations"
    ON public.user_integrations FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'default_user' OR user_id LIKE 'guest_%');

CREATE POLICY "Users update own integrations"
    ON public.user_integrations FOR UPDATE
    USING (auth.uid()::text = user_id OR user_id = 'default_user' OR user_id LIKE 'guest_%');

CREATE POLICY "Users delete own integrations"
    ON public.user_integrations FOR DELETE
    USING (auth.uid()::text = user_id OR user_id = 'default_user' OR user_id LIKE 'guest_%');


-- 3. Plugin Tool Permissions Table (Default-Deny / Approvals)
CREATE TABLE IF NOT EXISTS public.plugin_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL REFERENCES public.plugin_catalog(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    permission_level VARCHAR(50) NOT NULL DEFAULT 'DENY', -- 'ALLOW', 'APPROVAL_REQUIRED', 'DENY'
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_plugin_tool UNIQUE (user_id, plugin_id, tool_name)
);

CREATE INDEX IF NOT EXISTS idx_plugin_permissions_user_plugin ON public.plugin_permissions(user_id, plugin_id);

ALTER TABLE public.plugin_permissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own permissions"
    ON public.plugin_permissions FOR SELECT
    USING (auth.uid()::text = user_id OR user_id = 'default_user' OR user_id LIKE 'guest_%');

CREATE POLICY "Users manage own permissions"
    ON public.plugin_permissions FOR ALL
    USING (auth.uid()::text = user_id OR user_id = 'default_user' OR user_id LIKE 'guest_%');


-- 4. OAuth States Table (PKCE & CSRF protection)
CREATE TABLE IF NOT EXISTS public.oauth_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state VARCHAR(255) UNIQUE NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    redirect_uri TEXT NOT NULL,
    code_verifier TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON public.oauth_states(state);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires ON public.oauth_states(expires_at);

ALTER TABLE public.oauth_states ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Backend manages oauth states"
    ON public.oauth_states FOR ALL
    USING (true);


-- 5. Plugin Execution Audit Logs
CREATE TABLE IF NOT EXISTS public.plugin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    arguments JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL, -- 'SUCCESS', 'FAILED', 'DENIED', 'APPROVAL_REQUIRED'
    result JSONB,
    error_message TEXT,
    duration_ms FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_plugin_audit_logs_user_id ON public.plugin_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_plugin_audit_logs_plugin_id ON public.plugin_audit_logs(plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugin_audit_logs_created_at ON public.plugin_audit_logs(created_at DESC);

ALTER TABLE public.plugin_audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own audit logs"
    ON public.plugin_audit_logs FOR SELECT
    USING (auth.uid()::text = user_id OR user_id = 'default_user' OR user_id LIKE 'guest_%');

CREATE POLICY "Service inserts audit logs"
    ON public.plugin_audit_logs FOR INSERT
    WITH CHECK (true);


-- 6. Seed Initial Plugin Catalog
INSERT INTO public.plugin_catalog (id, name, display_name, description, category, icon, auth_type, scopes, features, is_active)
VALUES
    (
        'gmail',
        'gmail',
        'Google Gmail',
        'Search emails, read communications, compose drafts, and securely send emails with AI assistance.',
        'email',
        'Mail',
        'oauth2',
        '["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.compose"]'::jsonb,
        '["Search inbox with search queries", "Read messages & threads", "Compose draft replies", "Send emails with explicit confirmation"]'::jsonb,
        true
    ),
    (
        'github',
        'github',
        'GitHub',
        'Analyze repositories, browse commits & branches, view issues, and create issue tickets directly from chat.',
        'developer',
        'Github',
        'oauth2',
        '["repo", "read:user", "user:email"]'::jsonb,
        '["List and inspect repositories", "Read file contents & tree", "View & create issue tickets", "Review recent commits & branches"]'::jsonb,
        true
    ),
    (
        'google_drive',
        'google_drive',
        'Google Drive',
        'Search documents, analyze spreadsheets, extract text from PDFs, and manage startup assets.',
        'productivity',
        'HardDrive',
        'oauth2',
        '["https://www.googleapis.com/auth/drive.readonly"]'::jsonb,
        '["Browse folder hierarchy", "Read Docs, Sheets & PDFs", "Direct RAG document indexing"]'::jsonb,
        false
    ),
    (
        'slack',
        'slack',
        'Slack Workspace',
        'Connect team channels, read updates, summarize discussions, and post notifications.',
        'communication',
        'MessageSquare',
        'oauth2',
        '["channels:read", "chat:write"]'::jsonb,
        '["Summarize channel threads", "Post automated updates", "Team notifications"]'::jsonb,
        false
    ),
    (
        'notion',
        'notion',
        'Notion Workspace',
        'Sync startup roadmaps, retrieve business plans, and update documentation databases.',
        'productivity',
        'FileText',
        'oauth2',
        '["read_content", "update_content"]'::jsonb,
        '["Read notes and project wikis", "Sync roadmap milestones", "Query Notion databases"]'::jsonb,
        false
    ),
    (
        'custom_mcp',
        'custom_mcp',
        'Custom MCP Server',
        'Connect any external Model Context Protocol server via Streamable HTTP or STDIO transports.',
        'tools',
        'Cpu',
        'mcp',
        '[]'::jsonb,
        '["Dynamic MCP tool discovery", "STDIO & HTTP transports", "Custom enterprise tools"]'::jsonb,
        true
    )
ON CONFLICT (id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    icon = EXCLUDED.icon,
    scopes = EXCLUDED.scopes,
    features = EXCLUDED.features,
    updated_at = timezone('utc'::text, now());
