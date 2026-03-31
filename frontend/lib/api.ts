export type Profile = {
  id: number;
  full_name: string;
  raw_text: string | null;
  parsed_skills: string[];
  parsed_languages: string[];
  parsed_location: string | null;
  parsed_seniority: string | null;
  availability_status: string;
  source: string;
  created_at: string;
  updated_at: string;
};

export type ProfileSearchParams = {
  q?: string;
  language?: string;
  location?: string;
  seniority?: string;
  availability?: string;
  skill?: string;
  skills?: string[];
  skillMode?: "any" | "all";
  sortBy?: "relevance" | "date" | "seniority";
  limit?: number;
  offset?: number;
};

export type ProfileSearchResponse = {
  total: number;
  items: Profile[];
};

export type Mission = {
  id: number;
  title: string;
  description: string;
  required_skills: string[];
  required_language: string | null;
  required_location: string | null;
  required_seniority: string | null;
  desired_start_date: string | null;
  created_at: string;
  updated_at: string;
};

export type MatchResult = {
  id: number;
  mission_id: number;
  profile_id: number;
  structured_score: number;
  semantic_score: number;
  business_score: number;
  final_score: number;
  explanation_tags: string[];
  created_at: string;
};

export type ProfileUpdatePayload = {
  full_name?: string;
  parsed_skills?: string[];
  parsed_languages?: string[];
  parsed_location?: string | null;
  parsed_seniority?: string | null;
  availability_status?: string;
  raw_text?: string | null;
};

export type MissionPayload = {
  title: string;
  description: string;
  required_skills: string[];
  required_language?: string | null;
  required_location?: string | null;
  required_seniority?: string | null;
  desired_start_date?: string | null;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type AdminIdentity = {
  sub: string;
  role: string;
};

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
const ADMIN_TOKEN_STORAGE_KEY = "optimus_admin_access_token";

function getStoredAdminToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
}

export function saveAdminToken(token: string): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token);
  }
}

export function clearAdminToken(): void {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
  }
}

export function hasAdminToken(): boolean {
  return Boolean(getStoredAdminToken());
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? undefined);
  const token = getStoredAdminToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    ...init,
    headers,
  });

  if (!response.ok) {
    let detail = `API request failed with ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Ignore parse errors and keep fallback detail.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export async function adminLogin(username: string, password: string): Promise<AuthTokenResponse> {
  return apiFetch<AuthTokenResponse>("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });
}

export async function getAdminMe(): Promise<AdminIdentity | null> {
  try {
    return await apiFetch<AdminIdentity>("/auth/me");
  } catch {
    return null;
  }
}

function toSearchQuery(params: ProfileSearchParams): string {
  const search = new URLSearchParams();

  if (params.q) {
    search.set("q", params.q);
  }
  if (params.language) {
    search.set("language", params.language);
  }
  if (params.location) {
    search.set("location", params.location);
  }
  if (params.seniority) {
    search.set("seniority", params.seniority);
  }
  if (params.availability) {
    search.set("availability", params.availability);
  }
  if (params.skill) {
    search.set("skill", params.skill);
  }
  if (params.skills && params.skills.length > 0) {
    const values = params.skills.map((value) => value.trim()).filter(Boolean);
    if (values.length > 0) {
      search.set("skills", values.join(","));
    }
  }
  if (params.skillMode) {
    search.set("skill_mode", params.skillMode);
  }
  if (params.sortBy) {
    search.set("sort_by", params.sortBy);
  }
  if (typeof params.limit === "number") {
    search.set("limit", String(params.limit));
  }
  if (typeof params.offset === "number") {
    search.set("offset", String(params.offset));
  }

  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function getProfiles(filters: ProfileSearchParams = {}): Promise<Profile[]> {
  try {
    return await apiFetch<Profile[]>(`/profiles${toSearchQuery(filters)}`);
  } catch {
    return [];
  }
}

export async function searchProfiles(
  filters: ProfileSearchParams = {},
): Promise<ProfileSearchResponse> {
  try {
    return await apiFetch<ProfileSearchResponse>(`/search/profiles${toSearchQuery(filters)}`);
  } catch {
    return {
      total: 0,
      items: [],
    };
  }
}

export async function getMissions(): Promise<Mission[]> {
  try {
    return await apiFetch<Mission[]>("/missions");
  } catch {
    return [];
  }
}

export async function getMissionMatches(missionId: number): Promise<MatchResult[]> {
  try {
    return await apiFetch<MatchResult[]>(`/missions/${missionId}/matches`);
  } catch {
    return [];
  }
}

export async function getMission(missionId: number): Promise<Mission | null> {
  try {
    return await apiFetch<Mission>(`/missions/${missionId}`);
  } catch {
    return null;
  }
}

export async function createMission(payload: MissionPayload): Promise<Mission> {
  return apiFetch<Mission>("/missions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function updateMission(missionId: number, payload: Partial<MissionPayload>): Promise<Mission> {
  return apiFetch<Mission>(`/missions/${missionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function runMissionMatch(missionId: number, topN = 10): Promise<MatchResult[]> {
  return apiFetch<MatchResult[]>(`/missions/${missionId}/match?top_n=${topN}`, {
    method: "POST",
  });
}

export async function getProfile(profileId: number): Promise<Profile | null> {
  try {
    return await apiFetch<Profile>(`/profiles/${profileId}`);
  } catch {
    return null;
  }
}

export async function manualCorrectProfile(
  profileId: number,
  payload: ProfileUpdatePayload,
): Promise<Profile> {
  return apiFetch<Profile>(`/profiles/${profileId}/manual-correction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
