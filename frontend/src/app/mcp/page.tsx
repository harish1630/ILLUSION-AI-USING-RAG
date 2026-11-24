"use client";

import React, { useState, useEffect } from "react";
import {
  Server,
  Terminal,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  Plus,
  Unplug,
  Check,
  X,
  Clock,
  Layers,
  Search,
  Activity,
  FileCode,
  Sliders,
  ChevronRight,
  Code2,
} from "lucide-react";

interface MCPServer {
  id: string;
  name: string;
  description?: string;
  transport: string;
  transport_type?: string;
  command?: string;
  args: string[];
  url?: string;
  status: "connected" | "disconnected" | "connecting" | "error";
  tools_count?: number;
  tool_count?: number;
  created_at: string;
}

interface MCPTool {
  id: string;
  server_id: string;
  server_name: string;
  tool_name: string;
  qualified_name: string;
  description: string;
  input_schema: any;
  permission_level: "ALLOW" | "APPROVAL_REQUIRED" | "DENY";
  is_enabled: boolean;
}

interface MCPHealth {
  status: string;
  total_servers: number;
  active_servers: number;
  total_tools: number;
  pending_approvals: number;
  default_policy: string;
}

interface MCPApproval {
  id: string;
  user_id: string;
  server_id: string;
  tool_name: string;
  arguments: any;
  status: "PENDING" | "APPROVED" | "REJECTED";
  created_at: string;
}

interface MCPLog {
  id: string;
  server_id: string;
  tool_name: string;
  status: string;
  duration_ms: number;
  executed_at: string;
  result?: any;
  error_message?: string;
}

function MCPDashboardContent() {
  const [activeTab, setActiveTab] = useState<"overview" | "servers" | "tools" | "permissions" | "approvals" | "logs">("overview");
  const [health, setHealth] = useState<MCPHealth | null>(null);
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [approvals, setApprovals] = useState<MCPApproval[]>([]);
  const [logs, setLogs] = useState<MCPLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [toolSearch, setToolSearch] = useState<string>("");

  // Test Tool Execution modal
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [executingArgs, setExecutingArgs] = useState<string>("{}");
  const [execResult, setExecResult] = useState<any>(null);
  const [execLoading, setExecLoading] = useState<boolean>(false);

  // Add Server modal
  const [showAddServer, setShowAddServer] = useState<boolean>(false);
  const [newServerName, setNewServerName] = useState("");
  const [newServerTransport, setNewServerTransport] = useState("stdio");
  const [newServerCommand, setNewServerCommand] = useState("");
  const [newServerArgs, setNewServerArgs] = useState("");
  const [newServerUrl, setNewServerUrl] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [hRes, sRes, tRes, aRes, lRes] = await Promise.all([
        fetch("/api/mcp/health").then((r) => (r.ok ? r.json() : null)),
        fetch("/api/mcp/servers").then((r) => (r.ok ? r.json() : [])),
        fetch("/api/mcp/tools").then((r) => (r.ok ? r.json() : [])),
        fetch("/api/mcp/approvals").then((r) => (r.ok ? r.json() : [])),
        fetch("/api/mcp/logs?limit=50").then((r) => (r.ok ? r.json() : [])),
      ]);
      setHealth(hRes);
      setServers(sRes || []);
      setTools(tRes || []);
      setApprovals(aRes || []);
      setLogs(lRes || []);
    } catch (e) {
      console.error("Failed to load MCP dashboard data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleConnectServer = async (id: string) => {
    await fetch(`/api/mcp/servers/${id}/connect`, { method: "POST" });
    fetchData();
  };

  const handleDisconnectServer = async (id: string) => {
    await fetch(`/api/mcp/servers/${id}/disconnect`, { method: "POST" });
    fetchData();
  };

  const handleApprove = async (approvalId: string) => {
    await fetch(`/api/mcp/approvals/${approvalId}/approve`, { method: "POST" });
    fetchData();
  };

  const handleReject = async (approvalId: string) => {
    await fetch(`/api/mcp/approvals/${approvalId}/reject`, { method: "POST" });
    fetchData();
  };

  const handleSetPermission = async (server_id: string, tool_name: string, level: string) => {
    await fetch("/api/mcp/permissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ server_id, tool_name, permission_level: level }),
    });
    fetchData();
  };

  const handleExecuteTool = async () => {
    if (!selectedTool) return;
    setExecLoading(true);
    setExecResult(null);
    try {
      const parsedArgs = JSON.parse(executingArgs || "{}");
      const resp = await fetch("/api/mcp/tools/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          server_id: selectedTool.server_id,
          tool_name: selectedTool.tool_name,
          arguments: parsedArgs,
        }),
      });
      const data = await resp.json();
      setExecResult(data);
      // Refresh logs
      fetch("/api/mcp/logs?limit=50").then((r) => r.json()).then(setLogs);
    } catch (err: any) {
      setExecResult({ error: `JSON Parse or Network Error: ${err.message}` });
    } finally {
      setExecLoading(false);
    }
  };

  const handleAddServer = async (e: React.FormEvent) => {
    e.preventDefault();
    const argsArr = newServerArgs
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);

    await fetch("/api/mcp/servers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: newServerName,
        transport: newServerTransport,
        command: newServerCommand || undefined,
        args: argsArr,
        url: newServerUrl || undefined,
        auto_connect: true,
      }),
    });

    setShowAddServer(false);
    setNewServerName("");
    setNewServerCommand("");
    setNewServerArgs("");
    setNewServerUrl("");
    fetchData();
  };

  const filteredTools = tools.filter(
    (t) =>
      t.tool_name.toLowerCase().includes(toolSearch.toLowerCase()) ||
      t.server_id.toLowerCase().includes(toolSearch.toLowerCase()) ||
      t.description.toLowerCase().includes(toolSearch.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#0A0A0C] text-white">
      {/* Top Banner */}
      <div className="border-b border-[#1E1E24] bg-[#0E0E12]/80 backdrop-blur-md px-6 py-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  Model Context Protocol (MCP) Hub
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                    2.0 Active
                  </span>
                </h1>
                <p className="text-sm text-neutral-400">
                  Dynamic Tool Discovery, Sandboxed Execution, and Human Approval Pipeline
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              className="px-3.5 py-2 rounded-lg bg-[#18181F] hover:bg-[#22222B] border border-[#2B2B36] text-neutral-300 text-sm flex items-center gap-2 transition"
            >
              <RotateCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button
              onClick={() => setShowAddServer(true)}
              className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-semibold text-sm flex items-center gap-2 transition shadow-lg shadow-amber-500/20"
            >
              <Plus className="w-4 h-4" />
              Add Server
            </button>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="max-w-7xl mx-auto mt-6 flex gap-2 border-b border-[#1E1E24] pb-px">
          {[
            { id: "overview", label: "Overview", icon: Activity },
            { id: "servers", label: `Servers (${servers.length})`, icon: Server },
            { id: "tools", label: `Tool Explorer (${tools.length})`, icon: Terminal },
            { id: "permissions", label: "Permissions Matrix", icon: Shield },
            {
              id: "approvals",
              label: `Approvals (${approvals.filter((a) => a.status === "PENDING").length})`,
              icon: AlertTriangle,
            },
            { id: "logs", label: "Execution Logs", icon: FileCode },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition -mb-px ${
                  active
                    ? "border-amber-400 text-amber-400 bg-amber-400/5"
                    : "border-transparent text-neutral-400 hover:text-white hover:border-neutral-700"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* =========================================================================
            TAB 1: OVERVIEW
        ========================================================================= */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Health Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-xl bg-[#121217] border border-[#22222B] relative overflow-hidden">
                <div className="text-xs uppercase tracking-wider text-neutral-400 font-mono">Active Servers</div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">
                    {health?.active_servers ?? 0}
                  </span>
                  <span className="text-sm text-neutral-500">/ {health?.total_servers ?? 0} configured</span>
                </div>
                <div className="mt-3 text-xs text-emerald-400 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  illusion_custom operational
                </div>
              </div>

              <div className="p-5 rounded-xl bg-[#121217] border border-[#22222B]">
                <div className="text-xs uppercase tracking-wider text-neutral-400 font-mono">Discovered Tools</div>
                <div className="mt-2 text-3xl font-extrabold text-white">{health?.total_tools ?? 0}</div>
                <div className="mt-3 text-xs text-neutral-400">Available to LLM router</div>
              </div>

              <div className="p-5 rounded-xl bg-[#121217] border border-[#22222B]">
                <div className="text-xs uppercase tracking-wider text-neutral-400 font-mono">Pending Approvals</div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-amber-400">
                    {approvals.filter((a) => a.status === "PENDING").length}
                  </span>
                  <span className="text-xs text-neutral-400">requests</span>
                </div>
                <div className="mt-3 text-xs text-neutral-400">Human-in-the-loop gate</div>
              </div>

              <div className="p-5 rounded-xl bg-[#121217] border border-[#22222B]">
                <div className="text-xs uppercase tracking-wider text-neutral-400 font-mono">Default Policy</div>
                <div className="mt-2 text-3xl font-extrabold text-red-400">DENY</div>
                <div className="mt-3 text-xs text-neutral-400">Zero-trust security model</div>
              </div>
            </div>

            {/* Architecture Card */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-[#121217] to-[#181822] border border-[#242432]">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-amber-400" />
                Hybrid MCP Architecture
              </h2>
              <p className="mt-2 text-sm text-neutral-400 max-w-3xl">
                Illusion AI combines internal LangGraph tools, custom built-in diagnostics (
                <span className="text-amber-400 font-mono">illusion_custom</span>), and remote MCP servers via STDIO and
                Streamable HTTP/SSE. Every request undergoes 3-tier permission evaluation with strict 15s execution timeout.
              </p>

              <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                <div className="p-4 rounded-xl bg-[#0E0E12] border border-[#22222B]">
                  <div className="text-amber-400 font-semibold mb-1">1. User & Intent Router</div>
                  <div className="text-neutral-400">Classifies queries and maps them to discovered MCP tool schemas dynamically.</div>
                </div>
                <div className="p-4 rounded-xl bg-[#0E0E12] border border-[#22222B]">
                  <div className="text-cyan-400 font-semibold mb-1">2. Policy & Approval Engine</div>
                  <div className="text-neutral-400">Enforces ALLOW, APPROVAL_REQUIRED, or strict default DENY per user and tool.</div>
                </div>
                <div className="p-4 rounded-xl bg-[#0E0E12] border border-[#22222B]">
                  <div className="text-emerald-400 font-semibold mb-1">3. Sandboxed Executor</div>
                  <div className="text-neutral-400">Runs tools under a 15-second timeout and records comprehensive audit logs.</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 2: SERVERS
        ========================================================================= */}
        {activeTab === "servers" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4">
              {servers.map((s) => (
                <div
                  key={s.id}
                  className="p-5 rounded-xl bg-[#121217] border border-[#22222B] flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-[#1A1A22] border border-[#2C2C38] flex items-center justify-center text-amber-400">
                      <Server className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white text-base">{s.name}</h3>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#1F1F2A] text-neutral-300">
                          {s.id}
                        </span>
                        <span className="text-xs uppercase px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                          {s.transport}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-400 mt-1 max-w-xl">{s.description || "No description provided."}</p>
                      <div className="mt-2 text-xs text-neutral-500 font-mono flex items-center gap-4">
                        <span>Tools: {s.tool_count ?? s.tools_count ?? 0}</span>
                        {s.command && <span>Command: {s.command}</span>}
                        {s.url && <span>URL: {s.url}</span>}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-mono flex items-center gap-1.5 ${
                        s.status === "connected"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-neutral-800 text-neutral-400"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          s.status === "connected" ? "bg-emerald-400 animate-pulse" : "bg-neutral-500"
                        }`}
                      ></span>
                      {s.status.toUpperCase()}
                    </span>

                    {s.status === "connected" ? (
                      <button
                        onClick={() => handleDisconnectServer(s.id)}
                        className="px-3 py-1.5 text-xs rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition flex items-center gap-1"
                      >
                        <Unplug className="w-3.5 h-3.5" />
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => handleConnectServer(s.id)}
                        className="px-3 py-1.5 text-xs rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 transition flex items-center gap-1"
                      >
                        <Play className="w-3.5 h-3.5" />
                        Connect
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 3: TOOL EXPLORER
        ========================================================================= */}
        {activeTab === "tools" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-neutral-500" />
                <input
                  type="text"
                  placeholder="Search discovered tools by name, server, or description..."
                  value={toolSearch}
                  onChange={(e) => setToolSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-[#121217] border border-[#22222B] rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-400"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredTools.map((t) => (
                <div
                  key={t.qualified_name}
                  className="p-5 rounded-xl bg-[#121217] border border-[#22222B] flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-amber-400" />
                        <span className="font-bold text-white text-sm">{t.tool_name}</span>
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded bg-[#1B1B24] text-neutral-300 font-mono">
                        {t.server_id}
                      </span>
                    </div>
                    <p className="text-xs text-neutral-400 mt-2 line-clamp-2">{t.description}</p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-[#1C1C24] flex items-center justify-between">
                    <span className="text-[11px] font-mono text-neutral-500">
                      Params: {Object.keys(t.input_schema?.properties || {}).length}
                    </span>
                    <button
                      onClick={() => {
                        setSelectedTool(t);
                        setExecutingArgs(
                          JSON.stringify(
                            t.tool_name === "calculate" ? { expression: "125 * 4" } : {},
                            null,
                            2
                          )
                        );
                      }}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1.5 transition"
                    >
                      <Play className="w-3 h-3" />
                      Run Tool
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 4: PERMISSIONS MATRIX
        ========================================================================= */}
        {activeTab === "permissions" && (
          <div className="p-6 rounded-xl bg-[#121217] border border-[#22222B] space-y-4">
            <div>
              <h3 className="font-bold text-white">Tool Execution Permissions</h3>
              <p className="text-xs text-neutral-400 mt-1">
                Configure whether tools execute automatically (ALLOW), require human confirmation (APPROVAL_REQUIRED), or are blocked (DENY).
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[#22222B] text-xs font-mono text-neutral-500 uppercase">
                    <th className="py-3 px-4">Tool Name</th>
                    <th className="py-3 px-4">Server</th>
                    <th className="py-3 px-4">Current Policy</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1C1C24] font-mono text-xs">
                  {tools.map((t) => (
                    <tr key={t.qualified_name} className="hover:bg-[#16161D]">
                      <td className="py-3 px-4 font-bold text-white">{t.tool_name}</td>
                      <td className="py-3 px-4 text-neutral-400">{t.server_id}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] ${
                            t.tool_name === "calculate" || t.tool_name.startsWith("get_")
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }`}
                        >
                          {t.tool_name === "calculate" || t.tool_name.startsWith("get_") ? "ALLOW" : "DENY"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex gap-1">
                          <button
                            onClick={() => handleSetPermission(t.server_id, t.tool_name, "ALLOW")}
                            className="px-2 py-1 rounded bg-[#1E1E28] hover:bg-emerald-500/20 hover:text-emerald-400 text-neutral-300 transition"
                          >
                            Allow
                          </button>
                          <button
                            onClick={() => handleSetPermission(t.server_id, t.tool_name, "APPROVAL_REQUIRED")}
                            className="px-2 py-1 rounded bg-[#1E1E28] hover:bg-amber-500/20 hover:text-amber-400 text-neutral-300 transition"
                          >
                            Ask Approval
                          </button>
                          <button
                            onClick={() => handleSetPermission(t.server_id, t.tool_name, "DENY")}
                            className="px-2 py-1 rounded bg-[#1E1E28] hover:bg-red-500/20 hover:text-red-400 text-neutral-300 transition"
                          >
                            Deny
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 5: APPROVAL CENTER
        ========================================================================= */}
        {activeTab === "approvals" && (
          <div className="space-y-4">
            {approvals.length === 0 ? (
              <div className="p-8 rounded-xl bg-[#121217] border border-[#22222B] text-center text-neutral-500">
                <CheckCircle2 className="w-8 h-8 text-neutral-600 mx-auto mb-2" />
                No pending or historical approval requests.
              </div>
            ) : (
              approvals.map((req) => (
                <div
                  key={req.id}
                  className="p-5 rounded-xl bg-[#121217] border border-[#22222B] flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      <span className="font-bold text-white text-sm">{req.tool_name}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-[#1B1B24] text-neutral-400 font-mono">
                        {req.server_id}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-mono ${
                          req.status === "PENDING"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : req.status === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {req.status}
                      </span>
                    </div>
                    <pre className="mt-2 text-xs font-mono bg-[#0A0A0E] p-3 rounded-lg text-neutral-300 max-w-xl overflow-x-auto">
                      {JSON.stringify(req.arguments, null, 2)}
                    </pre>
                  </div>

                  {req.status === "PENDING" && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleApprove(req.id)}
                        className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-500 text-black hover:bg-emerald-400 transition flex items-center gap-1.5"
                      >
                        <Check className="w-3.5 h-3.5" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(req.id)}
                        className="px-4 py-2 text-xs font-semibold rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition flex items-center gap-1.5"
                      >
                        <X className="w-3.5 h-3.5" />
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* =========================================================================
            TAB 6: EXECUTION LOGS
        ========================================================================= */}
        {activeTab === "logs" && (
          <div className="p-6 rounded-xl bg-[#121217] border border-[#22222B]">
            <h3 className="font-bold text-white text-base mb-4">MCP Tool Audit Trail</h3>
            <div className="space-y-3 font-mono text-xs">
              {logs.length === 0 ? (
                <div className="text-neutral-500">No tool execution logs found yet.</div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="p-3 rounded-lg bg-[#0E0E12] border border-[#1E1E26]">
                    <div className="flex items-center justify-between text-neutral-400">
                      <span className="text-white font-bold">{log.tool_name}</span>
                      <span className="text-[11px] text-neutral-500">{log.executed_at}</span>
                    </div>
                    <div className="mt-1 flex items-center gap-4 text-[11px]">
                      <span className="text-neutral-400">Server: {log.server_id}</span>
                      <span className="text-neutral-400">Duration: {log.duration_ms.toFixed(2)} ms</span>
                      <span
                        className={
                          log.status === "SUCCESS"
                            ? "text-emerald-400 font-bold"
                            : "text-red-400 font-bold"
                        }
                      >
                        {log.status}
                      </span>
                    </div>
                    {log.error_message && (
                      <div className="mt-2 text-red-400 bg-red-950/30 p-2 rounded">{log.error_message}</div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* =========================================================================
          MODAL: RUN TOOL
      ========================================================================= */}
      {selectedTool && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl bg-[#121217] border border-[#2A2A38] rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code2 className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-white">Execute MCP Tool</h3>
              </div>
              <button
                onClick={() => setSelectedTool(null)}
                className="text-neutral-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <div className="font-mono text-xs text-amber-400">
                {selectedTool.server_id}:{selectedTool.tool_name}
              </div>
              <p className="text-xs text-neutral-400 mt-1">{selectedTool.description}</p>
            </div>

            <div>
              <label className="text-xs font-mono text-neutral-400 mb-1 block">Input Arguments (JSON)</label>
              <textarea
                rows={5}
                value={executingArgs}
                onChange={(e) => setExecutingArgs(e.target.value)}
                className="w-full bg-[#0A0A0E] border border-[#22222B] rounded-xl p-3 font-mono text-xs text-white focus:outline-none focus:border-amber-400"
              />
            </div>

            {execResult && (
              <div>
                <label className="text-xs font-mono text-neutral-400 mb-1 block">Output Result</label>
                <pre className="bg-[#0A0A0E] border border-[#22222B] rounded-xl p-3 font-mono text-xs text-emerald-400 max-h-40 overflow-y-auto">
                  {JSON.stringify(execResult, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setSelectedTool(null)}
                className="px-4 py-2 text-xs rounded-lg bg-[#181820] text-neutral-300 hover:bg-[#22222C]"
              >
                Close
              </button>
              <button
                disabled={execLoading}
                onClick={handleExecuteTool}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-400 text-black flex items-center gap-1.5 transition"
              >
                <Play className="w-3.5 h-3.5" />
                {execLoading ? "Executing..." : "Execute"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: ADD SERVER
      ========================================================================= */}
      {showAddServer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <form
            onSubmit={handleAddServer}
            className="w-full max-w-lg bg-[#121217] border border-[#2A2A38] rounded-2xl p-6 shadow-2xl space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-base">Add MCP Server</h3>
              <button onClick={() => setShowAddServer(false)} className="text-neutral-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="text-xs font-mono text-neutral-400 mb-1 block">Server Name</label>
              <input
                required
                type="text"
                placeholder="e.g. GitHub Copilot, Postgres Inspector"
                value={newServerName}
                onChange={(e) => setNewServerName(e.target.value)}
                className="w-full bg-[#0A0A0E] border border-[#22222B] rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-amber-400"
              />
            </div>

            <div>
              <label className="text-xs font-mono text-neutral-400 mb-1 block">Transport Type</label>
              <select
                value={newServerTransport}
                onChange={(e) => setNewServerTransport(e.target.value)}
                className="w-full bg-[#0A0A0E] border border-[#22222B] rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-amber-400"
              >
                <option value="stdio">STDIO Subprocess</option>
                <option value="sse">Server-Sent Events (SSE)</option>
                <option value="http">Streamable HTTP</option>
              </select>
            </div>

            {newServerTransport === "stdio" ? (
              <>
                <div>
                  <label className="text-xs font-mono text-neutral-400 mb-1 block">Command Executable</label>
                  <input
                    type="text"
                    placeholder="e.g. npx, python, node"
                    value={newServerCommand}
                    onChange={(e) => setNewServerCommand(e.target.value)}
                    className="w-full bg-[#0A0A0E] border border-[#22222B] rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-neutral-400 mb-1 block">Command Arguments (one per line)</label>
                  <textarea
                    rows={3}
                    placeholder="-y&#10;@modelcontextprotocol/server-postgres"
                    value={newServerArgs}
                    onChange={(e) => setNewServerArgs(e.target.value)}
                    className="w-full bg-[#0A0A0E] border border-[#22222B] rounded-xl p-2.5 font-mono text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                </div>
              </>
            ) : (
              <div>
                <label className="text-xs font-mono text-neutral-400 mb-1 block">Endpoint URL</label>
                <input
                  type="url"
                  placeholder="http://localhost:8080/sse"
                  value={newServerUrl}
                  onChange={(e) => setNewServerUrl(e.target.value)}
                  className="w-full bg-[#0A0A0E] border border-[#22222B] rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-amber-400"
                />
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowAddServer(false)}
                className="px-4 py-2 text-xs rounded-lg bg-[#181820] text-neutral-300 hover:bg-[#22222C]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-400 text-black transition"
              >
                Register Server
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default function MCPDashboard() {
  return <MCPDashboardContent />;
}
