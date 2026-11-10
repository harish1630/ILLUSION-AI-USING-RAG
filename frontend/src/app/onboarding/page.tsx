"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { api } from "@/lib/api";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Building2,
  MapPin,
  Coins,
  CheckCircle2,
  HelpCircle,
  ShieldCheck,
  Compass,
} from "lucide-react";

const TN_DISTRICTS = [
  "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
  "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
  "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal",
  "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet",
  "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi",
  "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", "Tiruvallur",
  "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"
];

export default function OnboardingPage() {
  const router = useRouter();
  const { language, setLanguage, t } = useLanguage();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    preferred_language: language,
    state: "Tamil Nadu",
    district: "Coimbatore",
    business_idea: "",
    business_category: "manufacturing",
    investment_budget: 300000,
    business_stage: "idea",
    age_range: "18-35",
    first_generation_entrepreneur: true,
    primary_need: "subsidies",
  });

  const isTamil = language === "ta";

  const handleNext = () => {
    if (step === 2 && !formData.business_idea.trim()) {
      setError(isTamil ? "தயவுசெய்து உங்கள் தொழில் யோசனையை குறிப்பிடவும்." : "Please describe your business idea or activity.");
      return;
    }
    setError(null);
    setStep((prev) => Math.min(prev + 1, 4));
  };

  const handlePrev = () => {
    setError(null);
    setStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // 1. Save profile
      const profile = await api.saveBusinessProfile({
        preferred_language: language,
        state: formData.state,
        district: formData.district,
        business_idea: formData.business_idea,
        business_category: formData.business_category,
        investment_budget: Number(formData.investment_budget),
        business_stage: formData.business_stage,
        age_range: formData.age_range,
        first_generation_entrepreneur: formData.first_generation_entrepreneur,
        primary_need: formData.primary_need,
      });

      // 2. Generate Roadmap
      const roadmap = await api.createRoadmap(
        {
          user_id: profile.id,
          title: `${formData.business_idea.slice(0, 40)} Launch Roadmap`,
          business_summary: formData.business_idea,
          category: formData.business_category,
          district: formData.district,
          budget: Number(formData.investment_budget),
          stage: formData.business_stage,
        },
        language
      );

      // Save locally
      localStorage.setItem("current_roadmap_id", roadmap.id);
      localStorage.setItem("current_profile", JSON.stringify(formData));

      // Redirect to roadmap page
      router.push(`/roadmap?id=${roadmap.id}`);
    } catch (err: any) {
      console.error("Onboarding failed:", err);
      setError(isTamil ? "சேமிப்பதில் பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்." : "Failed to generate roadmap. Please verify backend is running.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold mb-3">
            <Compass className="w-3.5 h-3.5 text-teal-600" />
            <span>{isTamil ? "தொழில் தொடக்க சுயவிவரம்" : "Step-by-Step Onboarding Questionnaire"}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {isTamil ? "உங்கள் வணிக பயணத்தை தொடங்குங்கள்" : "Launch Your Business Journey"}
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-600">
            {isTamil
              ? "எளிய 4 படிகளில் உங்கள் தொழில் யோசனைக்கான அரசு திட்டங்கள் மற்றும் வரைபடத்தைப் பெறுங்கள்."
              : "Tell us about your venture to discover eligible schemes and generate your tailored action plan."}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
            <span>{isTamil ? `படி ${step} / 4` : `Step ${step} of 4`}</span>
            <span>{Math.round((step / 4) * 100)}%</span>
          </div>
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
            <div
              className="bg-teal-600 h-full transition-all duration-300 rounded-full"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>
        </div>

        {/* Card Form */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm">
          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Step 1: Language & District */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "விருப்பமான மொழி" : "Preferred Language"}
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setLanguage("en")}
                      className={`p-3 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
                        language === "en"
                          ? "border-teal-600 bg-teal-50 text-teal-900 ring-2 ring-teal-500/20"
                          : "border-slate-200 hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <span>English</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setLanguage("ta")}
                      className={`p-3 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
                        language === "ta"
                          ? "border-teal-600 bg-teal-50 text-teal-900 ring-2 ring-teal-500/20"
                          : "border-slate-200 hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <span>தமிழ் (Tamil)</span>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "மாநிலம் & மாவட்டம்" : "State & District"}
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <input
                        type="text"
                        disabled
                        value="Tamil Nadu"
                        className="w-full bg-slate-100 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-600 font-medium cursor-not-allowed"
                      />
                    </div>
                    <div>
                      <select
                        value={formData.district}
                        onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                        className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                      >
                        {TN_DISTRICTS.map((d) => (
                          <option key={d} value={d}>
                            {d}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <p className="mt-1.5 text-[11px] text-slate-500">
                    {isTamil
                      ? "மாவட்ட தொழில் மையம் (DIC) மூலம் விண்ணப்பிக்க உங்கள் மாவட்டத்தைத் தேர்ந்தெடுக்கவும்."
                      : "District selects the respective District Industries Centre (DIC) jurisdiction."}
                  </p>
                </div>
              </div>
            )}

            {/* Step 2: Business Idea & Category */}
            {step === 2 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "வணிக வகை (Category)" : "Business Category"}
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                    {[
                      { id: "manufacturing", labelEn: "Manufacturing", labelTa: "உற்பத்தி" },
                      { id: "services", labelEn: "Services", labelTa: "சேவை" },
                      { id: "trading", labelEn: "Trading / Retail", labelTa: "வர்த்தகம்" },
                      { id: "agriculture_allied", labelEn: "Agri-Allied", labelTa: "வேளாண் சார்ந்த" },
                      { id: "other", labelEn: "Other", labelTa: "மற்றவை" },
                    ].map((cat) => (
                      <button
                        key={cat.id}
                        type="button"
                        onClick={() => setFormData({ ...formData, business_category: cat.id })}
                        className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                          formData.business_category === cat.id
                            ? "border-teal-600 bg-teal-50 text-teal-900 ring-2 ring-teal-500/20"
                            : "border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {isTamil ? cat.labelTa : cat.labelEn}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "உங்கள் தொழில் யோசனை" : "Business Idea or Activity"}
                  </label>
                  <textarea
                    rows={4}
                    value={formData.business_idea}
                    onChange={(e) => setFormData({ ...formData, business_idea: e.target.value })}
                    placeholder={
                      isTamil
                        ? "எ.கா: கோயம்புத்தூரில் சிறிய ஆடை உற்பத்தி தொழிற்சாலை அல்லது இயற்கை தேன் தயாரிப்பு அலகு..."
                        : "e.g., Small garment manufacturing unit in Coimbatore, organic food processing, or IT services..."
                    }
                    className="w-full bg-white border border-slate-300 rounded-xl p-3.5 text-xs text-slate-800 focus:ring-2 focus:ring-teal-500 focus:outline-none leading-relaxed"
                  />
                  <p className="mt-1.5 text-[11px] text-slate-500">
                    {isTamil
                      ? "எளிய முறையில் விளக்குங்கள். அதிகாரப்பூர்வ சொற்கள் தேவையில்லை."
                      : "Describe simply. You don't need formal technical business jargon."}
                  </p>
                </div>
              </div>
            )}

            {/* Step 3: Investment Budget & Stage */}
            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "உத்தேச முதலீட்டு பட்ஜெட் (ரூபாயில்)" : "Estimated Investment Budget (₹ INR)"}
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-sm font-bold text-slate-500">
                      ₹
                    </span>
                    <input
                      type="number"
                      min={10000}
                      step={50000}
                      value={formData.investment_budget}
                      onChange={(e) =>
                        setFormData({ ...formData, investment_budget: Number(e.target.value) })
                      }
                      className="w-full pl-8 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-semibold text-slate-800 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <div className="flex gap-2 mt-2">
                    {[100000, 300000, 1000000, 2500000, 5000000].map((amt) => (
                      <button
                        key={amt}
                        type="button"
                        onClick={() => setFormData({ ...formData, investment_budget: amt })}
                        className="px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded-md text-[10px] font-semibold text-slate-700"
                      >
                        ₹{(amt / 100000).toFixed(amt >= 100000 ? 0 : 1)}L
                      </button>
                    ))}
                  </div>
                  <p className="mt-1.5 text-[11px] text-slate-500">
                    {isTamil
                      ? "இயந்திரங்கள், வாடகை முன்பணம் மற்றும் நடைமுறை மூலதனம் உள்ளிட்ட உத்தேச செலவு."
                      : "Includes machinery, rental deposit, and working capital estimation."}
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "வணிகத்தின் தற்போதைய நிலை" : "Current Business Stage"}
                  </label>
                  <div className="grid grid-cols-2 gap-2.5">
                    {[
                      { id: "idea", labelEn: "Idea Phase", labelTa: "யோசனை நிலை" },
                      { id: "planning", labelEn: "Planning & DPR", labelTa: "திட்டமிடல்" },
                      { id: "registration", labelEn: "Registration", labelTa: "பதிவு நிலை" },
                      { id: "operating", labelEn: "Already Operating", labelTa: "இயங்குகிறது" },
                    ].map((stg) => (
                      <button
                        key={stg.id}
                        type="button"
                        onClick={() => setFormData({ ...formData, business_stage: stg.id })}
                        className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                          formData.business_stage === stg.id
                            ? "border-teal-600 bg-teal-50 text-teal-900 ring-2 ring-teal-500/20"
                            : "border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {isTamil ? stg.labelTa : stg.labelEn}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Eligibility Details (Optional & Transparent) */}
            {step === 4 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "வயது வரம்பு (தகுதி சரிபார்ப்புக்கு மட்டும்)" : "Age Range (Eligibility Only)"}
                  </label>
                  <select
                    value={formData.age_range}
                    onChange={(e) => setFormData({ ...formData, age_range: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  >
                    <option value="18-35">18 - 35 Years (General UYEGP / NEEDS Youth)</option>
                    <option value="36-45">36 - 45 Years (Special Categories / Concessions)</option>
                    <option value="46+">46+ Years (PMEGP / MUDRA / MSME Loans)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "முதல் தலைமுறை தொழில்முனைவோரா?" : "First-Generation Entrepreneur?"}
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, first_generation_entrepreneur: true })}
                      className={`p-3 rounded-xl border text-xs font-semibold transition-all ${
                        formData.first_generation_entrepreneur === true
                          ? "border-teal-600 bg-teal-50 text-teal-900 ring-2 ring-teal-500/20"
                          : "border-slate-200 text-slate-700"
                      }`}
                    >
                      {isTamil ? "ஆம் (Yes)" : "Yes, First Generation"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, first_generation_entrepreneur: false })}
                      className={`p-3 rounded-xl border text-xs font-semibold transition-all ${
                        formData.first_generation_entrepreneur === false
                          ? "border-teal-600 bg-teal-50 text-teal-900 ring-2 ring-teal-500/20"
                          : "border-slate-200 text-slate-700"
                      }`}
                    >
                      {isTamil ? "இல்லை (No)" : "No, Family in Business"}
                    </button>
                  </div>
                  <p className="mt-1.5 text-[11px] text-slate-500">
                    {isTamil
                      ? "தமிழ்நாடு NEEDS திட்டத்திற்கு முதல் தலைமுறை தொழில்முனைவோர் தகுதி தேவைப்படுகிறது."
                      : "Required for Tamil Nadu NEEDS capital subsidy qualification."}
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                    {isTamil ? "முதன்மை தேவை" : "Primary Need"}
                  </label>
                  <select
                    value={formData.primary_need}
                    onChange={(e) => setFormData({ ...formData, primary_need: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  >
                    <option value="subsidies">Government Subsidies & Grants (மானியம்)</option>
                    <option value="loans">Bank Loans & Working Capital (கடன்)</option>
                    <option value="registration">Udyam & Legal Licences (பதிவு)</option>
                    <option value="general_guidance">General Startup Roadmap (முழு வழிகாட்டல்)</option>
                  </select>
                </div>

                {/* Privacy Guarantee Note */}
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-[11px] flex gap-2 items-center">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    {isTamil
                      ? "நாங்கள் ஆதார் எண் அல்லது வங்கி கணக்கு போன்ற தனிப்பட்ட இரகசியங்களை கேட்பதில்லை."
                      : "We never ask for Aadhaar numbers, bank credentials, or sensitive personal data."}
                  </span>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between">
              {step > 1 ? (
                <button
                  type="button"
                  onClick={handlePrev}
                  className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>{isTamil ? "முந்தைய படி" : "Previous"}</span>
                </button>
              ) : (
                <div />
              )}

              {step < 4 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-xl text-xs font-semibold shadow-sm transition-all"
                >
                  <span>{isTamil ? "அடுத்த படி" : "Continue"}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-teal-400" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white px-6 py-2.5 rounded-xl text-xs font-bold shadow-md transition-all disabled:opacity-50"
                >
                  {loading ? (
                    <span>{isTamil ? "உருவாக்குகிறது..." : "Generating Roadmap..."}</span>
                  ) : (
                    <>
                      <span>{isTamil ? "வரைபடத்தை உருவாக்கு" : "Generate My Launch Roadmap"}</span>
                      <Sparkles className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

