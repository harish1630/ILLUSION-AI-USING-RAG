-- ============================================================================
-- ILLUSION AI: Supabase PostgreSQL Migration for MCP & GitHub OAuth Integration
-- ============================================================================

-- 1. GitHub Connections Table
CREATE TABLE IF NOT EXISTS public.github_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    github_user_id VARCHAR(100) NOT NULL,
    github_username VARCHAR(100) NOT NULL,
    github_email VARCHAR(255),
    avatar_url TEXT,
    encrypted_access_token TEXT NOT NULL,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_github_connections_user_id ON public.github_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_github_connections_github_user_id ON public.github_connections(github_user_id);

-- Enable RLS
ALTER TABLE public.github_connections ENABLE ROW LEVEL SECURITY;

-- RLS Policies for github_connections
CREATE POLICY "Users can view own github connection"
    ON public.github_connections FOR SELECT
    USING (auth.uid()::text = user_id OR user_id = 'default_user');

CREATE POLICY "Users can insert own github connection"
    ON public.github_connections FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'default_user');

CREATE POLICY "Users can update own github connection"
    ON public.github_connections FOR UPDATE
    USING (auth.uid()::text = user_id OR user_id = 'default_user');

CREATE POLICY "Users can delete own github connection"
    ON public.github_connections FOR DELETE
    USING (auth.uid()::text = user_id OR user_id = 'default_user');


-- 2. MCP Servers Table
CREATE TABLE IF NOT EXISTS public.mcp_servers (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL DEFAULT 'system',
    name VARCHAR(100) NOT NULL,
    description TEXT,
    transport VARCHAR(50) NOT NULL,
    command VARCHAR(255),
    args JSONB DEFAULT '[]'::jsonb,
    url TEXT,
    status VARCHAR(50) DEFAULT 'disconnected',
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_mcp_servers_user_id ON public.mcp_servers(user_id);
ALTER TABLE public.mcp_servers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read mcp_servers"
    ON public.mcp_servers FOR SELECT
    USING (true);

CREATE POLICY "Users manage own mcp_servers"
    ON public.mcp_servers FOR ALL
    USING (auth.uid()::text = user_id OR user_id = 'system');


-- 3. MCP Tools Table
CREATE TABLE IF NOT EXISTS public.mcp_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    qualified_name VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    input_schema JSONB DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN DEFAULT true,
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_mcp_tools_server_id ON public.mcp_tools(server_id);
CREATE INDEX IF NOT EXISTS idx_mcp_tools_qualified_name ON public.mcp_tools(qualified_name);
ALTER TABLE public.mcp_tools ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read mcp_tools"
    ON public.mcp_tools FOR SELECT
    USING (true);


-- 4. MCP Permissions Table
CREATE TABLE IF NOT EXISTS public.mcp_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    server_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    permission_level VARCHAR(50) NOT NULL DEFAULT 'DENY',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_mcp_permissions_user_server_tool ON public.mcp_permissions(user_id, server_id, tool_name);
ALTER TABLE public.mcp_permissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own permissions"
    ON public.mcp_permissions FOR SELECT
    USING (auth.uid()::text = user_id OR user_id = '*');

CREATE POLICY "Users manage own permissions"
    ON public.mcp_permissions FOR ALL
    USING (auth.uid()::text = user_id);


-- 5. MCP Approvals Table
CREATE TABLE IF NOT EXISTS public.mcp_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    server_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    arguments JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    reviewer_id VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    reviewed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_mcp_approvals_user_id ON public.mcp_approvals(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_approvals_status ON public.mcp_approvals(status);
ALTER TABLE public.mcp_approvals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own approvals"
    ON public.mcp_approvals FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users update own approvals"
    ON public.mcp_approvals FOR UPDATE
    USING (auth.uid()::text = user_id);


-- 6. MCP Execution Logs Table
CREATE TABLE IF NOT EXISTS public.mcp_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    server_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    arguments JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL,
    result JSONB,
    error_message TEXT,
    duration_ms DOUBLE PRECISION DEFAULT 0.0,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_mcp_logs_user_id ON public.mcp_execution_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_logs_executed_at ON public.mcp_execution_logs(executed_at DESC);
ALTER TABLE public.mcp_execution_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own execution logs"
    ON public.mcp_execution_logs FOR SELECT
    USING (auth.uid()::text = user_id);
