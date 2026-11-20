"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { api, Scheme } from "@/lib/api";
import AuthGuard from "@/components/AuthGuard";
import {
  Landmark,
  Search,
  ExternalLink,
  ShieldCheck,
  CheckCircle,
  AlertCircle,
  FileText,
  Building,
  Info,
  Calendar,
  Layers,
} from "lucide-react";

function SchemesPageContent() {
  const { language, t } = useLanguage();
  const isTamil = language === "ta";

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedState, setSelectedState] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");

  useEffect(() => {
    loadSchemes();
  }, [selectedState, selectedType]);

  const loadSchemes = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (selectedState !== "all") params.state = selectedState;
      if (selectedType !== "all") params.scheme_type = selectedType;
      if (search.trim()) params.search = search.trim();

      const data = await api.listSchemes(params);
      setSchemes(data.items);
    } catch (err: any) {
      console.error("Failed to load schemes:", err);
      setError(
        isTamil
          ? "திட்டங்களை ஏற்றுவதில் பிழை. பின்னர் முயற்சிக்கவும்."
          : "Failed to load government schemes. Ensure backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadSchemes();
  };

  return (
    <div className="min-h-screen bg-[#0D0D0E] text-[#EDEDED] py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold mb-3">
            <Landmark className="w-3.5 h-3.5" />
            <span>{isTamil ? "அரசு மானியங்கள் & கடன் திட்டங்கள்" : "Tamil Nadu & Central Government Schemes"}</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            {isTamil ? "அரசு உதவி திட்டங்கள் மற்றும் மானியங்கள்" : "Verified Government Schemes & Subsidies"}
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-zinc-400 max-w-3xl">
            {isTamil
              ? "தமிழ்நாடு மற்றும் மத்திய அரசால் தொழில்முனைவோருக்கு வழங்கப்படும் அதிகாரப்பூர்வ மானியங்கள், கடன்கள் மற்றும் உத்யாம் வழிகாட்டல்கள்."
              : "Discover verified state and central schemes (NEEDS, UYEGP, PMEGP, TANSEED, Udyam) with authentic criteria, documents, and official application portals."}
          </p>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="bg-[#151518] p-4 rounded-xl border border-[#2E2E36] shadow-sm space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-zinc-500 absolute left-3.5 top-3" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={
                  isTamil
                    ? "திட்டத்தின் பெயர் அல்லது விபரத்தை தேடுங்கள் (எ.கா: NEEDS, UYEGP, உற்பத்தி, மானியம்)..."
                    : "Search schemes by keyword (e.g. NEEDS, UYEGP, PMEGP, manufacturing, subsidy)..."
                }
                className="w-full pl-10 pr-4 py-2 bg-[#1C1C20] border border-[#2E2E36] rounded-lg text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500"
              />
            </div>
            <button
              type="submit"
              className="bg-amber-500 hover:bg-amber-400 text-black px-4 py-2 rounded-lg text-xs font-semibold transition-all shrink-0"
            >
              {isTamil ? "தேடு" : "Search Schemes"}
            </button>
          </form>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[#24242A] text-xs">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
                {isTamil ? "மாநிலம்:" : "Scope:"}
              </span>
              {[
                { id: "all", label: isTamil ? "அனைத்தும்" : "All" },
                { id: "Tamil Nadu", label: "Tamil Nadu" },
                { id: "Central", label: "Central" },
              ].map((st) => (
                <button
                  key={st.id}
                  onClick={() => setSelectedState(st.id)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                    selectedState === st.id
                      ? "bg-amber-500 text-black font-semibold"
                      : "bg-[#1C1C20] text-zinc-400 hover:text-white border border-[#2E2E36]"
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="font-semibold text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
                {isTamil ? "வகை:" : "Type:"}
              </span>
              {[
                { id: "all", label: isTamil ? "அனைத்தும்" : "All" },
                { id: "subsidy", label: "Subsidy" },
                { id: "grant", label: "Grant" },
                { id: "loan", label: "Loan" },
                { id: "support", label: "Udyam" },
              ].map((tp) => (
                <button
                  key={tp.id}
                  onClick={() => setSelectedType(tp.id)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                    selectedType === tp.id
                      ? "bg-amber-500 text-black font-semibold"
                      : "bg-[#1C1C20] text-zinc-400 hover:text-white border border-[#2E2E36]"
                  }`}
                >
                  {tp.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Info */}
        {error ? (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
            {error}
          </div>
        ) : loading ? (
          <div className="text-center py-20 text-zinc-500 text-xs font-mono">
            {isTamil ? "அரசு திட்டங்கள் ஏற்றப்படுகின்றன..." : "Loading authentic government schemes..."}
          </div>
        ) : schemes.length === 0 ? (
          <div className="text-center py-20 bg-[#151518] rounded-xl border border-[#2E2E36]">
            <Info className="w-8 h-8 text-zinc-500 mx-auto mb-2" />
            <p className="text-xs text-zinc-400 font-medium">
              {isTamil ? "பொருத்தமான திட்டங்கள் எதுவும் காணப்படவில்லை." : "No matching schemes found for your search."}
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            {schemes.map((scheme) => (
              <div
                key={scheme.id}
                className="bg-[#151518] rounded-xl p-5 sm:p-6 border border-[#2E2E36] hover:border-amber-500/40 transition-all"
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-[#24242A]">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                        {scheme.state}
                      </span>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#1C1C20] text-zinc-300 border border-[#2E2E36]">
                        {scheme.scheme_type}
                      </span>
                      <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        <ShieldCheck className="w-3 h-3" />
                        Verified Source
                      </span>
                    </div>
                    <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                      {scheme.name}
                    </h2>
                    <p className="text-xs text-zinc-400 mt-0.5">
                      {scheme.department}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {scheme.application_url && (
                      <a
                        href={scheme.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-black px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
                      >
                        <span>{isTamil ? "விண்ணப்பிக்கவும்" : "Apply Online"}</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                    <a
                      href={scheme.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 border border-[#2E2E36] bg-[#1C1C20] hover:bg-[#222228] text-zinc-300 px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
                    >
                      <span>{isTamil ? "அரசு தளம்" : "Official Portal"}</span>
                      <ExternalLink className="w-3.5 h-3.5 text-zinc-500" />
                    </a>
                  </div>
                </div>

                {/* Content grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
                  {/* Benefits & Subsidies */}
                  <div className="bg-[#1C1C20] rounded-lg p-3.5 border border-[#2E2E36]">
                    <h3 className="text-[11px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 mb-2 font-mono">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>{isTamil ? "திட்டத்தின் பயன்கள் & மானியம்" : "Financial Benefits & Subsidy"}</span>
                    </h3>
                    <p className="text-xs text-zinc-300 leading-relaxed">
                      {scheme.benefits_summary}
                    </p>
                  </div>

                  {/* Eligibility Criteria */}
                  <div className="bg-[#1C1C20] rounded-lg p-3.5 border border-[#2E2E36]">
                    <h3 className="text-[11px] font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5 mb-2 font-mono">
                      <Info className="w-3.5 h-3.5 text-amber-400" />
                      <span>{isTamil ? "தகுதி வரம்புகள்" : "Eligibility Criteria"}</span>
                    </h3>
                    <p className="text-xs text-zinc-300 leading-relaxed">
                      {scheme.eligibility_summary}
                    </p>
                  </div>
                </div>

                {/* Required Documents & Application Steps */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1 text-xs">
                  {scheme.required_documents && scheme.required_documents.length > 0 && (
                    <div>
                      <h4 className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <FileText className="w-3 h-3 text-zinc-500" />
                        <span>{isTamil ? "தேவையான ஆவணங்கள்" : "Required Documents"}</span>
                      </h4>
                      <ul className="space-y-1 text-xs text-zinc-400">
                        {scheme.required_documents.map((doc, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-amber-400 font-bold">•</span>
                            <span>{doc}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {scheme.application_steps && scheme.application_steps.length > 0 && (
                    <div>
                      <h4 className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Layers className="w-3 h-3 text-zinc-500" />
                        <span>{isTamil ? "விண்ணப்பிக்கும் வழிமுறைகள்" : "How to Apply"}</span>
                      </h4>
                      <ul className="space-y-1 text-xs text-zinc-400">
                        {scheme.application_steps.map((step, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-zinc-500 font-mono">{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SchemesPage() {
  return (
    <AuthGuard>
      <SchemesPageContent />
    </AuthGuard>
  );
}
