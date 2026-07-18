/**
 * Backend API client.
 *
 * This file will centralize all frontend calls to the FastAPI backend,
 * including onboarding submission, mentor briefing retrieval, chat requests,
 * ingestion status checks, and shared response typing.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ChatRequest = {
  question: string;
  role?: string;
  team?: string;
};

export type Citation = {
  title: string;
  source: string;
  relevance: string;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
};

export type MentorRequest = {
  name: string;
  role: string;
  team: string;
  background: string;
  goal: string;
};

export type LearningItem = {
  title: string;
  detail: string;
  owner: string;
};

export type MentorBriefing = {
  headline: string;
  summary: string;
  first_week: LearningItem[];
  recommended_sources: string[];
  people_to_meet: string[];
};

export type IngestRequest = {
  directory: string;
  collection_name: string;
};

export type IngestResult = {
  files_processed: number;
  chunks_created: number;
  collection_name: string;
};

export async function askQuestion(request: ChatRequest): Promise<ChatResponse> {
  return postJson<ChatResponse>("/chat", request);
}

export async function getMentorBriefing(request: MentorRequest): Promise<MentorBriefing> {
  return postJson<MentorBriefing>("/mentor", request);
}

export async function ingestDirectory(request: IngestRequest): Promise<IngestResult> {
  return postJson<IngestResult>("/ingest", request);
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}
