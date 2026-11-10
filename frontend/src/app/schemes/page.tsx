"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { api, Scheme } from "@/lib/api";
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

export default function SchemesPage() {
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
      setError(isTamil ? "திட்டங்களை ஏற்றுவதில் பிழை. பின்னர் முயற்சிக்கவும்." : "Failed to load government schemes. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadSchemes();
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold mb-3">
            <Landmark className="w-3.5 h-3.5 text-teal-600" />
            <span>{isTamil ? "அரசு மானியங்கள் & கடன் திட்டங்கள்" : "Tamil Nadu & Central Government Schemes"}</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {isTamil ? "அரசு உதவி திட்டங்கள் மற்றும் மானியங்கள்" : "Verified Government Schemes & Subsidies"}
          </h1>
          <p className="mt-2 text-sm text-slate-600 max-w-3xl">
            {isTamil
              ? "தமிழ்நாடு மற்றும் மத்திய அரசால் தொழில்முனைவோருக்கு வழங்கப்படும் அதிகாரப்பூர்வ மானியங்கள், கடன்கள் மற்றும் உத்யாம் வழிகாட்டல்கள்."
              : "Discover verified state and central schemes (NEEDS, UYEGP, PMEGP, TANSEED, Udyam) with authentic criteria, documents, and official application portals."}
          </p>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm mb-8 space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={
                  isTamil
                    ? "திட்டத்தின் பெயர் அல்லது விபரத்தை தேடுங்கள் (எ.கா: NEEDS, UYEGP, உற்பத்தி, மானியம்)..."
                    : "Search schemes by keyword (e.g. NEEDS, UYEGP, PMEGP, manufacturing, subsidy)..."
                }
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <button
              type="submit"
              className="bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-xl text-xs font-semibold shadow-sm transition-all shrink-0"
            >
              {isTamil ? "தேடு" : "Search Schemes"}
            </button>
          </form>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-500 text-[11px] uppercase tracking-wider">
                {isTamil ? "மாநிலம்:" : "Scope:"}
              </span>
              {[
                { id: "all", label: isTamil ? "அனைத்தும்" : "All" },
                { id: "Tamil Nadu", label: "Tamil Nadu (மாநிலம்)" },
                { id: "Central", label: "Central (மத்திய அரசு)" },
              ].map((st) => (
                <button
                  key={st.id}
                  onClick={() => setSelectedState(st.id)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    selectedState === st.id
                      ? "bg-teal-600 text-white font-semibold"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-500 text-[11px] uppercase tracking-wider">
                {isTamil ? "வகை:" : "Type:"}
              </span>
              {[
                { id: "all", label: isTamil ? "அனைத்தும்" : "All" },
                { id: "subsidy", label: isTamil ? "மானியம் (Subsidy)" : "Subsidy" },
                { id: "grant", label: isTamil ? "நிதி (Grant)" : "Grant" },
                { id: "loan", label: isTamil ? "கடன் (Loan)" : "Loan" },
                { id: "support", label: isTamil ? "சான்றிதழ் (Udyam)" : "Support" },
              ].map((tp) => (
                <button
                  key={tp.id}
                  onClick={() => setSelectedType(tp.id)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    selectedType === tp.id
                      ? "bg-slate-900 text-white font-semibold"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
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
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
            {error}
          </div>
        ) : loading ? (
          <div className="text-center py-20 text-slate-500 text-sm">
            {isTamil ? "அரசு திட்டங்கள் ஏற்றப்படுகின்றன..." : "Loading authentic government schemes..."}
          </div>
        ) : schemes.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-slate-200">
            <Info className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm text-slate-600 font-medium">
              {isTamil ? "பொருத்தமான திட்டங்கள் எதுவும் காணப்படவில்லை." : "No matching schemes found for your search."}
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {schemes.map((scheme) => (
              <div
                key={scheme.id}
                className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200 hover:border-teal-300 shadow-sm transition-all"
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-slate-100">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200">
                        {scheme.state}
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                        {scheme.scheme_type}
                      </span>
                      <span className="text-[10px] text-emerald-700 font-semibold flex items-center gap-1 bg-emerald-50 px-2 py-0.5 rounded-md">
                        <ShieldCheck className="w-3 h-3 text-emerald-600" />
                        Verified Official Source
                      </span>
                    </div>
                    <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                      {scheme.name}
                    </h2>
                    <p className="text-xs text-slate-500 font-medium mt-0.5">
                      {scheme.department}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {scheme.application_url && (
                      <a
                        href={scheme.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 bg-teal-600 hover:bg-teal-700 text-white px-3.5 py-2 rounded-xl text-xs font-semibold shadow-sm transition-all"
                      >
                        <span>{isTamil ? "விண்ணப்பிக்கவும்" : "Apply Online"}</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                    <a
                      href={scheme.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all"
                    >
                      <span>{isTamil ? "அரசு தளம்" : "Official Portal"}</span>
                      <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                    </a>
                  </div>
                </div>

                {/* Content grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-4">
                  {/* Benefits & Subsidies */}
                  <div className="bg-emerald-50/50 rounded-xl p-4 border border-emerald-100">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-900 flex items-center gap-1.5 mb-2">
                      <CheckCircle className="w-4 h-4 text-emerald-600" />
                      {isTamil ? "திட்டத்தின் பயன்கள் & மானியம்" : "Financial Benefits & Subsidy"}
                    </h3>
                    <p className="text-xs text-slate-800 leading-relaxed font-medium">
                      {scheme.benefits_summary}
                    </p>
                  </div>

                  {/* Eligibility Criteria */}
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5 mb-2">
                      <Info className="w-4 h-4 text-indigo-600" />
                      {isTamil ? "தகுதி வரம்புகள்" : "Eligibility Criteria"}
                    </h3>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {scheme.eligibility_summary}
                    </p>
                  </div>
                </div>

                {/* Required Documents & Application Steps */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                  {scheme.required_documents && scheme.required_documents.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-slate-500" />
                        {isTamil ? "தேவையான ஆவணங்கள்" : "Required Documents"}
                      </h4>
                      <ul className="space-y-1.5 text-xs text-slate-600">
                        {scheme.required_documents.map((doc, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-teal-600 font-bold">•</span>
                            <span>{doc}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {scheme.application_steps && scheme.application_steps.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-slate-500" />
                        {isTamil ? "விண்ணப்பிக்கும் வழிமுறைகள்" : "How to Apply"}
                      </h4>
                      <ul className="space-y-1.5 text-xs text-slate-600">
                        {scheme.application_steps.map((step, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-slate-400 font-semibold">{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Exclusions note if any */}
                {scheme.exclusions && scheme.exclusions.length > 0 && (
                  <div className="mt-4 p-3 bg-amber-50/80 border border-amber-200/60 rounded-xl text-[11px] text-amber-900 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">{isTamil ? "விலக்குகள் & நிபந்தனைகள்: " : "Known Exclusions & Conditions: "}</span>
                      <span>{scheme.exclusions.join("; ")}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

