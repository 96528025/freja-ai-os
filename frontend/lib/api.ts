export type AssetType = "idea" | "news" | "brief" | "research" | "link" | "repository" | "document" | "note" | "task";

export interface Asset {
  id: string;
  type: AssetType;
  title: string;
  content: string;
  summary: string | null;
  source: string | null;
  url: string | null;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface DashboardData {
  today_brief: Asset | null;
  latest_ideas: Asset[];
  recent_research: Asset[];
  upcoming_tasks: Asset[];
  stats: { total_assets: number; ideas: number; news: number; research: number; tasks: number };
}

export type FeedbackSignal = "interested" | "not_interested";
export type FeedbackReason = "not_relevant" | "too_basic" | "too_marketing" | "repetitive" | "source_not_useful" | "other";

export interface Feedback {
  id: string;
  brief_id: string;
  asset_id: string | null;
  signal: FeedbackSignal | null;
  reason: FeedbackReason | null;
  satisfaction: number | null;
  note: string | null;
}

export interface BriefFeedbackState {
  satisfaction: Feedback | null;
  items: Array<{ asset: Asset; feedback: Feedback | null }>;
}

export interface PreferenceProfile {
  total_item_feedback: number;
  interested: number;
  not_interested: number;
  average_satisfaction: number | null;
  preferred_topics: string[];
  avoided_topics: string[];
}

export interface SourceDefinition {
  id: string;
  name: string;
  description: string;
  kind: "community" | "official" | "code";
  acquisition: string;
  auth_mode: string;
  availability: "available" | "needs_auth" | "planned";
  enabled: boolean;
  health: "unknown" | "healthy" | "error" | "needs_auth";
  last_error: string | null;
  last_success_at: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function getDashboard(): Promise<DashboardData> {
  const response = await fetch(`${API_URL}/dashboard`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load Personal AI");
  return response.json();
}

export async function captureIdea(content: string): Promise<Asset> {
  const response = await fetch(`${API_URL}/assets/ideas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!response.ok) throw new Error("Idea could not be saved");
  return response.json();
}

export async function generateBrief(): Promise<void> {
  const response = await fetch(`${API_URL}/briefs/generate`, { method: "POST" });
  if (!response.ok) throw new Error("Brief could not be started");
}

export async function getBriefFeedback(briefId: string): Promise<BriefFeedbackState> {
  const response = await fetch(`${API_URL}/briefs/${briefId}/feedback`, { cache: "no-store" });
  if (!response.ok) throw new Error("无法加载简报反馈");
  return response.json();
}

export async function rateBrief(briefId: string, satisfaction: number): Promise<Feedback> {
  const response = await fetch(`${API_URL}/briefs/${briefId}/feedback`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ satisfaction }),
  });
  if (!response.ok) throw new Error("无法保存满意度");
  return response.json();
}

export async function rateBriefItem(
  briefId: string,
  assetId: string,
  signal: FeedbackSignal | null,
  reason: FeedbackReason | null = null,
): Promise<Feedback | null> {
  const response = await fetch(`${API_URL}/briefs/${briefId}/items/${assetId}/feedback`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signal, reason }),
  });
  if (!response.ok) throw new Error("无法保存新闻反馈");
  if (response.status === 204) return null;
  return response.json();
}

export async function getPreferenceProfile(): Promise<PreferenceProfile> {
  const response = await fetch(`${API_URL}/briefs/preferences/profile`, { cache: "no-store" });
  if (!response.ok) throw new Error("无法加载偏好画像");
  return response.json();
}

export async function getSources(): Promise<SourceDefinition[]> {
  const response = await fetch(`${API_URL}/sources`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load sources");
  return response.json();
}

export async function updateSource(sourceId: string, enabled: boolean): Promise<SourceDefinition[]> {
  const response = await fetch(`${API_URL}/sources/${sourceId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail ?? "Could not update source");
  }
  return response.json();
}

export async function updateAllSources(enabled: boolean): Promise<SourceDefinition[]> {
  const response = await fetch(`${API_URL}/sources`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) throw new Error("Could not update sources");
  return response.json();
}
