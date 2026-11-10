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
} from "lucide-react";

export default function HomePage() {
  const { t, language } = useLanguage();

  const featureCards = [
    {
      icon: <Compass className="w-6 h-6 text-teal-600" />,
      title: t.features.f1Title,
      description: t.features.f1Desc,
      tag: "Step 1",
    },
    {
      icon: <Bot className="w-6 h-6 text-indigo-600" />,
      title: t.features.f2Title,
      description: t.features.f2Desc,
      tag: "AI Guided",
    },
    {
      icon: <Landmark className="w-6 h-6 text-emerald-600" />,
      title: t.features.f3Title,
      description: t.features.f3Desc,
      tag: "TN & Central",
    },
    {
      icon: <FileCheck2 className="w-6 h-6 text-amber-600" />,
      title: t.features.f4Title,
      description: t.features.f4Desc,
      tag: "Actionable",
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
      text: "I want to start a small manufacturing business in Coimbatore with ₹3 lakh. What should I do first, and which government schemes should I check?",
    },
    {
      lang: "ta",
      text: "நான் கோயம்புத்தூரில் ₹3 லட்சத்தில் சிறிய தொழில் தொடங்க விரும்புகிறேன். முதலில் என்ன செய்ய வேண்டும்? என்ன அரசு திட்டங்கள் இருக்கின்றன?",
    },
  ];

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-100 via-white to-slate-50 pt-16 pb-20 lg:pt-24 lg:pb-32 border-b border-slate-200">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f01f_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f01f_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold uppercase tracking-wider mb-6 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>{t.hero.badge}</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
            <span>{t.hero.titleLine1}</span>{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-indigo-600">
              {t.hero.titleLine2}
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mt-6 text-base sm:text-lg lg:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            {t.hero.description}
          </p>

          {/* CTA Buttons */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/onboarding"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold px-7 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all text-sm group"
            >
              <span>{t.hero.primaryCta}</span>
              <ArrowRight className="w-4 h-4 text-teal-400 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/schemes"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white hover:bg-slate-50 text-slate-700 font-semibold px-7 py-3.5 rounded-xl border border-slate-300 shadow-sm transition-all text-sm"
            >
              <Landmark className="w-4 h-4 text-teal-600" />
              <span>{t.hero.secondaryCta}</span>
            </Link>
          </div>

          {/* Trust Text */}
          <div className="mt-8 flex items-center justify-center gap-2 text-xs text-slate-500 font-medium">
            <ShieldCheck className="w-4 h-4 text-teal-600" />
            <span>{t.hero.trustText}</span>
          </div>

          {/* Sample Prompts Preview */}
          <div className="mt-12 max-w-3xl mx-auto bg-white rounded-2xl p-5 border border-slate-200 shadow-sm text-left">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-teal-600" />
                {language === "ta" ? "எடுத்துக்காட்டு கேள்விகள்" : "Try Asking In Tamil or English"}
              </span>
              <span className="text-[11px] text-teal-700 font-medium bg-teal-50 px-2 py-0.5 rounded-md">
                Bilingual RAG
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sampleQueries.map((q, idx) => (
                <Link
                  key={idx}
                  href={`/chat?q=${encodeURIComponent(q.text)}`}
                  className="p-3.5 rounded-xl border border-slate-200 hover:border-teal-500 hover:bg-teal-50/30 transition-all text-xs text-slate-700 font-medium group flex flex-col justify-between"
                >
                  <p className="line-clamp-2 leading-relaxed text-slate-800 mb-2">
                    &ldquo;{q.text}&rdquo;
                  </p>
                  <span className="text-[10px] text-teal-600 font-semibold flex items-center gap-1 group-hover:underline">
                    Ask AI Assistant &rarr;
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="py-20 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              {t.features.title}
            </h2>
            <p className="mt-3 text-sm sm:text-base text-slate-600">
              {t.features.subtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {featureCards.map((feat, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl bg-white shadow-sm border border-slate-100 flex items-center justify-center">
                      {feat.icon}
                    </div>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                      {feat.tag}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-2">
                    {feat.title}
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {feat.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Flow */}
      <section className="py-20 bg-slate-50 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              {t.howItWorks.title}
            </h2>
            <p className="mt-3 text-sm sm:text-base text-slate-600">
              {t.howItWorks.subtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((st, i) => (
              <div key={i} className="relative">
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm h-full flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-3xl font-black text-teal-600/30">
                        {st.num}
                      </span>
                      <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">
                        {st.badge}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mb-2">
                      {st.title}
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {st.desc}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Quick CTA inside Flow */}
          <div className="mt-16 text-center">
            <Link
              href="/onboarding"
              className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-8 py-3.5 rounded-xl shadow-md transition-all text-sm"
            >
              <span>{t.hero.primaryCta}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Initial Schemes Preview Bar */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                Key Tamil Nadu & Central Schemes Supported
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                Verified against official Government portals and notifications
              </p>
            </div>
            <Link
              href="/schemes"
              className="mt-4 md:mt-0 text-sm font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1"
            >
              <span>View All Supported Schemes</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50">
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded uppercase">
                TN State Scheme
              </span>
              <h3 className="text-base font-bold text-slate-900 mt-2">NEEDS Scheme</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                New Entrepreneur-cum-Enterprise Development Scheme
              </p>
              <p className="text-xs text-slate-700 mt-3 leading-relaxed">
                Up to 25% capital subsidy (max ₹75 Lakhs) for educated first-generation entrepreneurs in Tamil Nadu.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50">
              <span className="text-[10px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded uppercase">
                TN State Scheme
              </span>
              <h3 className="text-base font-bold text-slate-900 mt-2">UYEGP Scheme</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Unemployed Youth Employment Generation Programme
              </p>
              <p className="text-xs text-slate-700 mt-3 leading-relaxed">
                25% subsidy for micro enterprises in manufacturing, services, and business for youth in Tamil Nadu.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50">
              <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded uppercase">
                Central Govt Scheme
              </span>
              <h3 className="text-base font-bold text-slate-900 mt-2">PMEGP Scheme</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Prime Minister&apos;s Employment Generation Programme
              </p>
              <p className="text-xs text-slate-700 mt-3 leading-relaxed">
                Credit linked subsidy program providing 15% to 35% margin money assistance across India.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

