"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { api, Roadmap, RoadmapTask } from "@/lib/api";
import {
  FileCheck2,
  CheckCircle2,
  Clock,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  FileText,
  Sparkles,
  ArrowRight,
  Filter,
} from "lucide-react";

function RoadmapContent() {
  const searchParams = useSearchParams();
  const queryRoadmapId = searchParams.get("id");

  const { language, t } = useLanguage();
  const isTamil = language === "ta";

  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "pending" | "in_progress" | "completed">("all");

  useEffect(() => {
    loadRoadmap();
  }, [queryRoadmapId]);

  const loadRoadmap = async () => {
    setLoading(true);
    setError(null);
    try {
      const rid = queryRoadmapId || localStorage.getItem("current_roadmap_id");
      if (rid) {
        const data = await api.getRoadmap(rid);
        setRoadmap(data);
      } else {
        // Create a default initial roadmap for Coimbatore Garments / general MSME
        const defaultRoadmap = await api.createRoadmap(
          {
            title: isTamil ? "தொழில் தொடக்க வரைபடம்" : "First-Time Entrepreneur Launch Roadmap",
            business_summary: isTamil
              ? "கோயம்புத்தூரில் சிறிய உற்பத்தி அலகு"
              : "Micro Manufacturing & Service Enterprise in Tamil Nadu",
            category: "manufacturing",
            district: "Coimbatore",
            budget: 300000,
            stage: "idea",
          },
          language
        );
        setRoadmap(defaultRoadmap);
        localStorage.setItem("current_roadmap_id", defaultRoadmap.id);
      }
    } catch (err: any) {
      console.error("Failed to load roadmap:", err);
      setError(isTamil ? "வரைபடத்தை ஏற்றுவதில் பிழை." : "Failed to load roadmap. Please verify backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: "pending" | "in_progress" | "completed") => {
    if (!roadmap) return;
    try {
      const updated = await api.updateTaskStatus(roadmap.id, taskId, newStatus);
      setRoadmap(updated);
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const tasks = roadmap?.tasks || [];
  const filteredTasks = tasks.filter((task) => {
    if (filter === "all") return true;
    return task.status === filter;
  });

  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const progress = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold mb-3">
            <FileCheck2 className="w-3.5 h-3.5 text-teal-600" />
            <span>{isTamil ? "தனிப்பயனாக்கப்பட்ட வணிக வரைபடம்" : "Personalized Launch Roadmap"}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {roadmap?.title || (isTamil ? "உங்கள் தொழில் தொடக்க வரைபடம்" : "Startup Action Plan")}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-600">
            {roadmap?.business_summary}
          </p>
        </div>

        {/* Progress Card */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
            <div>
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                {isTamil ? "முன்னேற்றம்" : "Launch Progress"}
              </span>
              <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">
                {progress}%
              </span>
              <span className="text-xs text-slate-500 ml-2">
                ({completedCount} of {tasks.length} {isTamil ? "பணிகள் முடிந்தது" : "tasks completed"})
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Link
                href="/onboarding"
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <span>{isTamil ? "சுயவிவரத்தை மாற்று" : "Retake Questionnaire"}</span>
              </Link>
              <Link
                href="/chat"
                className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white px-3.5 py-2 rounded-xl text-xs font-semibold shadow-sm transition-all"
              >
                <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                <span>{isTamil ? "ஆலோசகரிடம் கேள்" : "Ask Advisor"}</span>
              </Link>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-teal-500 to-indigo-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 mb-6 text-xs overflow-x-auto pb-1">
          <span className="font-semibold text-slate-500 flex items-center gap-1 mr-1">
            <Filter className="w-3.5 h-3.5" />
            {isTamil ? "வடிகட்டு:" : "Filter:"}
          </span>
          {[
            { id: "all", label: isTamil ? "அனைத்து பணிகள்" : "All Tasks" },
            { id: "pending", label: isTamil ? "நிலுவையில்" : "Pending" },
            { id: "in_progress", label: isTamil ? "செயலில்" : "In Progress" },
            { id: "completed", label: isTamil ? "முடிந்தவை" : "Completed" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as any)}
              className={`px-3 py-1.5 rounded-xl font-semibold transition-colors shrink-0 ${
                filter === tab.id
                  ? "bg-slate-900 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Task Cards List */}
        {loading ? (
          <div className="text-center py-20 text-slate-500 text-sm">
            {isTamil ? "வரைபடம் ஏற்றப்படுகிறது..." : "Loading roadmap checklist..."}
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
            {error}
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 text-xs text-slate-500">
            {isTamil ? "இப்பிரிவில் பணிகள் எதுவும் இல்லை." : "No tasks found in this filter."}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTasks.map((task, idx) => {
              const isCompleted = task.status === "completed";
              const isInProgress = task.status === "in_progress";

              return (
                <div
                  key={task.id}
                  className={`bg-white rounded-2xl p-5 sm:p-6 border transition-all ${
                    isCompleted
                      ? "border-emerald-200 bg-emerald-50/20"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() =>
                          handleStatusChange(
                            task.id,
                            isCompleted ? "pending" : "completed"
                          )
                        }
                        className={`mt-0.5 w-6 h-6 rounded-lg flex items-center justify-center border transition-all shrink-0 ${
                          isCompleted
                            ? "bg-emerald-600 border-emerald-600 text-white shadow-sm"
                            : "border-slate-300 hover:border-teal-500 bg-white"
                        }`}
                        title="Toggle task completion"
                      >
                        {isCompleted && <CheckCircle2 className="w-4 h-4" />}
                      </button>

                      <div>
                        <div className="flex items-center gap-2 mb-1.5">
                          <span
                            className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                              task.priority === "high"
                                ? "bg-red-50 text-red-700 border border-red-200"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {task.priority} priority
                          </span>

                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                              isCompleted
                                ? "bg-emerald-100 text-emerald-800"
                                : isInProgress
                                ? "bg-amber-100 text-amber-800"
                                : "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {task.status.replace("_", " ")}
                          </span>
                        </div>

                        <h3
                          className={`text-sm sm:text-base font-bold tracking-tight ${
                            isCompleted
                              ? "line-through text-slate-400"
                              : "text-slate-900"
                          }`}
                        >
                          {task.title}
                        </h3>

                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                          {task.description}
                        </p>
                      </div>
                    </div>

                    {/* Status switcher controls */}
                    <div className="flex items-center gap-2 self-end sm:self-start shrink-0">
                      <select
                        value={task.status}
                        onChange={(e) =>
                          handleStatusChange(task.id, e.target.value as any)
                        }
                        className="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500"
                      >
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                      </select>
                    </div>
                  </div>

                  {/* Required Documents Checklist */}
                  {task.required_documents && task.required_documents.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-100 ml-9">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1 mb-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        {isTamil ? "தேவையான ஆவணங்கள்:" : "Required Documents:"}
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {task.required_documents.map((doc, i) => (
                          <span
                            key={i}
                            className="text-[11px] bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-md font-medium"
                          >
                            {doc}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Official Portal Button */}
                  {task.official_url && (
                    <div className="mt-3 pt-2 border-t border-slate-100 ml-9 flex justify-between items-center text-xs">
                      <span className="text-[11px] text-slate-400">
                        {isTamil ? "அதிகாரப்பூர்வ அரசு இணைப்பு:" : "Official Govt Portal:"}
                      </span>
                      <a
                        href={task.official_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-teal-700 hover:text-teal-800 font-semibold"
                      >
                        <span>{isTamil ? "இணையதளத்தை திற" : "Open Portal"}</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function RoadmapPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading Roadmap...</div>}>
      <RoadmapContent />
    </Suspense>
  );
}

