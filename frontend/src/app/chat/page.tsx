"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { api, ChatResponse, ChatSource, ExecutedTool } from "@/lib/api";
import AuthGuard from "@/components/AuthGuard";
import {
  Send,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  ExternalLink,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  RotateCcw,
  Wrench,
  Calculator,
  Search,
  Database,
  FileText,
  Sliders,
  Check,
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  sources?: ChatSource[];
  matched_schemes?: any[];
  follow_up_questions?: string[];
  disclaimer?: string;
  executed_tools?: ExecutedTool[];
  tool_mode_used?: string;
  timestamp: string;
}

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q");

  const { language, setLanguage, t } = useLanguage();
  const isTamil = language === "ta";

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Hybrid Tool Calling UI State
  const [toolMode, setToolMode] = useState<"auto" | "manual" | "hybrid">("auto");
  const [selectedTools, setSelectedTools] = useState<string[]>(["calculator", "rag_search"]);
  const [showToolSettings, setShowToolSettings] = useState(false);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "assistant",
      text: isTamil
        ? "வணக்கம்! நான் illusion AI இன் அதிகாரப்பூர்வ தொழில் வழிகாட்டி ஆலோசகர். தமிழ்நாடு மற்றும் மத்திய அரசு தொழில் திட்டங்கள், மானியங்கள் (NEEDS, UYEGP, PMEGP), உத்யாம் பதிவு, மற்றும் துல்லியமான முதலீட்டு கணக்கீடுகளை (Hybrid Tools) தமிழில் அல்லது ஆங்கிலத்தில் கேட்கலாம்."
        : "Hello! I am your AI Startup & Government Scheme Advisor. Ask me anything about launching your business in Tamil Nadu, finding relevant subsidies (NEEDS, UYEGP, PMEGP), obtaining free Udyam registration, calculating exact subsidies with our AST math engine, or retrieving real-time web portal updates.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (initialQuery && messages.length === 1) {
      handleSend(initialQuery);
    }
  }, [initialQuery]);

  const toggleTool = (toolName: string) => {
    setSelectedTools((prev) =>
      prev.includes(toolName) ? prev.filter((t) => t !== toolName) : [...prev, toolName]
    );
  };

  const handleSend = async (userText?: string) => {
    const textToSend = userText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const savedProfile = localStorage.getItem("current_profile");
      const profileObj = savedProfile ? JSON.parse(savedProfile) : undefined;

      const res: ChatResponse = await api.sendChatMessage(
        textToSend,
        language,
        profileObj,
        toolMode,
        toolMode !== "auto" ? selectedTools : undefined
      );

      const assistantMsg: Message = {
        id: `asst-${Date.now()}`,
        sender: "assistant",
        text: res.answer,
        sources: res.sources,
        matched_schemes: res.matched_schemes,
        follow_up_questions: res.follow_up_questions,
        disclaimer: res.disclaimer,
        executed_tools: res.executed_tools,
        tool_mode_used: res.tool_mode_used,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text: isTamil
            ? "மன்னிக்கவும், தகவலைப் பெறுவதில் சிக்கல் ஏற்பட்டது. தயவுசெய்து backend சர்வர் இயங்குகிறதா என்பதை சரிபார்க்கவும்."
            : "Sorry, I encountered an error connecting to the backend service. Please ensure the server is running.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleSuggestions = isTamil
    ? [
        "ரூ. 30 லட்சத்திற்கு NEEDS மானியத்தை கணக்கிடுங்கள் (25%)",
        "நான் கோயம்புத்தூரில் ₹3 லட்சத்தில் தொழில் தொடங்க என்ன திட்டங்கள் உள்ளன?",
        "எனது GitHub களஞ்சியங்களை காட்டு (Show my GitHub repos)",
        "NEEDS திட்டத்தில் அதிகபட்ச மானியம் எவ்வளவு?",
        "உத்யாம் பதிவு செய்ய கட்டணம் உண்டா?",
      ]
    : [
        "Show my GitHub repositories",
        "Explain the latest commit in my repository",
        "Get project info from custom MCP server",
        "Calculate 25% capital subsidy for ₹40 Lakhs project cost under NEEDS scheme",
        "How do I get free official Udyam registration?",
      ];

  return (
    <div className="min-h-screen bg-[#0D0D0E] text-[#EDEDED] flex flex-col">
      {/* Top Banner */}
      <div className="bg-[#151518] border-b border-[#24242A] py-3 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#18181C] border border-[#2E2E36] flex items-center justify-center text-amber-400 shadow-sm">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                <span>{isTamil ? "இருமொழி AI ஆலோசகர்" : "Bilingual AI Startup Advisor"}</span>
                <span className="text-[10px] font-semibold bg-amber-500/10 text-amber-300 px-2 py-0.5 rounded-full border border-amber-500/30">
                  Hybrid Tools Active
                </span>
              </h1>
              <p className="text-[10px] text-zinc-400">
                {isTamil ? "தமிழ்நாடு & மத்திய அரசு திட்ட தகவல் மையம்" : "Tamil Nadu & Central MSME Scheme Intelligence"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Tool Mode Selector Pill */}
            <button
              onClick={() => setShowToolSettings(!showToolSettings)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] font-medium transition-colors ${
                showToolSettings
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                  : "bg-[#1C1C20] text-zinc-300 border-[#2E2E36] hover:text-white"
              }`}
            >
              <Sliders className="w-3 h-3 text-amber-400" />
              <span className="capitalize">{toolMode} Mode</span>
            </button>

            <button
              onClick={() => setLanguage(language === "en" ? "ta" : "en")}
              className="px-2.5 py-1 rounded-md border border-[#2E2E36] bg-[#1C1C20] text-zinc-300 hover:text-white text-[11px] font-semibold"
            >
              {language === "en" ? "தமிழ்" : "English"}
            </button>
          </div>
        </div>

        {/* Expandable Hybrid Tool Settings */}
        {showToolSettings && (
          <div className="max-w-4xl mx-auto mt-3 pt-3 border-t border-[#24242A] text-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-zinc-300">Tool Selection Routing Mode:</span>
              <div className="flex gap-1.5">
                {(["auto", "manual", "hybrid"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setToolMode(mode)}
                    className={`px-2.5 py-1 rounded text-[11px] font-medium capitalize transition-all ${
                      toolMode === mode
                        ? "bg-amber-500 text-black font-semibold"
                        : "bg-[#1C1C20] text-zinc-400 hover:text-white border border-[#2E2E36]"
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            {toolMode !== "auto" && (
              <div className="flex items-center gap-2 pt-1 flex-wrap">
                <span className="text-[11px] text-zinc-400">Selected Tools:</span>
                {[
                  { id: "calculator", label: "Calculator (AST)" },
                  { id: "rag_search", label: "RAG Vector Search" },
                  { id: "web_search", label: "Tavily Web Search" },
                  { id: "file_reader", label: "File Reader" },
                  { id: "gmail_search_emails", label: "Gmail Search" },
                  { id: "github_list_repositories", label: "GitHub Repos" },
                ].map((t) => {
                  const active = selectedTools.includes(t.id);
                  return (
                    <button
                      key={t.id}
                      onClick={() => toggleTool(t.id)}
                      className={`px-2 py-0.5 rounded text-[11px] flex items-center gap-1 border transition-all ${
                        active
                          ? "bg-amber-500/15 border-amber-500/40 text-amber-300"
                          : "bg-[#1C1C20] border-[#2E2E36] text-zinc-500 hover:text-zinc-300"
                      }`}
                    >
                      {active && <Check className="w-2.5 h-2.5 text-amber-400" />}
                      <span>{t.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 overflow-y-auto space-y-5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.sender === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-[#18181C] border border-[#2E2E36] text-amber-400 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                <Sparkles className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-[85%] sm:max-w-[78%] rounded-xl p-4 sm:p-5 text-xs sm:text-sm leading-relaxed shadow-md ${
                msg.sender === "user"
                  ? "bg-amber-500 text-black font-medium rounded-tr-none"
                  : "bg-[#151518] text-zinc-200 border border-[#2E2E36] rounded-tl-none"
              }`}
            >
              {/* Tool Execution Badge */}
              {msg.executed_tools && msg.executed_tools.length > 0 && (
                <div className="mb-3 pb-2.5 border-b border-[#24242A] flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider flex items-center gap-1 mr-1">
                    <Wrench className="w-3 h-3 text-amber-400" />
                    <span>Tools Executed:</span>
                  </span>
                  {msg.executed_tools.map((et, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-[#1C1C20] border border-[#2E2E36] text-amber-300"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>{et.tool_name}</span>
                    </span>
                  ))}
                </div>
              )}

              {/* Message text */}
              <div className="whitespace-pre-wrap font-normal leading-relaxed">{msg.text}</div>

              {/* Citations & Verified Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[#24242A]">
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-zinc-400 uppercase tracking-wider mb-2">
                    <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                    <span>{isTamil ? "சரிபார்க்கப்பட்ட அரசு ஆதாரங்கள்:" : "Verified Source Citations:"}</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((src, i) => (
                      <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#1C1C20] hover:bg-[#24242A] border border-[#2E2E36] text-zinc-300 text-[11px] font-medium transition-colors"
                      >
                        <span className="truncate max-w-[200px]">{src.title}</span>
                        <ExternalLink className="w-3 h-3 text-zinc-500" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Follow-up question chips */}
              {msg.follow_up_questions && msg.follow_up_questions.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[#24242A] flex flex-wrap gap-1.5">
                  {msg.follow_up_questions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(q)}
                      className="text-[11px] text-left bg-[#1C1C20] hover:bg-amber-500/10 hover:text-amber-300 border border-[#2E2E36] hover:border-amber-500/30 rounded-md px-2.5 py-1 text-zinc-400 transition-colors"
                    >
                      {q} &rarr;
                    </button>
                  ))}
                </div>
              )}

              <span className="block text-[10px] text-zinc-500 mt-2 text-right">
                {msg.timestamp}
              </span>
            </div>

            {msg.sender === "user" && (
              <div className="w-8 h-8 rounded-lg bg-amber-500 text-black flex items-center justify-center shrink-0 mt-1 shadow-sm font-bold">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 items-center">
            <div className="w-8 h-8 rounded-lg bg-[#18181C] border border-[#2E2E36] text-amber-400 flex items-center justify-center shadow-sm">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-[#151518] border border-[#2E2E36] rounded-xl rounded-tl-none p-3.5 text-xs text-zinc-400 shadow-sm flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span>
                {isTamil
                  ? "AI கருவிகளை இயக்கி அதிகாரப்பூர்வ அரசு ஆவணங்களை தேடுகிறது..."
                  : "Dispatching hybrid tools & generating grounded response..."}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested prompts if few messages */}
      {messages.length <= 2 && (
        <div className="max-w-4xl w-full mx-auto px-4 sm:px-6 mb-3">
          <span className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider block mb-2">
            {isTamil ? "பரிந்துரைக்கப்பட்ட கேள்விகள் (கருவி சோதனை):" : "Suggested Tool Queries:"}
          </span>
          <div className="flex flex-wrap gap-2">
            {sampleSuggestions.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(s)}
                className="text-xs bg-[#151518] border border-[#2E2E36] hover:border-amber-500/40 hover:bg-[#1C1C20] rounded-lg px-3 py-1.5 text-zinc-300 font-medium transition-all text-left"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form Bar */}
      <div className="bg-[#151518] border-t border-[#24242A] p-4 sticky bottom-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="max-w-4xl mx-auto flex items-center gap-2.5"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isTamil
                ? "உங்கள் கேள்வியை தட்டச்சு செய்க (எ.கா: ரூ. 20 லட்சத்திற்கு 25% மானியத்தை கணக்கிடு)..."
                : "Ask any startup question or formula (e.g., Calculate 25% subsidy for 25L, or Tamil Nadu NEEDS rules)..."
            }
            className="flex-1 bg-[#1C1C20] border border-[#2E2E36] focus:border-amber-500 rounded-lg px-4 py-2.5 text-xs sm:text-sm text-white placeholder-zinc-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-amber-500 hover:bg-amber-400 text-black p-2.5 rounded-lg shadow-sm transition-all disabled:opacity-40 shrink-0"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <AuthGuard>
      <Suspense fallback={<div className="p-8 text-center text-xs text-zinc-500">Loading Chat...</div>}>
        <ChatContent />
      </Suspense>
    </AuthGuard>
  );
}
