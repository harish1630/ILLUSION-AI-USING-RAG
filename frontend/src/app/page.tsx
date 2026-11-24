"use client";

import React from "react";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Compass,
  FileCheck2,
  Bot,
  MapPin,
  CheckCircle2,
  TrendingUp,
  Landmark,
  BadgePercent,
  MessageSquare,
  Wrench,
  Calculator,
  Search,
  Database,
  Cpu,
} from "lucide-react";

export default function HomePage() {
  const { t, language } = useLanguage();

  const featureCards = [
    {
      icon: <Compass className="w-5 h-5 text-amber-400" />,
      title: t.features.f1Title,
      description: t.features.f1Desc,
      tag: "Step 1",
    },
    {
      icon: <Bot className="w-5 h-5 text-amber-400" />,
      title: t.features.f2Title,
      description: t.features.f2Desc,
      tag: "AI Guided",
    },
    {
      icon: <Landmark className="w-5 h-5 text-amber-400" />,
      title: t.features.f3Title,
      description: t.features.f3Desc,
      tag: "TN & Central",
    },
    {
      icon: <FileCheck2 className="w-5 h-5 text-amber-400" />,
      title: t.features.f4Title,
      description: t.features.f4Desc,
      tag: "Actionable",
    },
  ];

  const toolsSummary = [
    {
      icon: <Calculator className="w-5 h-5 text-amber-400" />,
      title: "Safe Math AST Calculator",
      desc: "Computes subsidies, loan installments, and investment caps without executing unsafe code or eval().",
    },
    {
      icon: <Search className="w-5 h-5 text-amber-400" />,
      title: "Tavily Real-Time Web Search",
      desc: "Live search across official Tamil Nadu and Central notifications, gazettes, and portals.",
    },
    {
      icon: <Database className="w-5 h-5 text-amber-400" />,
      title: "Gemini Vector RAG Search",
      desc: "Retrieves authentic verified government schemes (NEEDS, UYEGP, PMEGP, StartupTN) with citations.",
    },
    {
      icon: <FileCheck2 className="w-5 h-5 text-amber-400" />,
      title: "Document Extractor (PDF/DOCX)",
      desc: "Instantly parse Detailed Project Reports (DPR), balance sheets, or policy PDFs up to 15 MB.",
    },
  ];

  const steps = [
    {
      num: "01",
      title: t.howItWorks.step1Title,
      desc: t.howItWorks.step1Desc,
      badge: "2 Minutes",
    },
    {
      num: "02",
      title: t.howItWorks.step2Title,
      desc: t.howItWorks.step2Desc,
      badge: "Verified Rules",
    },
    {
      num: "03",
      title: t.howItWorks.step3Title,
      desc: t.howItWorks.step3Desc,
      badge: "Bilingual RAG",
    },
    {
      num: "04",
      title: t.howItWorks.step4Title,
      desc: t.howItWorks.step4Desc,
      badge: "Clear Checklist",
    },
  ];

  const sampleQueries = [
    {
      lang: "en",
      text: "Calculate 25% capital subsidy for ₹40 Lakhs project cost under NEEDS scheme and check Coimbatore rules.",
    },
    {
      lang: "ta",
      text: "ரூ. 30 லட்சத்திற்கு NEEDS மானியத்தை கணக்கிடுங்கள் (25%) மற்றும் தகுதிகளை விளக்குக.",
    },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-[#0D0D0E] text-[#EDEDED]">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-20 lg:pt-24 lg:pb-32 border-b border-[#24242A]">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Badge */}
          <div className="flex flex-wrap items-center justify-center gap-2 mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>{t.hero.badge}</span>
            </div>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight max-w-4xl mx-auto leading-tight">
            <span>{t.hero.titleLine1}</span>{" "}
            <span className="text-amber-400">
              {t.hero.titleLine2}
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mt-6 text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            {t.hero.description}
          </p>

          {/* CTA Buttons */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/onboarding"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black font-semibold px-7 py-3 rounded-lg shadow-sm transition-all text-xs sm:text-sm group"
            >
              <span>{t.hero.primaryCta}</span>
              <ArrowRight className="w-4 h-4 text-black group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/tools"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-[#18181C] hover:bg-[#202026] text-white font-semibold px-7 py-3 rounded-lg border border-[#2E2E36] hover:border-amber-500/40 shadow-sm transition-all text-xs sm:text-sm"
            >
              <Wrench className="w-4 h-4 text-amber-400" />
              <span>Explore AI Tools Studio</span>
            </Link>
          </div>

          {/* Trust Text */}
          <div className="mt-8 flex items-center justify-center gap-2 text-xs text-zinc-500 font-medium">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>{t.hero.trustText}</span>
          </div>

          {/* Sample Prompts Preview */}
          <div className="mt-12 max-w-3xl mx-auto bg-[#151518] rounded-xl p-5 border border-[#2E2E36] shadow-md text-left">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
                {language === "ta" ? "கருவி ஆதரவு கேள்விகள்" : "Interactive Hybrid Tool Prompts"}
              </span>
              <span className="text-[10px] text-amber-400 font-medium bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                Hybrid AI Calling
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sampleQueries.map((q, idx) => (
                <Link
                  key={idx}
                  href={`/chat?q=${encodeURIComponent(q.text)}`}
                  className="p-3.5 rounded-lg border border-[#24242A] bg-[#18181C] hover:border-amber-500/40 hover:bg-[#1E1E24] transition-all text-xs text-zinc-300 font-medium group flex flex-col justify-between"
                >
                  <p className="line-clamp-2 leading-relaxed text-zinc-200 mb-2">
                    &ldquo;{q.text}&rdquo;
                  </p>
                  <span className="text-[10px] text-amber-400 font-semibold flex items-center gap-1 group-hover:underline">
                    Ask AI Advisor &rarr;
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="py-20 bg-[#111114] border-b border-[#24242A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              {t.features.title}
            </h2>
            <p className="mt-3 text-xs sm:text-sm text-zinc-400">
              {t.features.subtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {featureCards.map((feat, i) => (
              <div
                key={i}
                className="p-5 rounded-xl border border-[#2E2E36] bg-[#151518] hover:border-amber-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-lg bg-[#1C1C20] border border-[#2E2E36] flex items-center justify-center">
                      {feat.icon}
                    </div>
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                      {feat.tag}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white mb-1.5">
                    {feat.title}
                  </h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    {feat.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Tools Studio Feature Banner */}
      <section className="py-20 bg-[#0D0D0E] border-b border-[#24242A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-12 gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[10px] font-mono uppercase tracking-wider mb-2 border border-amber-500/30">
                <Cpu className="w-3 h-3" />
                <span>Extensible AI Engine</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-white">
                Modular Hybrid Tool System
              </h2>
              <p className="text-xs sm:text-sm text-zinc-400 mt-1 max-w-xl">
                Automatic, Manual, and Hybrid execution modes with real-time web data, AST arithmetic, and document extraction.
              </p>
            </div>
            <Link
              href="/tools"
              className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1.5"
            >
              <span>Launch Studio Sandbox</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {toolsSummary.map((tool, i) => (
              <div
                key={i}
                className="p-5 rounded-xl border border-[#2E2E36] bg-[#151518] hover:bg-[#1C1C20] hover:border-amber-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="w-9 h-9 rounded-lg bg-[#1F1F24] border border-[#2E2E36] flex items-center justify-center mb-3">
                    {tool.icon}
                  </div>
                  <h3 className="text-sm font-bold text-white mb-1.5">
                    {tool.title}
                  </h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    {tool.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Flow */}
      <section className="py-20 bg-[#111114] border-b border-[#24242A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              {t.howItWorks.title}
            </h2>
            <p className="mt-3 text-xs sm:text-sm text-zinc-400">
              {t.howItWorks.subtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((st, i) => (
              <div key={i} className="relative">
                <div className="bg-[#151518] p-5 rounded-xl border border-[#2E2E36] h-full flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-2xl font-black text-amber-500/20 font-mono">
                        {st.num}
                      </span>
                      <span className="text-[10px] font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                        {st.badge}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-white mb-1.5">
                      {st.title}
                    </h3>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      {st.desc}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
