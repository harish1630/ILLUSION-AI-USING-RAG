/**
 * API client connecting frontend to illusion AI backend.
 */

const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL ||
  "https://illusion-ai-using-rag.onrender.com/api/v1"
).replace(/\/+$/, "");
const API_HEALTH_URL = `${API_BASE.replace(/\/api\/v1$/, "")}/health`;

export interface Scheme {
  id: string;
  name: string;
  department: string;
  description: string;
  state: string;
  scheme_type: string;
  official_url: string;
  application_url?: string;
  benefits_summary: string;
  eligibility_summary: string;
  exclusions?: string[];
  required_documents?: string[];
  application_steps?: string[];
  last_verified_at?: string;
  eligibility_status?: string;
  match_reasons?: string[];
  missing_criteria?: string[];
}

export interface RoadmapTask {
  id: string;
  roadmap_id: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  status: "pending" | "in_progress" | "completed";
  prerequisites?: string[];
  required_documents?: string[];
  official_url?: string;
  source_references?: string[];
}

export interface Roadmap {
  id: string;
  user_id: string;
  title: string;
  business_summary: string;
  status: string;
  progress_percentage: number;
  tasks: RoadmapTask[];
  created_at: string;
}

export interface ChatSource {
  title: string;
  url: string;
  document_id?: string;
  page?: number;
  section?: string;
  last_verified_at?: string;
}

export interface ChatResponse {
  answer: string;
  language: string;
  sources: ChatSource[];
  eligibility_status?: string;
  follow_up_questions: string[];
  matched_schemes: Scheme[];
  disclaimer: string;
  conversation_id?: string;
}

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(API_HEALTH_URL);
    if (!res.ok) throw new Error("Backend offline");
    return res.json();
  },

  // Schemes
  async listSchemes(params?: { state?: string; scheme_type?: string; search?: string }): Promise<{ total: number; items: Scheme[]; disclaimer: string }> {
    const query = new URLSearchParams();
    if (params?.state) query.set("state", params.state);
    if (params?.scheme_type) query.set("scheme_type", params.scheme_type);
    if (params?.search) query.set("search", params.search);

    const res = await fetch(`${API_BASE}/schemes?${query.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch schemes");
    return res.json();
  },

  async getScheme(id: string): Promise<Scheme> {
    const res = await fetch(`${API_BASE}/schemes/${id}`);
    if (!res.ok) throw new Error("Scheme not found");
    return res.json();
  },

  async matchSchemes(data: any): Promise<Scheme[]> {
    const res = await fetch(`${API_BASE}/schemes/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to screen schemes");
    return res.json();
  },

  // Business Onboarding
  async saveBusinessProfile(data: any) {
    const res = await fetch(`${API_BASE}/business/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to save profile");
    return res.json();
  },

  // Roadmaps
  async createRoadmap(data: any, language: string = "en"): Promise<Roadmap> {
    const res = await fetch(`${API_BASE}/roadmaps?language=${encodeURIComponent(language)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to generate roadmap");
    return res.json();
  },

  async getRoadmap(roadmapId: string): Promise<Roadmap> {
    const res = await fetch(`${API_BASE}/roadmaps/${roadmapId}`);
    if (!res.ok) throw new Error("Roadmap not found");
    return res.json();
  },

  async updateTaskStatus(roadmapId: string, taskId: string, status: string): Promise<Roadmap> {
    const res = await fetch(`${API_BASE}/roadmaps/${roadmapId}/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error("Failed to update task");
    return res.json();
  },

  // Chat
  async sendChatMessage(question: string, language: string = "en", profile?: any): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, language, profile }),
    });
    if (!res.ok) throw new Error("Chat request failed");
    return res.json();
  },
};
