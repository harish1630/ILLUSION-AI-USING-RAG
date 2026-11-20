"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { api, ToolDefinition } from "@/lib/api";
import {
  Calculator,
  FileText,
  Search,
  Database,
  ArrowRight,
  Upload,
  Copy,
  Check,
  RefreshCw,
  Sparkles,
  ExternalLink,
  ShieldAlert,
  FileCheck2,
  Trash2,
  Equal,
  Percent,
  Plus,
  Minus,
  X as Multiply,
  Divide,
  CornerDownLeft,
} from "lucide-react";

export default function ToolsPage() {
  const { language } = useLanguage();
  const isTamil = language === "ta";

  // Active Tool Selector: "calc" | "reader" | "web" | "rag"
  const [activeTool, setActiveTool] = useState<"calc" | "reader" | "web" | "rag">("calc");
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  // 1. Calculator GUI State
  const [calcInput, setCalcInput] = useState<string>("2500000 * 0.25");
  const [calcDisplayResult, setCalcDisplayResult] = useState<string>("625,000");
  const [calcHistory, setCalcHistory] = useState<Array<{ expr: string; res: string }>>([
    { expr: "2500000 * 0.25", res: "625,000" },
    { expr: "1500000 - 375000", res: "1,125,000" },
  ]);
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcError, setCalcError] = useState<string | null>(null);

  // 2. File Reader GUI State
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [extractedData, setExtractedData] = useState<{
    fileName: string;
    format: string;
    sizeKb: number;
    charCount: number;
    text: string;
  } | null>(null);
  const [readerLoading, setReaderLoading] = useState(false);
  const [readerError, setReaderError] = useState<string | null>(null);

  // 3. Web Search GUI State
  const [webQuery, setWebQuery] = useState("Tamil Nadu NEEDS scheme 2026 subsidy limit");
  const [webResults, setWebResults] = useState<{
    answer?: string;
    results: Array<{ title: string; url: string; content: string; score?: number }>;
  } | null>(null);
  const [webLoading, setWebLoading] = useState(false);
  const [webError, setWebError] = useState<string | null>(null);

  // 4. RAG Vector Search GUI State
  const [ragQuery, setRagQuery] = useState("NEEDS subsidy eligibility criteria first generation");
  const [ragResults, setRagResults] = useState<Array<{
    title: string;
    url: string;
    content: string;
    category?: string;
  }> | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // --- Calculator Engine ---
  const handleCalculate = async (customExpr?: string) => {
    const expr = customExpr || calcInput;
    if (!expr.trim()) return;
    setCalcLoading(true);
    setCalcError(null);
    try {
      const res = await api.executeToolDirect("calculator", { expression: expr });
      if (res && res.success && res.data) {
        const out = String(res.data.formatted || res.data.result);
        setCalcDisplayResult(out);
        setCalcHistory((prev) => [{ expr, res: out }, ...prev.slice(0, 5)]);
      } else {
        setCalcError(res?.error || "Evaluation failed");
      }
    } catch (err: any) {
      setCalcError(err.message || "Failed to calculate");
    } finally {
      setCalcLoading(false);
    }
  };

  // --- Document Reader Engine ---
  const handleFileUpload = async (file: File) => {
    setUploadedFile(file);
    setReaderLoading(true);
    setReaderError(null);
    setExtractedData(null);
    try {
      const res = await api.uploadToolDocument(file);
      if (res && res.data) {
        setExtractedData({
          fileName: res.file_name,
          format: res.format,
          sizeKb: Math.round(res.size_bytes / 1024),
          charCount: res.data.total_characters || res.data.content?.length || 0,
          text: res.data.content,
        });
      }
    } catch (err: any) {
      setReaderError(err.message || "Failed to extract text from file");
    } finally {
      setReaderLoading(false);
    }
  };

  // --- Web Search Engine ---
  const handleWebSearch = async () => {
    if (!webQuery.trim()) return;
    setWebLoading(true);
    setWebError(null);
    setWebResults(null);
    try {
      const res = await api.executeToolDirect("web_search", {
        query: webQuery,
        max_results: 4,
      });
      if (res && res.success && res.data) {
        setWebResults({
          answer: res.data.answer,
          results: res.data.results || [],
        });
      } else {
        setWebError(res?.error || "No web search results returned");
      }
    } catch (err: any) {
      setWebError(err.message || "Web search error");
    } finally {
      setWebLoading(false);
    }
  };

  // --- RAG Knowledge Engine ---
  const handleRagSearch = async () => {
    if (!ragQuery.trim()) return;
    setRagLoading(true);
    setRagError(null);
    setRagResults(null);
    try {
      const res = await api.executeToolDirect("rag_search", {
        query: ragQuery,
        limit: 4,
      });
      if (res && res.success && res.data) {
        setRagResults(res.data.chunks || []);
      } else {
        setRagError(res?.error || "No knowledge chunks retrieved");
      }
    } catch (err: any) {
      setRagError(err.message || "RAG search error");
    } finally {
      setRagLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0D0D0E] text-[#EDEDED] py-8 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#24242A] gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-[11px] font-mono tracking-widest text-amber-400 uppercase">
                AI Tool Deck & Quick Sandbox
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-0.5 tracking-tight">
              Tools <span className="text-amber-400">Console</span>
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black text-xs font-bold transition-all shadow-sm"
            >
              <span>Use in AI Chat</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* 4 Tool Cards / Tabs Switcher */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            {
              id: "calc",
              title: "Calculator",
              desc: "Safe AST Math & Subsidies",
              icon: <Calculator className="w-5 h-5" />,
              badge: "AST Engine",
            },
            {
              id: "reader",
              title: "File Extractor",
              desc: "PDF / DOCX / TXT Parser",
              icon: <FileText className="w-5 h-5" />,
              badge: "Up to 15MB",
            },
            {
              id: "web",
              title: "Web Search",
              desc: "Tavily Live Government Portals",
              icon: <Search className="w-5 h-5" />,
              badge: "Live Web",
            },
            {
              id: "rag",
              title: "RAG Retrieval",
              desc: "TN Verified Scheme Gazettes",
              icon: <Database className="w-5 h-5" />,
              badge: "Supabase + Gemini",
            },
          ].map((item) => {
            const isActive = activeTool === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTool(item.id as any)}
                className={`p-3.5 rounded-xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                  isActive
                    ? "bg-[#18181C] border-amber-500 shadow-md ring-1 ring-amber-500/30"
                    : "bg-[#131316] border-[#24242A] hover:bg-[#18181C] hover:border-[#383842]"
                }`}
              >
                {isActive && (
                  <div className="absolute top-0 right-0 w-8 h-8 bg-amber-500/10 rounded-bl-xl flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  </div>
                )}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        isActive
                          ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                          : "bg-[#1A1A20] text-zinc-400 border border-[#2E2E36]"
                      }`}
                    >
                      {item.icon}
                    </div>
                    <span className="text-[10px] font-mono text-zinc-400 px-1.5 py-0.5 rounded bg-[#101014] border border-[#26262E]">
                      {item.badge}
                    </span>
                  </div>
                  <h2 className={`text-xs font-bold ${isActive ? "text-white" : "text-zinc-300"}`}>
                    {item.title}
                  </h2>
                  <p className="text-[11px] text-zinc-400 mt-0.5 leading-snug line-clamp-1">
                    {item.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>

        {/* MAIN INTERACTIVE WORKSPACE */}
        <div className="bg-[#141417] border border-[#26262E] rounded-2xl p-5 sm:p-6 shadow-xl">
          {/* ======================================================== */}
          {/* TOOL 1: CALCULATOR GUI */}
          {/* ======================================================== */}
          {activeTool === "calc" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-[#222228]">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Calculator className="w-4 h-4 text-amber-400" />
                    <span>Safe Math & Financial Formula Calculator</span>
                  </h3>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Evaluates exact capital subsidies, working capital, EMI & percentages using Python AST (zero eval).
                  </p>
                </div>
                <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded">
                  AST Protected
                </span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left: Input & Keypad / Presets */}
                <div className="lg:col-span-7 space-y-4">
                  <div className="bg-[#0E0E10] border border-[#26262E] rounded-xl p-3 focus-within:border-amber-500 transition-colors">
                    <span className="text-[10px] font-mono text-zinc-400 block mb-1 uppercase tracking-wider">
                      Expression Input
                    </span>
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={calcInput}
                        onChange={(e) => setCalcInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleCalculate()}
                        placeholder="e.g. 2500000 * 0.25"
                        className="w-full bg-transparent text-sm sm:text-base font-mono text-white placeholder-zinc-500 outline-none"
                      />
                      {calcInput && (
                        <button
                          onClick={() => setCalcInput("")}
                          className="text-zinc-400 hover:text-zinc-200 text-xs px-1.5 py-0.5"
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Calculator Operator Bar */}
                  <div className="grid grid-cols-6 gap-1.5 font-mono text-xs">
                    {[
                      { label: "+", val: " + " },
                      { label: "-", val: " - " },
                      { label: "×", val: " * " },
                      { label: "÷", val: " / " },
                      { label: "(", val: "(" },
                      { label: ")", val: ")" },
                      { label: "25%", val: " * 0.25" },
                      { label: "35%", val: " * 0.35" },
                      { label: "sqrt", val: "sqrt(" },
                      { label: "pow", val: " ** 2" },
                      { label: "10L", val: "1000000" },
                      { label: "50L", val: "5000000" },
                    ].map((btn) => (
                      <button
                        key={btn.label}
                        onClick={() => setCalcInput((prev) => prev + btn.val)}
                        className="py-2 rounded-lg bg-[#19191E] hover:bg-[#22222A] border border-[#2A2A33] text-zinc-300 hover:text-white font-medium transition-all"
                      >
                        {btn.label}
                      </button>
                    ))}
                  </div>

                  {/* Scheme Presets */}
                  <div>
                    <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block mb-2">
                      Instant Government Subsidy Presets
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {[
                        { label: "NEEDS 25% on ₹30 Lakhs", expr: "3000000 * 0.25" },
                        { label: "NEEDS Max Cap (₹75L project)", expr: "7500000 * 0.25" },
                        { label: "UYEGP 25% on ₹15L Manufacturing", expr: "1500000 * 0.25" },
                        { label: "PMEGP 35% Special Rural on ₹20L", expr: "2000000 * 0.35" },
                      ].map((item) => (
                        <button
                          key={item.label}
                          onClick={() => {
                            setCalcInput(item.expr);
                            handleCalculate(item.expr);
                          }}
                          className="p-2.5 rounded-lg bg-[#111114] hover:bg-[#18181D] border border-[#222228] hover:border-amber-500/40 text-left transition-all group flex items-center justify-between"
                        >
                          <div>
                            <div className="text-xs font-semibold text-zinc-200 group-hover:text-amber-400">
                              {item.label}
                            </div>
                            <div className="text-[10px] font-mono text-zinc-400">{item.expr}</div>
                          </div>
                          <CornerDownLeft className="w-3.5 h-3.5 text-zinc-500 group-hover:text-amber-400" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => handleCalculate()}
                    disabled={calcLoading || !calcInput.trim()}
                    className="w-full py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-bold text-xs uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-md"
                  >
                    {calcLoading ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Calculating AST...</span>
                      </>
                    ) : (
                      <>
                        <Equal className="w-4 h-4" />
                        <span>Compute Exact Result</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Right: Crisp Clear Result Card */}
                <div className="lg:col-span-5 bg-[#0D0D0E] border border-[#24242A] rounded-xl p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-[#1E1E24]">
                      <span className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider">
                        Crisp Evaluation
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        AST Verified
                      </span>
                    </div>

                    {calcError ? (
                      <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 shrink-0" />
                        <span>{calcError}</span>
                      </div>
                    ) : (
                      <div className="mt-4">
                        <span className="text-xs font-mono text-zinc-400 block mb-1">
                          Expression: {calcInput}
                        </span>
                        <div className="text-3xl sm:text-4xl font-extrabold font-mono text-amber-400 tracking-tight flex items-baseline justify-between">
                          <span>₹ {calcDisplayResult}</span>
                          <button
                            onClick={() => copyToClipboard(calcDisplayResult, "calc-res")}
                            className="text-zinc-400 hover:text-white p-1 rounded hover:bg-[#1E1E24] transition-all"
                            title="Copy result"
                          >
                            {copiedIndex === "calc-res" ? (
                              <Check className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        <p className="text-[11px] text-zinc-400 mt-2">
                          Evaluated without arbitrary code execution risk. Safe for government and audit figures.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* History */}
                  <div className="mt-6 pt-4 border-t border-[#1E1E24]">
                    <span className="text-[10px] font-mono text-zinc-400 block mb-2 uppercase tracking-wider">
                      Recent Evaluations
                    </span>
                    <div className="space-y-1.5">
                      {calcHistory.map((item, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            setCalcInput(item.expr);
                            setCalcDisplayResult(item.res);
                          }}
                          className="flex items-center justify-between text-xs font-mono p-1.5 rounded hover:bg-[#18181D] cursor-pointer text-zinc-400 hover:text-zinc-200"
                        >
                          <span className="truncate max-w-[160px]">{item.expr}</span>
                          <span className="text-amber-400 font-semibold">= {item.res}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TOOL 2: DOCUMENT EXTRACTOR GUI */}
          {/* ======================================================== */}
          {activeTool === "reader" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-[#222228]">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <FileText className="w-4 h-4 text-amber-400" />
                    <span>Business Document & PDF/DOCX Text Extractor</span>
                  </h3>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Extract text from Detailed Project Reports (DPR), quotation sheets, and government application PDFs.
                  </p>
                </div>
                <span className="text-[10px] font-mono bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded border border-zinc-700">
                  Max 15MB
                </span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Upload Target */}
                <div className="lg:col-span-5 space-y-4">
                  <div className="border-2 border-dashed border-[#2E2E36] hover:border-amber-500/50 rounded-xl p-6 text-center bg-[#0F0F12] transition-all">
                    <Upload className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                    <label className="text-xs font-bold text-white block cursor-pointer">
                      <span>Click to Select Document</span>
                      <input
                        type="file"
                        accept=".pdf,.docx,.txt"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleFileUpload(file);
                        }}
                        className="hidden"
                      />
                    </label>
                    <p className="text-[11px] text-zinc-400 mt-1">
                      Supports PDF, Word DOCX, and Plain TXT
                    </p>

                    {uploadedFile && (
                      <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded bg-[#18181D] border border-[#2E2E36] text-xs font-mono text-zinc-200">
                        <FileCheck2 className="w-3.5 h-3.5 text-amber-400" />
                        <span>{uploadedFile.name}</span>
                      </div>
                    )}
                  </div>

                  {readerError && (
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 shrink-0" />
                      <span>{readerError}</span>
                    </div>
                  )}

                  {/* Sample Document Buttons */}
                  <div>
                    <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block mb-2">
                      Try Sample Document Test
                    </span>
                    <button
                      onClick={() => {
                        const blob = new Blob(
                          [
                            "TAMIL NADU MSME SCHEME APPLICATION\nApplicant: First Generation Entrepreneur\nLocation: Coimbatore District\nActivity: Food Processing Unit\nEstimated Cost: Rs. 25,00,000\nSubsidy Claimed: NEEDS 25% Capital Subsidy\nRequired Attachments: DPR, Quotations, Degree Certificate.",
                          ],
                          { type: "text/plain" }
                        );
                        const file = new File([blob], "sample_business_proposal.txt", {
                          type: "text/plain",
                        });
                        handleFileUpload(file);
                      }}
                      className="w-full py-2 px-3 rounded-lg bg-[#141418] hover:bg-[#1B1B22] border border-[#26262E] text-left text-xs text-zinc-300 hover:text-white transition-all flex items-center justify-between"
                    >
                      <span>Load Sample Proposal (sample_business_proposal.txt)</span>
                      <span className="text-[10px] font-mono text-amber-400">Load</span>
                    </button>
                  </div>
                </div>

                {/* Right: Crisp Extracted Text Area */}
                <div className="lg:col-span-7 bg-[#0E0E10] border border-[#24242A] rounded-xl p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-[#1E1E24]">
                      <span className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider">
                        Extracted Content Output
                      </span>
                      {extractedData && (
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-mono text-zinc-400">
                            {extractedData.charCount} characters | {extractedData.sizeKb} KB
                          </span>
                          <button
                            onClick={() => copyToClipboard(extractedData.text, "doc-copy")}
                            className="flex items-center gap-1 text-[11px] text-amber-400 hover:text-amber-300"
                          >
                            {copiedIndex === "doc-copy" ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                            <span>Copy Text</span>
                          </button>
                        </div>
                      )}
                    </div>

                    {readerLoading ? (
                      <div className="py-16 text-center text-xs text-zinc-400 font-mono flex flex-col items-center gap-2">
                        <RefreshCw className="w-5 h-5 text-amber-400 animate-spin" />
                        <span>Parsing and extracting text with PyMuPDF / python-docx...</span>
                      </div>
                    ) : extractedData ? (
                      <div className="mt-3">
                        <div className="text-xs font-mono text-amber-400 mb-2">
                          Extracted from: {extractedData.fileName} (Format: {extractedData.format.toUpperCase()})
                        </div>
                        <pre className="text-xs font-mono text-zinc-200 leading-relaxed whitespace-pre-wrap bg-[#141418] p-3.5 rounded-lg border border-[#26262E] max-h-72 overflow-y-auto">
                          {extractedData.text}
                        </pre>
                      </div>
                    ) : (
                      <div className="py-16 text-center text-xs text-zinc-400 font-mono">
                        Select a document from the left to extract clean text.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TOOL 3: TAVILY WEB SEARCH GUI */}
          {/* ======================================================== */}
          {activeTool === "web" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-[#222228]">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Search className="w-4 h-4 text-amber-400" />
                    <span>Real-Time Government Portal Web Search (Tavily Engine)</span>
                  </h3>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Live web querying across msmeonline.tn.gov.in, myscheme.gov.in, and official circulars.
                  </p>
                </div>
                <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded">
                  Live Search
                </span>
              </div>

              {/* Search Bar */}
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={webQuery}
                  onChange={(e) => setWebQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleWebSearch()}
                  placeholder="Enter search query..."
                  className="flex-1 bg-[#0E0E10] border border-[#2A2A33] focus:border-amber-500 rounded-lg px-4 py-2.5 text-xs sm:text-sm text-white placeholder-zinc-500 outline-none"
                />
                <button
                  onClick={handleWebSearch}
                  disabled={webLoading || !webQuery.trim()}
                  className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shrink-0 flex items-center justify-center gap-1.5"
                >
                  {webLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Searching...</span>
                    </>
                  ) : (
                    <span>Search Web</span>
                  )}
                </button>
              </div>

              {/* Query Quick Picks */}
              <div className="flex flex-wrap gap-1.5 items-center">
                <span className="text-[10px] font-mono text-zinc-400 mr-1 uppercase">Try queries:</span>
                {[
                  "Tamil Nadu NEEDS scheme 2026 guidelines",
                  "Udyam registration zero cost portal",
                  "PMEGP subsidy limits manufacturing",
                  "StartupTN seed grant application window",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => {
                      setWebQuery(q);
                      handleWebSearch();
                    }}
                    className="px-2.5 py-1 rounded bg-[#16161B] hover:bg-[#202028] border border-[#26262E] text-[11px] text-zinc-300 hover:text-white transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Output Results */}
              {webResults && (
                <div className="space-y-4 pt-2">
                  {/* Clean AI Answer Summary */}
                  {webResults.answer && (
                    <div className="p-4 rounded-xl bg-[#0E0E10] border border-[#26262E]">
                      <span className="text-[10px] font-mono uppercase text-amber-400 font-bold block mb-1">
                        Synthesized Executive Summary
                      </span>
                      <p className="text-xs sm:text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">
                        {webResults.answer}
                      </p>
                    </div>
                  )}

                  {/* Crisp Results List */}
                  <div>
                    <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block mb-2.5">
                      Web Sources Retrieved ({webResults.results.length})
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {webResults.results.map((item, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-[#101014] border border-[#24242A] hover:border-amber-500/40 transition-all flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between gap-2">
                              <h4 className="text-xs font-bold text-white line-clamp-1">{item.title}</h4>
                              <a
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-amber-400 hover:text-amber-300 shrink-0"
                              >
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            </div>
                            <p className="text-[11px] text-zinc-400 mt-1 line-clamp-3 leading-relaxed">
                              {item.content}
                            </p>
                          </div>
                          <div className="mt-3 pt-2 border-t border-[#1E1E24] flex items-center justify-between text-[10px] font-mono text-zinc-400">
                            <span className="truncate max-w-[200px]">{item.url}</span>
                            <span className="text-emerald-400 font-semibold">Live URL</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TOOL 4: RAG VECTOR SEARCH GUI */}
          {/* ======================================================== */}
          {activeTool === "rag" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-[#222228]">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Database className="w-4 h-4 text-amber-400" />
                    <span>RAG Verified Scheme Knowledge Search (Gemini + Supabase pgvector)</span>
                  </h3>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Retrieves authentic government scheme chunks with source metadata, exclusions, and rules.
                  </p>
                </div>
                <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded">
                  Vector Grounded
                </span>
              </div>

              {/* Search Bar */}
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={ragQuery}
                  onChange={(e) => setRagQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleRagSearch()}
                  placeholder="Enter scheme criteria query (e.g. NEEDS 25% subsidy first gen)..."
                  className="flex-1 bg-[#0E0E10] border border-[#2A2A33] focus:border-amber-500 rounded-lg px-4 py-2.5 text-xs sm:text-sm text-white placeholder-zinc-500 outline-none"
                />
                <button
                  onClick={handleRagSearch}
                  disabled={ragLoading || !ragQuery.trim()}
                  className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shrink-0 flex items-center justify-center gap-1.5"
                >
                  {ragLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Retrieving Chunks...</span>
                    </>
                  ) : (
                    <span>Query Vectors</span>
                  )}
                </button>
              </div>

              {/* RAG Results Display */}
              {ragResults && (
                <div>
                  <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block mb-2.5">
                    Verified Chunks Retrieved ({ragResults.length})
                  </span>
                  <div className="space-y-3">
                    {ragResults.map((chunk, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-[#0E0E10] border border-[#26262E] hover:border-amber-500/30 transition-all"
                      >
                        <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#1E1E24]">
                          <span className="text-xs font-bold text-white">{chunk.title}</span>
                          {chunk.url && (
                            <a
                              href={chunk.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] text-amber-400 hover:underline flex items-center gap-1 font-mono"
                            >
                              <span>Official Portal</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                        <p className="text-xs text-zinc-300 leading-relaxed font-normal">
                          {chunk.content}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
