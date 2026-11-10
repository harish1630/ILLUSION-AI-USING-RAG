"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { api, ChatResponse, ChatSource } from "@/lib/api";
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
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  sources?: ChatSource[];
  matched_schemes?: any[];
  follow_up_questions?: string[];
  disclaimer?: string;
  timestamp: string;
}

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q");

  const { language, setLanguage, t } = useLanguage();
  const isTamil = language === "ta";

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "assistant",
      text: isTamil
        ? "வணக்கம்! நான் illusion AI இன் அதிகாரப்பூர்வ தொழில் வழிகாட்டி ஆலோசகர். தமிழ்நாடு மற்றும் மத்திய அரசு தொழில் திட்டங்கள், மானியங்கள் (NEEDS, UYEGP, PMEGP) மற்றும் உத்யாம் பதிவு குறித்த உங்கள் சந்தேகங்களை தமிழில் அல்லது ஆங்கிலத்தில் கேட்கலாம்."
        : "Hello! I am your AI Startup & Government Scheme Advisor. Ask me anything about launching your business in Tamil Nadu, finding relevant subsidies (NEEDS, UYEGP, PMEGP), obtaining free Udyam registration, or estimating startup costs.",
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
        profileObj
      );

      const assistantMsg: Message = {
        id: `asst-${Date.now()}`,
        sender: "assistant",
        text: res.answer,
        sources: res.sources,
        matched_schemes: res.matched_schemes,
        follow_up_questions: res.follow_up_questions,
        disclaimer: res.disclaimer,
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
        "நான் கோயம்புத்தூரில் ₹3 லட்சத்தில் தொழில் தொடங்க என்ன திட்டங்கள் உள்ளன?",
        "NEEDS திட்டத்தில் அதிகபட்ச மானியம் எவ்வளவு?",
        "உத்யாம் பதிவு செய்ய கட்டணம் உண்டா?",
        "UYEGP திட்டத்திற்கு என்ன தகுதிகள் தேவை?",
      ]
    : [
        "I want to start a small manufacturing business in Coimbatore with ₹3 lakh. What should I do first?",
        "What is the maximum subsidy under Tamil Nadu NEEDS scheme?",
        "How do I get free official Udyam registration?",
        "What are the eligibility criteria for UYEGP scheme?",
      ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Banner */}
      <div className="bg-white border-b border-slate-200 py-3.5 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white shadow-sm">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span>{isTamil ? "இருமொழி AI ஆலோசகர்" : "Bilingual AI Startup Advisor"}</span>
                <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200">
                  Grounded in Govt Portals
                </span>
              </h1>
              <p className="text-[11px] text-slate-500">
                {isTamil ? "தமிழ்நாடு & மத்திய அரசு திட்ட தகவல் மையம்" : "Tamil Nadu & Central MSME Scheme Intelligence"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <button
              onClick={() => setLanguage(language === "en" ? "ta" : "en")}
              className="px-2.5 py-1 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
            >
              {language === "en" ? "தமிழ்" : "English"}
            </button>
          </div>
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 overflow-y-auto space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${
              msg.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.sender === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-slate-900 text-teal-400 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                <Sparkles className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 sm:p-5 text-xs sm:text-sm leading-relaxed shadow-sm ${
                msg.sender === "user"
                  ? "bg-slate-900 text-white rounded-tr-none"
                  : "bg-white text-slate-800 border border-slate-200 rounded-tl-none"
              }`}
            >
              {/* Message text */}
              <div className="whitespace-pre-wrap font-normal">{msg.text}</div>

              {/* Matched Scheme Cards */}
              {msg.matched_schemes && msg.matched_schemes.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                    {isTamil ? "பொருந்தக்கூடிய அரசு திட்டங்கள்:" : "Relevant Government Schemes:"}
                  </span>
                  {msg.matched_schemes.map((s: any) => (
                    <div
                      key={s.id}
                      className="p-3 bg-teal-50/60 rounded-xl border border-teal-200/80 text-xs"
                    >
                      <div className="flex justify-between items-start gap-2">
                        <span className="font-bold text-teal-950">{s.name}</span>
                        <a
                          href={s.official_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] text-teal-700 hover:underline flex items-center gap-1 shrink-0 font-semibold"
                        >
                          <span>Portal</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      <p className="text-[11px] text-teal-900 mt-1">{s.benefits_summary}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Citations & Verified Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                    <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                    <span>{isTamil ? "சரிபார்க்கப்பட்ட அரசு ஆதாரங்கள்:" : "Verified Source Citations:"}</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((src, i) => (
                      <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition-colors"
                      >
                        <span className="truncate max-w-[200px]">{src.title}</span>
                        <ExternalLink className="w-3 h-3 text-slate-400" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              {msg.disclaimer && (
                <div className="mt-3 text-[10px] text-slate-400 border-t border-slate-100 pt-2 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 text-amber-500 shrink-0" />
                  <span>{msg.disclaimer}</span>
                </div>
              )}

              {/* Follow-up question chips */}
              {msg.follow_up_questions && msg.follow_up_questions.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-1.5">
                  {msg.follow_up_questions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(q)}
                      className="text-[11px] text-left bg-slate-50 hover:bg-teal-50 hover:text-teal-900 border border-slate-200 hover:border-teal-300 rounded-lg px-2.5 py-1 text-slate-700 transition-colors"
                    >
                      {q} &rarr;
                    </button>
                  ))}
                </div>
              )}

              <span className="block text-[10px] text-slate-400 mt-2 text-right">
                {msg.timestamp}
              </span>
            </div>

            {msg.sender === "user" && (
              <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 items-center">
            <div className="w-8 h-8 rounded-full bg-slate-900 text-teal-400 flex items-center justify-center shadow-sm">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-500 shadow-sm flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <span>
                {isTamil
                  ? "அதிகாரப்பூர்வ அரசு ஆவணங்களை தேடுகிறது..."
                  : "Searching verified official documents & generating response..."}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested prompts if few messages */}
      {messages.length <= 2 && (
        <div className="max-w-4xl w-full mx-auto px-4 sm:px-6 mb-3">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
            {isTamil ? "பரிந்துரைக்கப்பட்ட கேள்விகள்:" : "Suggested Questions:"}
          </span>
          <div className="flex flex-wrap gap-2">
            {sampleSuggestions.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(s)}
                className="text-xs bg-white border border-slate-200 hover:border-teal-400 hover:bg-teal-50/50 rounded-xl px-3 py-1.5 text-slate-700 font-medium transition-all text-left"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form Bar */}
      <div className="bg-white border-t border-slate-200 p-4 sticky bottom-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="max-w-4xl mx-auto flex items-center gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isTamil
                ? "உங்கள் கேள்வியை தமிழில் அல்லது ஆங்கிலத்தில் தட்டச்சு செய்க..."
                : "Ask any question in English, Tamil (தமிழ்), or mixed..."
            }
            className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 shadow-inner"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-slate-900 hover:bg-slate-800 text-white p-3 rounded-xl shadow-md transition-all disabled:opacity-40 shrink-0"
            aria-label="Send message"
          >
            <Send className="w-4 h-4 text-teal-400" />
          </button>
        </form>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading Chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}

