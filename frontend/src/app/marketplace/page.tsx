"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  getMarketplacePlugins,
  getUserIntegrations,
  connectMarketplacePlugin,
  connectDirectPlugin,
  disconnectMarketplacePlugin,
  getMarketplacePermissions,
  updateMarketplacePermission,
  executeMarketplaceTool,
  getMarketplaceAuditLogs,
  PluginCatalogItem,
  UserIntegration,
  PluginPermission,
  AuditLogItem,
} from "@/lib/api";
import {
  Sparkles,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Shield,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Mail,
  Github,
  HardDrive,
  MessageSquare,
  FileText,
  Cpu,
  Lock,
  Unlock,
  Sliders,
  History,
  Layers,
  Zap,
  Info,
  Loader2,
  Key,
} from "lucide-react";

export default function MarketplacePage() {
  return (
    <React.Suspense fallback={<div className="min-h-screen bg-[#0D0D0E] flex items-center justify-center text-zinc-400">Loading marketplace...</div>}>
      <MarketplaceContent />
    </React.Suspense>
  );
}

function MarketplaceContent() {
  const { accessToken } = useAuth();
  const searchParams = useSearchParams();

  // State
  const [activeTab, setActiveTab] = useState<"catalog" | "connected" | "permissions" | "audit">("catalog");
  const [plugins, setPlugins] = useState<PluginCatalogItem[]>([]);
  const [integrations, setIntegrations] = useState<UserIntegration[]>([]);
  const [permissions, setPermissions] = useState<PluginPermission[]>([]);
  const [selectedPluginForPerms, setSelectedPluginForPerms] = useState<string>("gmail");
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  
  // Status banner from OAuth redirect
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Direct Mock Connection Modal
  const [directConnectModal, setDirectConnectModal] = useState<{ open: boolean; pluginId: string } | null>(null);
  const [mockEmail, setMockEmail] = useState<string>("founder@illusion.ai");

  // Load initial data
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [catalogData, userIntegData] = await Promise.all([
        getMarketplacePlugins(accessToken || undefined),
        getUserIntegrations(accessToken || undefined),
      ]);
      setPlugins(catalogData);
      setIntegrations(userIntegData);

      if (userIntegData.length > 0) {
        setSelectedPluginForPerms(userIntegData[0].plugin_id);
      }
    } catch (err: any) {
      console.error("Error loading marketplace data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Check query params for OAuth callbacks
    const connectedParam = searchParams.get("connected");
    const errorParam = searchParams.get("error");

    if (connectedParam) {
      setNotification({
        type: "success",
        message: `Successfully connected ${connectedParam.toUpperCase()} to Illusion AI!`,
      });
      setActiveTab("connected");
    } else if (errorParam) {
      setNotification({
        type: "error",
        message: `Connection failed: ${errorParam}`,
      });
    }
  }, [accessToken, searchParams]);

  // Load permissions when tab changes or selected plugin changes
  useEffect(() => {
    if (activeTab === "permissions" && selectedPluginForPerms) {
      getMarketplacePermissions(selectedPluginForPerms, accessToken || undefined)
        .then(setPermissions)
        .catch(console.error);
    } else if (activeTab === "audit") {
      getMarketplaceAuditLogs(50, accessToken || undefined)
        .then(setAuditLogs)
        .catch(console.error);
    }
  }, [activeTab, selectedPluginForPerms, accessToken]);

  // Handle Connect Plugin (OAuth Flow)
  const handleConnect = async (pluginId: string) => {
    setActionLoading(pluginId);
    try {
      const res = await connectMarketplacePlugin(pluginId, accessToken || undefined);
      if (res?.authorization_url) {
        // Redirect to provider OAuth
        window.location.href = res.authorization_url;
      }
    } catch (err: any) {
      // Fallback: open mock connection modal if credentials aren't configured in development
      setDirectConnectModal({ open: true, pluginId });
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Direct Mock Connect (Dev/Demo mode)
  const handleDirectConnect = async () => {
    if (!directConnectModal) return;
    setActionLoading("direct");
    try {
      await connectDirectPlugin(
        {
          plugin_id: directConnectModal.pluginId,
          access_token: `mock_${directConnectModal.pluginId}_token_${Date.now()}`,
          account_email: mockEmail,
          account_username: mockEmail.split("@")[0],
        },
        accessToken || undefined
      );
      setNotification({
        type: "success",
        message: `Connected ${directConnectModal.pluginId.toUpperCase()} with ${mockEmail}!`,
      });
      setDirectConnectModal(null);
      await fetchData();
      setActiveTab("connected");
    } catch (err: any) {
      alert(err.message || "Failed to connect plugin");
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Disconnect
  const handleDisconnect = async (pluginId: string) => {
    if (!confirm(`Are you sure you want to disconnect ${pluginId.toUpperCase()}?`)) return;
    setActionLoading(`disc_${pluginId}`);
    try {
      await disconnectMarketplacePlugin(pluginId, accessToken || undefined);
      setNotification({
        type: "success",
        message: `Disconnected ${pluginId.toUpperCase()} successfully.`,
      });
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Disconnect failed");
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Permission Change
  const handlePermissionChange = async (toolName: string, level: string) => {
    try {
      await updateMarketplacePermission(
        {
          plugin_id: selectedPluginForPerms,
          tool_name: toolName,
          permission_level: level,
        },
        accessToken || undefined
      );
      setPermissions((prev) =>
        prev.map((p) => (p.tool_name === toolName ? { ...p, permission_level: level as any } : p))
      );
    } catch (err: any) {
      alert("Failed to update permission: " + err.message);
    }
  };

  // Helper: render icon
  const renderIcon = (iconName: string, className = "w-5 h-5") => {
    switch (iconName.toLowerCase()) {
      case "mail":
        return <Mail className={className} />;
      case "github":
        return <Github className={className} />;
      case "harddrive":
        return <HardDrive className={className} />;
      case "messagesquare":
        return <MessageSquare className={className} />;
      case "filetext":
        return <FileText className={className} />;
      case "cpu":
      default:
        return <Cpu className={className} />;
    }
  };

  // Filter plugins
  const filteredPlugins = plugins.filter((p) => {
    const matchesSearch =
      p.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = selectedCategory === "all" || p.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="min-h-screen bg-[#0D0D0E] text-zinc-100 pb-16">
      {/* Hero Header */}
      <div className="border-b border-[#24242A] bg-gradient-to-b from-[#141418] to-[#0D0D0E] pt-10 pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-400 text-xs font-mono mb-3">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Extensible AI Ecosystem</span>
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
                Plugin Marketplace
                <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full font-mono border border-amber-500/30">
                  MCP Compatible
                </span>
              </h1>
              <p className="mt-2 text-sm text-zinc-400 max-w-2xl">
                Discover, connect, and manage authorized SaaS tools and developer integrations.
                Our LangGraph agent dynamically discovers tools and executes actions under default-deny security.
              </p>
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-3 gap-3 bg-[#18181D] border border-[#2B2B33] rounded-2xl p-4 text-center">
              <div>
                <div className="text-xl font-bold text-white">{plugins.length}</div>
                <div className="text-[11px] text-zinc-400">Available</div>
              </div>
              <div className="border-x border-[#2B2B33] px-3">
                <div className="text-xl font-bold text-amber-400">{integrations.length}</div>
                <div className="text-[11px] text-zinc-400">Connected</div>
              </div>
              <div>
                <div className="text-xl font-bold text-emerald-400">Default-Deny</div>
                <div className="text-[11px] text-zinc-400">Security</div>
              </div>
            </div>
          </div>

          {/* Notification banner */}
          {notification && (
            <div
              className={`mt-6 p-4 rounded-xl flex items-center justify-between text-xs font-medium border ${
                notification.type === "success"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-300"
              }`}
            >
              <div className="flex items-center gap-2">
                {notification.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                )}
                <span>{notification.message}</span>
              </div>
              <button
                onClick={() => setNotification(null)}
                className="text-zinc-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex items-center gap-2 mt-8 border-b border-[#24242A]">
            <button
              onClick={() => setActiveTab("catalog")}
              className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 ${
                activeTab === "catalog"
                  ? "border-amber-400 text-amber-400"
                  : "border-transparent text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Explore Plugins ({plugins.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("connected")}
              className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 ${
                activeTab === "connected"
                  ? "border-amber-400 text-amber-400"
                  : "border-transparent text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Connected Apps ({integrations.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("permissions")}
              className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 ${
                activeTab === "permissions"
                  ? "border-amber-400 text-amber-400"
                  : "border-transparent text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Sliders className="w-4 h-4" />
              <span>Permissions & Security</span>
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 ${
                activeTab === "audit"
                  ? "border-amber-400 text-amber-400"
                  : "border-transparent text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <History className="w-4 h-4" />
              <span>Audit History</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
            <span className="text-xs font-mono text-zinc-400">Loading Marketplace...</span>
          </div>
        ) : (
          <>
            {/* TAB 1: EXPLORE PLUGINS */}
            {activeTab === "catalog" && (
              <div>
                {/* Search & Category Filter */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-8">
                  <div className="relative w-full sm:w-80">
                    <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Search Gmail, GitHub, Slack..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-[#141418] border border-[#272730] rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
                    {["all", "email", "developer", "productivity", "communication", "tools"].map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                          selectedCategory === cat
                            ? "bg-amber-500 text-black font-semibold"
                            : "bg-[#18181D] text-zinc-400 hover:text-white border border-[#272730]"
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Plugin Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredPlugins.map((plugin) => (
                    <div
                      key={plugin.id}
                      className="bg-[#141418] border border-[#26262F] hover:border-amber-500/40 rounded-2xl p-6 flex flex-col justify-between transition-all group"
                    >
                      <div>
                        {/* Top bar with icon and status */}
                        <div className="flex items-center justify-between mb-4">
                          <div className="w-12 h-12 rounded-xl bg-[#1C1C22] border border-[#2E2E38] flex items-center justify-center text-amber-400 group-hover:scale-105 transition-transform">
                            {renderIcon(plugin.icon, "w-6 h-6")}
                          </div>
                          <div>
                            {plugin.is_connected ? (
                              <span className="inline-flex items-center gap-1 bg-emerald-500/15 text-emerald-400 text-[11px] font-mono px-2.5 py-1 rounded-full border border-emerald-500/30 font-medium">
                                <CheckCircle2 className="w-3 h-3" />
                                Connected
                              </span>
                            ) : plugin.is_active ? (
                              <span className="inline-flex items-center gap-1 bg-amber-500/10 text-amber-400 text-[11px] font-mono px-2.5 py-1 rounded-full border border-amber-500/20">
                                Ready
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 bg-zinc-800 text-zinc-400 text-[11px] font-mono px-2.5 py-1 rounded-full">
                                Coming Soon
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Title and description */}
                        <h3 className="text-base font-bold text-white mb-1.5 group-hover:text-amber-400 transition-colors">
                          {plugin.display_name}
                        </h3>
                        <p className="text-xs text-zinc-400 leading-relaxed mb-4">
                          {plugin.description}
                        </p>

                        {/* Features List */}
                        <div className="space-y-1.5 mb-6">
                          {plugin.features.slice(0, 3).map((feat, idx) => (
                            <div key={idx} className="flex items-center gap-2 text-[11px] text-zinc-300">
                              <CheckCircle2 className="w-3.5 h-3.5 text-amber-500/70 shrink-0" />
                              <span className="truncate">{feat}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Card Action Footer */}
                      <div className="pt-4 border-t border-[#222228] flex items-center justify-between gap-3">
                        <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                          {plugin.tools.length} Tools
                        </span>

                        {plugin.is_connected ? (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => {
                                setSelectedPluginForPerms(plugin.id);
                                setActiveTab("permissions");
                              }}
                              className="px-3 py-1.5 rounded-lg border border-[#2B2B36] bg-[#1A1A22] text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                            >
                              Permissions
                            </button>
                            <button
                              onClick={() => handleDisconnect(plugin.id)}
                              className="px-3 py-1.5 rounded-lg border border-rose-500/20 bg-rose-500/10 text-xs font-medium text-rose-400 hover:bg-rose-500/20 transition-colors"
                            >
                              Disconnect
                            </button>
                          </div>
                        ) : plugin.is_active ? (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setDirectConnectModal({ open: true, pluginId: plugin.id })}
                              className="px-2.5 py-1.5 rounded-lg border border-[#2B2B36] text-[11px] text-zinc-400 hover:text-white"
                              title="Connect test or mock credentials"
                            >
                              Mock Connect
                            </button>
                            <button
                              onClick={() => handleConnect(plugin.id)}
                              disabled={actionLoading === plugin.id}
                              className="flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-black px-4 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all"
                            >
                              {actionLoading === plugin.id ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <>
                                  <span>Connect</span>
                                  <ArrowRight className="w-3.5 h-3.5" />
                                </>
                              )}
                            </button>
                          </div>
                        ) : (
                          <button
                            disabled
                            className="bg-[#1C1C22] text-zinc-500 px-3.5 py-1.5 rounded-lg text-xs font-medium cursor-not-allowed"
                          >
                            Coming Soon
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 2: CONNECTED APPS */}
            {activeTab === "connected" && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-lg font-bold text-white">Active Integrations</h2>
                    <p className="text-xs text-zinc-400">
                      Applications currently authorized to interact with your Illusion AI assistant.
                    </p>
                  </div>
                  <button
                    onClick={fetchData}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#272730] bg-[#141418] text-xs font-medium text-zinc-300 hover:text-white"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                  </button>
                </div>

                {integrations.length === 0 ? (
                  <div className="text-center py-16 bg-[#141418] border border-[#26262F] rounded-2xl p-8">
                    <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto mb-3">
                      <Zap className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-white mb-1">No Connected Apps Yet</h3>
                    <p className="text-xs text-zinc-400 max-w-md mx-auto mb-6">
                      Connect Gmail or GitHub from the Explore tab to allow Illusion AI to read communications,
                      inspect repositories, and compose drafts with your permission.
                    </p>
                    <button
                      onClick={() => setActiveTab("catalog")}
                      className="bg-amber-500 hover:bg-amber-400 text-black px-4 py-2 rounded-xl text-xs font-semibold shadow-sm inline-flex items-center gap-2"
                    >
                      <span>Explore Catalog</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {integrations.map((integ) => (
                      <div
                        key={integ.id}
                        className="bg-[#141418] border border-[#26262F] rounded-2xl p-6"
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-xl bg-[#1C1C22] border border-[#2E2E38] flex items-center justify-center text-amber-400">
                              {renderIcon(integ.plugin_icon, "w-6 h-6")}
                            </div>
                            <div>
                              <h3 className="text-base font-bold text-white">{integ.plugin_display_name}</h3>
                              <span className="text-xs text-zinc-400 font-mono">
                                {integ.account_email || integ.account_username || "Authorized Account"}
                              </span>
                            </div>
                          </div>

                          <span className="inline-flex items-center gap-1 bg-emerald-500/15 text-emerald-400 text-[11px] font-mono px-2.5 py-1 rounded-full border border-emerald-500/30">
                            <CheckCircle2 className="w-3 h-3" />
                            Active
                          </span>
                        </div>

                        <div className="bg-[#19191F] rounded-xl p-3 text-xs border border-[#272730] space-y-1.5 mb-6">
                          <div className="flex justify-between text-zinc-400">
                            <span>Account ID:</span>
                            <span className="font-mono text-zinc-300">{integ.account_id || "acc_default"}</span>
                          </div>
                          <div className="flex justify-between text-zinc-400">
                            <span>Connected Since:</span>
                            <span className="text-zinc-300">
                              {new Date(integ.connected_at).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex justify-between text-zinc-400">
                            <span>Token Encryption:</span>
                            <span className="text-emerald-400 font-mono">Fernet AES-128</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-2">
                          <button
                            onClick={() => {
                              setSelectedPluginForPerms(integ.plugin_id);
                              setActiveTab("permissions");
                            }}
                            className="flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 font-medium"
                          >
                            <Sliders className="w-3.5 h-3.5" />
                            <span>Manage Tool Permissions</span>
                          </button>

                          <button
                            onClick={() => handleDisconnect(integ.plugin_id)}
                            className="px-3 py-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 text-xs font-medium text-rose-400 hover:bg-rose-500/20 transition-colors"
                          >
                            Disconnect
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: PERMISSIONS & SECURITY */}
            {activeTab === "permissions" && (
              <div>
                <div className="bg-[#141418] border border-[#26262F] rounded-2xl p-6 mb-8">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <ShieldCheck className="w-5 h-5 text-amber-400" />
                        <h2 className="text-lg font-bold text-white">Default-Deny Permission Manager</h2>
                      </div>
                      <p className="text-xs text-zinc-400">
                        Configure authorization for individual AI tool actions. Write or sensitive actions default to
                        <span className="text-amber-400 font-mono ml-1">APPROVAL_REQUIRED</span>.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs text-zinc-400">Target Plugin:</span>
                      <select
                        value={selectedPluginForPerms}
                        onChange={(e) => setSelectedPluginForPerms(e.target.value)}
                        className="bg-[#1C1C22] border border-[#2B2B36] rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
                      >
                        {plugins.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.display_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Permissions Table */}
                <div className="bg-[#141418] border border-[#26262F] rounded-2xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#18181F] border-b border-[#24242A] text-zinc-400 font-mono text-[11px] uppercase">
                        <tr>
                          <th className="py-3.5 px-6">Tool Identifier</th>
                          <th className="py-3.5 px-6">Description</th>
                          <th className="py-3.5 px-6">Risk Profile</th>
                          <th className="py-3.5 px-6">Permission Level</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#222228]">
                        {permissions.map((perm) => (
                          <tr key={perm.tool_name} className="hover:bg-[#18181E] transition-colors">
                            <td className="py-4 px-6 font-mono text-white font-medium">
                              {perm.tool_name}
                            </td>
                            <td className="py-4 px-6 text-zinc-400 max-w-sm">
                              {perm.description}
                            </td>
                            <td className="py-4 px-6">
                              {perm.is_sensitive ? (
                                <span className="inline-flex items-center gap-1 bg-amber-500/15 text-amber-400 px-2 py-0.5 rounded text-[10px] font-mono border border-amber-500/25">
                                  <Lock className="w-2.5 h-2.5" />
                                  Sensitive Action
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded text-[10px] font-mono">
                                  <Unlock className="w-2.5 h-2.5" />
                                  Read-only
                                </span>
                              )}
                            </td>
                            <td className="py-4 px-6">
                              <select
                                value={perm.permission_level}
                                onChange={(e) => handlePermissionChange(perm.tool_name, e.target.value)}
                                className={`rounded-lg px-2.5 py-1 text-xs font-semibold focus:outline-none border ${
                                  perm.permission_level === "ALLOW"
                                    ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                                    : perm.permission_level === "APPROVAL_REQUIRED"
                                    ? "bg-amber-500/15 border-amber-500/30 text-amber-400"
                                    : "bg-rose-500/15 border-rose-500/30 text-rose-400"
                                }`}
                              >
                                <option value="ALLOW" className="bg-[#141418] text-white">ALLOW (Execute Instantly)</option>
                                <option value="APPROVAL_REQUIRED" className="bg-[#141418] text-white">APPROVAL_REQUIRED (Ask in Chat)</option>
                                <option value="DENY" className="bg-[#141418] text-white">DENY (Block Execution)</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: AUDIT HISTORY */}
            {activeTab === "audit" && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-lg font-bold text-white">Execution Audit Logs</h2>
                    <p className="text-xs text-zinc-400">
                      Cryptographic and audit log trail of all plugin actions initiated by the AI assistant.
                    </p>
                  </div>
                  <button
                    onClick={() => getMarketplaceAuditLogs(50, accessToken || undefined).then(setAuditLogs)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#272730] bg-[#141418] text-xs font-medium text-zinc-300 hover:text-white"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                  </button>
                </div>

                <div className="bg-[#141418] border border-[#26262F] rounded-2xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#18181F] border-b border-[#24242A] text-zinc-400 font-mono text-[11px] uppercase">
                        <tr>
                          <th className="py-3 px-6">Timestamp</th>
                          <th className="py-3 px-6">Plugin</th>
                          <th className="py-3 px-6">Tool Action</th>
                          <th className="py-3 px-6">Status</th>
                          <th className="py-3 px-6">Latency</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#222228]">
                        {auditLogs.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="py-12 text-center text-zinc-500">
                              No plugin executions recorded yet.
                            </td>
                          </tr>
                        ) : (
                          auditLogs.map((log) => (
                            <tr key={log.id} className="hover:bg-[#18181E] transition-colors">
                              <td className="py-3.5 px-6 font-mono text-zinc-400 text-[11px]">
                                {new Date(log.created_at).toLocaleTimeString()}
                              </td>
                              <td className="py-3.5 px-6 capitalize font-semibold text-white">
                                {log.plugin_id}
                              </td>
                              <td className="py-3.5 px-6 font-mono text-zinc-300">
                                {log.tool_name}
                              </td>
                              <td className="py-3.5 px-6">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                                    log.status === "SUCCESS"
                                      ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25"
                                      : log.status === "APPROVAL_REQUIRED"
                                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/25"
                                      : "bg-rose-500/15 text-rose-400 border border-rose-500/25"
                                  }`}
                                >
                                  {log.status}
                                </span>
                              </td>
                              <td className="py-3.5 px-6 font-mono text-zinc-400">
                                {log.duration_ms.toFixed(1)} ms
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Direct Mock Connection Modal */}
      {directConnectModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#141418] border border-[#2B2B36] rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Key className="w-4 h-4 text-amber-400" />
              <span>Connect {directConnectModal.pluginId.toUpperCase()} Sandbox</span>
            </h3>
            <p className="text-xs text-zinc-400 mb-4">
              Enter your test email or account identifier to connect in development/mock mode without requiring production OAuth credentials.
            </p>

            <div className="space-y-3 mb-6">
              <div>
                <label className="block text-[11px] font-mono text-zinc-400 mb-1">Account Email / ID</label>
                <input
                  type="text"
                  value={mockEmail}
                  onChange={(e) => setMockEmail(e.target.value)}
                  className="w-full bg-[#1C1C22] border border-[#2B2B36] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5">
              <button
                onClick={() => setDirectConnectModal(null)}
                className="px-3.5 py-1.5 rounded-lg border border-[#2B2B36] text-xs text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleDirectConnect}
                disabled={actionLoading === "direct"}
                className="bg-amber-500 hover:bg-amber-400 text-black px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2"
              >
                {actionLoading === "direct" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Authorize & Connect</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
