"use client";

import React, { useState, useEffect } from "react";
import {
  Github,
  GitBranch,
  Star,
  Lock,
  Globe,
  RotateCw,
  Unplug,
  ExternalLink,
  Code2,
  Search,
  CheckCircle2,
  FileText,
  GitCommit,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface GitHubStatus {
  is_connected: boolean;
  user_id?: string;
  github_user_id?: string;
  github_username?: string;
  github_email?: string;
  avatar_url?: string;
  connected_at?: string;
}

interface Repository {
  name: string;
  full_name: string;
  owner: string;
  private: boolean;
  description?: string;
  html_url: string;
  default_branch: string;
  stars: number;
  forks: number;
  language?: string;
  updated_at?: string;
}

function GitHubPageContent() {
  const [status, setStatus] = useState<GitHubStatus | null>(null);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>("");
  const [visibility, setVisibility] = useState<string>("all");
  const [analyzingRepo, setAnalyzingRepo] = useState<string | null>(null);

  const fetchStatusAndRepos = async () => {
    setLoading(true);
    try {
      const statusRes = await fetch("/api/github/status");
      if (statusRes.ok) {
        const sData: GitHubStatus = await statusRes.json();
        setStatus(sData);

        if (sData.is_connected) {
          const repoRes = await fetch(`/api/github/repos?visibility=${visibility}&per_page=50`);
          if (repoRes.ok) {
            const rData = await repoRes.json();
            setRepos(rData || []);
          }
        }
      }
    } catch (e) {
      console.error("Error fetching GitHub status:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatusAndRepos();
  }, [visibility]);

  const handleConnectGitHub = async () => {
    try {
      const res = await fetch("/api/github/url");
      if (res.ok) {
        const data = await res.json();
        if (data.authorization_url) {
          window.location.href = data.authorization_url;
        }
      }
    } catch (e) {
      console.error("Failed to initiate GitHub OAuth:", e);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect your GitHub account?")) return;
    try {
      await fetch("/api/github/disconnect", { method: "POST" });
      setStatus({ is_connected: false });
      setRepos([]);
    } catch (e) {
      console.error("Failed to disconnect GitHub:", e);
    }
  };

  const filteredRepos = repos.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      (r.description && r.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-[#0A0A0C] text-white">
      {/* Header */}
      <div className="border-b border-[#1E1E24] bg-[#0E0E12]/80 backdrop-blur-md px-6 py-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-neutral-800 border border-neutral-700 flex items-center justify-center text-white">
              <Github className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                GitHub Integration
                {status?.is_connected ? (
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                    Connected
                  </span>
                ) : (
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-neutral-800 text-neutral-400 font-mono">
                    Not Connected
                  </span>
                )}
              </h1>
              <p className="text-sm text-neutral-400">
                Connect your GitHub account to analyze authorized repositories with AI
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchStatusAndRepos}
              className="px-3.5 py-2 rounded-lg bg-[#18181F] hover:bg-[#22222B] border border-[#2B2B36] text-neutral-300 text-sm flex items-center gap-2 transition"
            >
              <RotateCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            {status?.is_connected ? (
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 font-semibold text-sm flex items-center gap-2 transition"
              >
                <Unplug className="w-4 h-4" />
                Disconnect GitHub
              </button>
            ) : (
              <button
                onClick={handleConnectGitHub}
                className="px-4 py-2 rounded-lg bg-white hover:bg-neutral-200 text-black font-semibold text-sm flex items-center gap-2 transition shadow-lg shadow-white/10"
              >
                <Github className="w-4 h-4" />
                Connect GitHub
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Connected Profile Card */}
        {status?.is_connected ? (
          <div className="p-6 rounded-2xl bg-[#121217] border border-[#22222B] flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              {status.avatar_url ? (
                <img
                  src={status.avatar_url}
                  alt={status.github_username}
                  className="w-16 h-16 rounded-full border border-neutral-700"
                />
              ) : (
                <div className="w-16 h-16 rounded-full bg-neutral-800 flex items-center justify-center text-white">
                  <Github className="w-8 h-8" />
                </div>
              )}
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  {status.github_username}
                  <a
                    href={`https://github.com/${status.github_username}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-neutral-500 hover:text-white"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </h2>
                {status.github_email && (
                  <p className="text-xs text-neutral-400 mt-0.5">{status.github_email}</p>
                )}
                <div className="mt-2 text-xs text-neutral-500 font-mono flex items-center gap-4">
                  <span>Connected: {new Date(status.connected_at || "").toLocaleDateString()}</span>
                  <span>Tokens: AES-CBC Fernet Encrypted</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <a
                href="/chat"
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-400 text-black flex items-center gap-2 transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Analyze in Chat
              </a>
            </div>
          </div>
        ) : (
          <div className="p-8 rounded-2xl bg-gradient-to-br from-[#121217] to-[#181822] border border-[#242432] text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-neutral-800 border border-neutral-700 flex items-center justify-center text-white mx-auto">
              <Github className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Connect GitHub to Illusion AI</h2>
              <p className="text-sm text-neutral-400 max-w-xl mx-auto mt-2">
                Authorize Illusion AI to securely access your repositories for AI-powered code analysis, commit explanations, and architecture reviews.
              </p>
            </div>
            <button
              onClick={handleConnectGitHub}
              className="px-6 py-2.5 rounded-xl bg-white hover:bg-neutral-200 text-black font-semibold text-sm inline-flex items-center gap-2 transition shadow-xl shadow-white/10"
            >
              <Github className="w-4 h-4" />
              Connect with GitHub OAuth 2.0
            </button>
          </div>
        )}

        {/* Repository Listing */}
        {status?.is_connected && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <h3 className="font-bold text-white text-lg flex items-center gap-2">
                <Code2 className="w-5 h-5 text-amber-400" />
                Authorized Repositories ({filteredRepos.length})
              </h3>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-64">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-neutral-500" />
                  <input
                    type="text"
                    placeholder="Search repositories..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-[#121217] border border-[#22222B] rounded-xl text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-amber-400"
                  />
                </div>

                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="bg-[#121217] border border-[#22222B] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                >
                  <option value="all">All</option>
                  <option value="public">Public</option>
                  <option value="private">Private</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredRepos.map((repo) => (
                <div
                  key={repo.full_name}
                  className="p-5 rounded-xl bg-[#121217] border border-[#22222B] flex flex-col justify-between hover:border-[#333342] transition"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <a
                        href={repo.html_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-bold text-white text-sm hover:text-amber-400 flex items-center gap-1.5 transition"
                      >
                        {repo.name}
                        <ExternalLink className="w-3.5 h-3.5 text-neutral-500" />
                      </a>
                      <span className="text-[11px] px-2 py-0.5 rounded font-mono bg-[#1B1B24] text-neutral-400 flex items-center gap-1">
                        {repo.private ? <Lock className="w-3 h-3 text-amber-400" /> : <Globe className="w-3 h-3 text-neutral-400" />}
                        {repo.private ? "Private" : "Public"}
                      </span>
                    </div>
                    <p className="text-xs text-neutral-400 mt-2 line-clamp-2">
                      {repo.description || "No repository description provided."}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-[#1C1C24] flex items-center justify-between text-xs text-neutral-500 font-mono">
                    <div className="flex items-center gap-3">
                      {repo.language && (
                        <span className="flex items-center gap-1 text-neutral-300">
                          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                          {repo.language}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Star className="w-3.5 h-3.5 text-neutral-400" />
                        {repo.stars}
                      </span>
                    </div>

                    <a
                      href={`/chat?prompt=Analyze repository ${repo.full_name}`}
                      className="text-amber-400 hover:text-amber-300 flex items-center gap-1 font-semibold text-xs"
                    >
                      AI Analyze
                      <ArrowRight className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function GitHubPage() {
  return <GitHubPageContent />;
}
