"use client";

import React from "react";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { Sparkles, ExternalLink, ShieldCheck, AlertCircle } from "lucide-react";

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
    <footer className="bg-slate-900 text-slate-300 pt-12 pb-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Official Sources Bar */}
        <div className="bg-slate-800/80 rounded-2xl p-6 border border-slate-700/60 mb-10">
          <div className="flex items-center gap-2 mb-3 text-teal-400 font-semibold text-sm">
            <ShieldCheck className="w-5 h-5 text-teal-400" />
            <span>{t.trust.title}</span>
          </div>
          <p className="text-xs text-slate-400 mb-4">{t.trust.description}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {officialPortals.map((portal) => (
              <a
                key={portal.url}
                href={portal.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-700/50 hover:border-teal-500/50 text-xs text-slate-300 hover:text-white transition-all group"
              >
                <span className="truncate">{portal.name}</span>
                <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-teal-400 shrink-0 ml-2" />
              </a>
            ))}
          </div>
        </div>

        {/* Legal Disclaimer Box */}
        <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4 mb-10 text-amber-200/90 text-xs flex gap-3 items-start">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">{t.disclaimer}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8 text-sm">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center text-slate-950 font-bold">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">
                illusion <span className="text-teal-400">AI</span>
              </span>
            </div>
            <p className="text-slate-400 text-xs max-w-sm leading-relaxed">
              Simplifying the entrepreneurship journey for aspiring business founders in Tamil Nadu and India.
              Automated scheme verification, actionable roadmaps, and bilingual AI assistance.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <Link href="/onboarding" className="hover:text-teal-400">
                  Business Onboarding
                </Link>
              </li>
              <li>
                <Link href="/schemes" className="hover:text-teal-400">
                  Government Schemes
                </Link>
              </li>
              <li>
                <Link href="/chat" className="hover:text-teal-400">
                  Bilingual AI Chatbot
                </Link>
              </li>
              <li>
                <Link href="/roadmap" className="hover:text-teal-400">
                  Interactive Roadmap
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">
              Tamil Nadu Hubs
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>Chennai • Coimbatore • Madurai</li>
              <li>Salem • Tiruchirappalli • Erode</li>
              <li>Tiruppur • Vellore • Tirunelveli</li>
              <li className="text-teal-400 pt-1">All 38 Districts Supported</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} illusion AI. {t.footer.rights}</p>
          <div className="flex items-center gap-4">
            <span className="text-slate-400">Tamil & English Bilingual Engine</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

