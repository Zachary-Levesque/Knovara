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
  collection_name?: string;
};

export type Citation = {
  title: string;
  source: string;
  relevance: string;
  score?: number | null;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  mode: string;
  collection_name: string;
};

export type MentorRequest = {
  name: string;
  role: string;
  team: string;
  background: string;
  goal: string;
  collection_name?: string;
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
  mode: string;
  collection_name: string;
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

export type CollectionStatus = {
  name: string;
  count: number;
  sample_sources: string[];
};

export type IndexStatus = {
  persist_dir: string;
  default_collection: string;
  openai_configured: boolean;
  collections: CollectionStatus[];
};

export type SourcePreview = {
  title: string;
  source: string;
  content: string;
  chunk_index?: string | null;
};

export type CollectionDetail = {
  name: string;
  count: number;
  chunks: SourcePreview[];
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

export async function getIndexStatus(): Promise<IndexStatus> {
  const response = await fetch(`${API_BASE_URL}/index/status`);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<IndexStatus>;
}

export async function clearCollection(collectionName: string): Promise<IndexStatus> {
  const response = await fetch(`${API_BASE_URL}/collections/${encodeURIComponent(collectionName)}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<IndexStatus>;
}

export async function getCollectionDetail(collectionName: string): Promise<CollectionDetail> {
  const response = await fetch(`${API_BASE_URL}/collections/${encodeURIComponent(collectionName)}`);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<CollectionDetail>;
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
