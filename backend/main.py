"""FastAPI application entry point for Knovara."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chat import ChatRequest, ChatResponse, answer_question
from config import CORS_ORIGINS, OPENAI_API_KEY, OPENAI_CHAT_MODEL
from ingest import IngestRequest, ingest_directory
from mentor import MentorBriefing, MentorRequest, build_briefing
from models import IngestResult
from retrieval import SourceChunk, search_sources


app = FastAPI(
    title="Knovara API",
    version="0.1.0",
    description="Technical onboarding copilot demo API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "mode": "demo" if not OPENAI_API_KEY else "llm-ready",
        "chat_model": OPENAI_CHAT_MODEL,
    }


@app.get("/sources", response_model=list[SourceChunk])
def sources(query: str = "architecture onboarding decisions") -> list[SourceChunk]:
    return search_sources(query)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return answer_question(request)


@app.post("/mentor", response_model=MentorBriefing)
def mentor(request: MentorRequest) -> MentorBriefing:
    return build_briefing(request)


@app.post("/ingest", response_model=IngestResult)
def ingest(request: IngestRequest) -> dict:
    return ingest_directory(request.directory, request.collection_name)
