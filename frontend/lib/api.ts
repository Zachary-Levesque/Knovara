const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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

export type ChatRequest = {
  question: string;
  role: string;
  team: string;
};

export type ChatResponse = {
  answer: string;
  citations: Array<{
    title: string;
    source: string;
    relevance: string;
  }>;
  follow_ups: string[];
};

async function postJson<TResponse, TBody>(path: string, body: TBody): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Knovara API request failed: ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}

export function getMentorBriefing(request: MentorRequest): Promise<MentorBriefing> {
  return postJson<MentorBriefing, MentorRequest>("/mentor", request);
}

export function askQuestion(request: ChatRequest): Promise<ChatResponse> {
  return postJson<ChatResponse, ChatRequest>("/chat", request);
}
