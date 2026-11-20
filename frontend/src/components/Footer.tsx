"use client";

import React from "react";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { Sparkles, ExternalLink, ShieldCheck, AlertCircle, Wrench } from "lucide-react";

export default function Footer() {
  const { t } = useLanguage();

  const officialPortals = [
    { name: "Tamil Nadu MSME Online", url: "https://msmeonline.tn.gov.in/" },
    { name: "MyScheme Govt of India", url: "https://www.myscheme.gov.in/" },
    { name: "Startup India National Hub", url: "https://www.startupindia.gov.in/" },
    { name: "Official Udyam Registration", url: "https://udyamregistration.gov.in/" },
    { name: "StartupTN Official Portal", url: "https://startuptn.in/" },
  ];

  return (
    <footer className="bg-[#0D0D0E] text-zinc-300 pt-12 pb-8 border-t border-[#24242A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Official Sources Bar */}
        <div className="bg-[#151518] rounded-xl p-5 border border-[#2E2E36] mb-8">
          <div className="flex items-center gap-2 mb-2 text-amber-400 font-semibold text-xs tracking-wider uppercase">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>{t.trust.title}</span>
          </div>
          <p className="text-xs text-zinc-400 mb-3">{t.trust.description}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
            {officialPortals.map((portal) => (
              <a
                key={portal.url}
                href={portal.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2 rounded-md bg-[#1C1C20] hover:bg-[#24242A] border border-[#2E2E36] hover:border-amber-500/40 text-xs text-zinc-300 hover:text-white transition-all group"
              >
                <span className="truncate text-[11px] font-medium">{portal.name}</span>
                <ExternalLink className="w-3 h-3 text-zinc-500 group-hover:text-amber-400 shrink-0 ml-1.5" />
              </a>
            ))}
          </div>
        </div>

        {/* Legal Disclaimer Box */}
        <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3.5 mb-8 text-amber-200/90 text-xs flex gap-2.5 items-start">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed text-[11px] text-zinc-300">{t.disclaimer}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8 text-xs">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-md bg-[#18181C] border border-[#2E2E36] flex items-center justify-center text-amber-400 font-bold">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <span className="text-base font-bold text-white tracking-tight">
                illusion <span className="text-amber-400">AI</span>
              </span>
            </div>
            <p className="text-zinc-400 text-xs max-w-sm leading-relaxed">
              Empowering first-time entrepreneurs in Tamil Nadu and India with automated scheme screening,
              actionable business roadmaps, and hybrid AI tools.
            </p>
          </div>

          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-200 mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-xs text-zinc-400">
              <li>
                <Link href="/onboarding" className="hover:text-amber-400 transition-colors">
                  Business Onboarding
                </Link>
              </li>
              <li>
                <Link href="/schemes" className="hover:text-amber-400 transition-colors">
                  Government Schemes
                </Link>
              </li>
              <li>
                <Link href="/tools" className="hover:text-amber-400 transition-colors flex items-center gap-1.5">
                  <span>AI Tools Studio</span>
                  <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1 py-0.2 rounded border border-amber-500/30">
                    Live
                  </span>
                </Link>
              </li>
              <li>
                <Link href="/chat" className="hover:text-amber-400 transition-colors">
                  Bilingual AI Advisor
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-200 mb-3">
              Tools Ecosystem
            </h4>
            <ul className="space-y-1.5 text-xs text-zinc-400">
              <li>Tavily Live Web Search</li>
              <li>Gemini Vector RAG Search</li>
              <li>Safe AST Math Calculator</li>
              <li>PDF / DOCX Document Extractor</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-[#24242A] pt-6 flex flex-col sm:flex-row justify-between items-center text-[11px] text-zinc-500 gap-4">
          <p>© {new Date().getFullYear()} illusion AI. {t.footer.rights}</p>
          <div className="flex gap-4">
            <span className="hover:text-zinc-400 cursor-pointer">{t.footer.privacy}</span>
            <span className="hover:text-zinc-400 cursor-pointer">{t.footer.terms}</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
