/**
 * API client connecting frontend to illusion AI backend.
 */

const getApiBase = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
  }
  if (typeof window !== "undefined") {
    // In browser: check if local dev
    const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    if (isLocalhost) {
      return "http://localhost:8000/api/v1";
    }
  }
  return "https://illusion-ai-using-rag.onrender.com/api/v1";
};

const API_BASE = getApiBase();
const API_HEALTH_URL = `${API_BASE.replace(/\/api\/v1$/, "")}/health`;

export interface Scheme {
  id: string;
  name: string;
  department: string;
  description: string;
  state: string;
  scheme_type: string;
  official_url: string;
  application_url?: string;
  benefits_summary: string;
  eligibility_summary: string;
  exclusions?: string[];
  required_documents?: string[];
  application_steps?: string[];
  last_verified_at?: string;
  eligibility_status?: string;
  match_reasons?: string[];
  missing_criteria?: string[];
}

export interface RoadmapTask {
  id: string;
  roadmap_id: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  status: "pending" | "in_progress" | "completed";
  prerequisites?: string[];
  required_documents?: string[];
  official_url?: string;
  source_references?: string[];
}

export interface Roadmap {
  id: string;
  user_id: string;
  title: string;
  business_summary: string;
  status: string;
  progress_percentage: number;
  tasks: RoadmapTask[];
  created_at: string;
}

export interface ChatSource {
  title: string;
  url: string;
  document_id?: string;
  page?: number;
  section?: string;
  last_verified_at?: string;
}

export interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: any;
}

export interface ToolDefinition {
  name: string;
  display_name: string;
  description: string;
  parameters: ToolParameter[];
  category: string;
  requires_auth: boolean;
  is_available: boolean;
}

export interface ExecutedTool {
  tool_name: string;
  success: boolean;
  data?: any;
  error?: string;
}

export interface ChatWorkflowStep {
  step: string;
  status: string;
  tool?: string;
  sources_count?: number;
  provider?: string;
}

export interface ChatResponse {
  answer: string;
  language: string;
  sources: ChatSource[];
  eligibility_status?: string;
  follow_up_questions: string[];
  matched_schemes: Scheme[];
  disclaimer: string;
  conversation_id?: string;
  executed_tools?: ExecutedTool[];
  tool_mode_used?: string;
  active_router?: string;
  requires_auth?: boolean;
  missing_auth_provider?: string;
  workflow_steps?: ChatWorkflowStep[];
}

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(API_HEALTH_URL);
    if (!res.ok) throw new Error("Backend offline");
    return res.json();
  },

  // Schemes
  async listSchemes(params?: { state?: string; scheme_type?: string; search?: string }): Promise<{ total: number; items: Scheme[]; disclaimer: string }> {
    const query = new URLSearchParams();
    if (params?.state) query.set("state", params.state);
    if (params?.scheme_type) query.set("scheme_type", params.scheme_type);
    if (params?.search) query.set("search", params.search);

    const res = await fetch(`${API_BASE}/schemes?${query.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch schemes");
    return res.json();
  },

  async getScheme(id: string): Promise<Scheme> {
    const res = await fetch(`${API_BASE}/schemes/${id}`);
    if (!res.ok) throw new Error("Scheme not found");
    return res.json();
  },

  async matchSchemes(data: any): Promise<Scheme[]> {
    const res = await fetch(`${API_BASE}/schemes/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to screen schemes");
    return res.json();
  },

  // Business Onboarding
  async saveBusinessProfile(data: any) {
    const res = await fetch(`${API_BASE}/business/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to save profile");
    return res.json();
  },

  // Roadmaps
  async createRoadmap(data: any, language: string = "en"): Promise<Roadmap> {
    const res = await fetch(`${API_BASE}/roadmaps?language=${encodeURIComponent(language)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to generate roadmap");
    return res.json();
  },

  async getRoadmap(roadmapId: string): Promise<Roadmap> {
    const res = await fetch(`${API_BASE}/roadmaps/${roadmapId}`);
    if (!res.ok) throw new Error("Roadmap not found");
    return res.json();
  },

  async updateTaskStatus(roadmapId: string, taskId: string, status: string): Promise<Roadmap> {
    const res = await fetch(`${API_BASE}/roadmaps/${roadmapId}/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error("Failed to update task");
    return res.json();
  },

  // Chat with Hybrid Tool System & LangGraph 6-Branch Router
  async sendChatMessage(
    question: string,
    language: string = "en",
    profile?: any,
    tool_mode: "auto" | "manual" | "hybrid" = "auto",
    selected_tools?: string[],
    tool_args?: Record<string, any>,
    user_id?: string
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        language,
        profile,
        tool_mode,
        selected_tools,
        tool_args,
        user_id: user_id || (typeof window !== "undefined" ? localStorage.getItem("illusion_user_id") || "guest_user" : "guest_user"),
      }),
    });
    if (!res.ok) throw new Error("Chat request failed");
    return res.json();
  },

  // AI Tools Catalogue & Direct Execution
  async listTools(): Promise<ToolDefinition[]> {
    const res = await fetch(`${API_BASE}/tools/`);
    if (!res.ok) throw new Error("Failed to fetch available tools");
    return res.json();
  },

  async executeToolDirect(tool_name: string, arguments_payload: Record<string, any> = {}): Promise<any> {
    const res = await fetch(`${API_BASE}/tools/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tool_name,
        arguments: arguments_payload,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Tool execution failed");
    }
    return res.json();
  },

  async uploadToolDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/tools/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "File extraction failed");
    }
    return res.json();
  },

  // Authentication & Google OAuth Endpoints
  async getGoogleAuthUrl(): Promise<{ authorization_url: string; client_id_configured: boolean }> {
    const res = await fetch(`${API_BASE}/auth/google/url`);
    if (!res.ok) throw new Error("Failed to get Google auth URL");
    return res.json();
  },

  async exchangeGoogleCode(code: string, redirect_uri?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/google/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, redirect_uri }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to exchange Google OAuth code");
    }
    return res.json();
  },

  async getCurrentUser(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Unauthorized or invalid token");
    return res.json();
  },

  async refreshToken(refreshTokenStr: string): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshTokenStr }),
    });
    if (!res.ok) throw new Error("Failed to refresh token");
    return res.json();
  },

  async logoutUser(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.json().catch(() => ({}));
  },

  async registerWithPassword(data: { email: string; username: string; password: string; full_name?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed. Please check inputs.");
    }
    return res.json();
  },

  async loginWithPassword(data: { username_or_email: string; password: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Invalid username/email or password.");
    }
    return res.json();
  },

  async forgotPassword(email: string): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to initiate password reset.");
    }
    return res.json();
  },

  async resetPassword(data: { token: string; new_password: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to reset password.");
    }
    return res.json();
  },

  // ---------------------------------------------------------------------------
  // Plugin Marketplace API Methods
  // ---------------------------------------------------------------------------

  async getMarketplacePlugins(token?: string): Promise<PluginCatalogItem[]> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/plugins`, { headers });
    if (!res.ok) throw new Error("Failed to load marketplace plugins");
    return res.json();
  },

  async getUserIntegrations(token?: string): Promise<UserIntegration[]> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/integrations`, { headers });
    if (!res.ok) throw new Error("Failed to load user integrations");
    return res.json();
  },

  async connectMarketplacePlugin(pluginId: string, token?: string): Promise<{ authorization_url: string; state: string; plugin_id: string }> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/connect/${pluginId}`, {
      method: "POST",
      headers,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to initiate connection for ${pluginId}`);
    }
    return res.json();
  },

  async connectDirectPlugin(data: { plugin_id: string; access_token: string; account_email?: string; account_username?: string }, token?: string): Promise<any> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/connect-direct`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to connect plugin");
    }
    return res.json();
  },

  async disconnectMarketplacePlugin(pluginId: string, token?: string): Promise<any> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/disconnect/${pluginId}`, {
      method: "POST",
      headers,
    });
    if (!res.ok) throw new Error(`Failed to disconnect ${pluginId}`);
    return res.json();
  },

  async getMarketplacePermissions(pluginId: string, token?: string): Promise<PluginPermission[]> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/permissions/${pluginId}`, { headers });
    if (!res.ok) throw new Error("Failed to load plugin permissions");
    return res.json();
  },

  async updateMarketplacePermission(data: { plugin_id: string; tool_name: string; permission_level: string }, token?: string): Promise<any> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/permissions`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update tool permission");
    return res.json();
  },

  async approveMarketplaceTool(approvalId: string, token?: string): Promise<any> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/approvals/${approvalId}/approve`, {
      method: "POST",
      headers,
    });
    if (!res.ok) throw new Error("Failed to approve tool execution");
    return res.json();
  },

  async rejectMarketplaceTool(approvalId: string, token?: string): Promise<any> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/approvals/${approvalId}/reject`, {
      method: "POST",
      headers,
    });
    if (!res.ok) throw new Error("Failed to reject tool execution");
    return res.json();
  },

  async executeMarketplaceTool(data: { plugin_id: string; tool_name: string; arguments?: any; approval_token?: string }, token?: string): Promise<any> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/execute`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Tool execution failed");
    }
    return res.json();
  },

  async getMarketplaceAuditLogs(limit: number = 50, token?: string): Promise<AuditLogItem[]> {
    const rootBase = API_BASE.replace(/\/api\/v1$/, "");
    const headers: Record<string, string> = {};
    if (token && !token.startsWith("guest_")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${rootBase}/api/marketplace/audit-logs?limit=${limit}`, { headers });
    if (!res.ok) throw new Error("Failed to load audit logs");
    return res.json();
  },
};

// Export Plugin Marketplace types and functions
export interface PluginCatalogItem {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  icon: string;
  auth_type: string;
  scopes: string[];
  features: string[];
  is_active: boolean;
  is_connected: boolean;
  account_info?: {
    account_id?: string;
    account_email?: string;
    account_username?: string;
    avatar_url?: string;
  };
  connected_at?: string;
  tools: Array<{
    tool_name: string;
    qualified_name: string;
    description: string;
    input_schema: any;
    is_sensitive: boolean;
    default_permission: string;
  }>;
}

export interface UserIntegration {
  id: string;
  user_id: string;
  plugin_id: string;
  plugin_name: string;
  plugin_display_name: string;
  plugin_icon: string;
  account_id?: string;
  account_email?: string;
  account_username?: string;
  avatar_url?: string;
  status: string;
  scopes: string[];
  connected_at: string;
  updated_at: string;
}

export interface PluginPermission {
  plugin_id: string;
  tool_name: string;
  description: string;
  is_sensitive: boolean;
  permission_level: "ALLOW" | "APPROVAL_REQUIRED" | "DENY";
  default_permission: "ALLOW" | "APPROVAL_REQUIRED" | "DENY";
}

export interface AuditLogItem {
  id: string;
  user_id: string;
  plugin_id: string;
  tool_name: string;
  arguments: any;
  status: "SUCCESS" | "FAILED" | "DENIED" | "APPROVAL_REQUIRED";
  result?: any;
  error_message?: string;
  duration_ms: number;
  created_at: string;
}

export const getMarketplacePlugins = api.getMarketplacePlugins.bind(api);
export const getUserIntegrations = api.getUserIntegrations.bind(api);
export const connectMarketplacePlugin = api.connectMarketplacePlugin.bind(api);
export const connectDirectPlugin = api.connectDirectPlugin.bind(api);
export const disconnectMarketplacePlugin = api.disconnectMarketplacePlugin.bind(api);
export const getMarketplacePermissions = api.getMarketplacePermissions.bind(api);
export const updateMarketplacePermission = api.updateMarketplacePermission.bind(api);
export const approveMarketplaceTool = api.approveMarketplaceTool.bind(api);
export const rejectMarketplaceTool = api.rejectMarketplaceTool.bind(api);
export const executeMarketplaceTool = api.executeMarketplaceTool.bind(api);
export const getMarketplaceAuditLogs = api.getMarketplaceAuditLogs.bind(api);

// Export standalone helper functions for easy import
export const getGoogleAuthUrl = api.getGoogleAuthUrl.bind(api);
export const exchangeGoogleCode = api.exchangeGoogleCode.bind(api);
export const getCurrentUser = api.getCurrentUser.bind(api);
export const refreshToken = api.refreshToken.bind(api);
export const logoutUser = api.logoutUser.bind(api);
export const registerWithPassword = api.registerWithPassword.bind(api);
export const loginWithPassword = api.loginWithPassword.bind(api);
export const forgotPassword = api.forgotPassword.bind(api);
export const resetPassword = api.resetPassword.bind(api);
