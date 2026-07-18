"""FastAPI application entry point for Knovara."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from chat import ChatRequest, ChatResponse, answer_question
from config import CORS_ORIGINS, OPENAI_API_KEY, OPENAI_CHAT_MODEL
from ingest import IngestRequest, ingest_directory
from mentor import MentorBriefing, MentorRequest, build_briefing
from models import IngestResult
from projects import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    create_project,
    delete_project,
    get_project,
    init_project_store,
    list_projects,
    set_project_ingest_status,
    update_project,
)
from retrieval import (
    CollectionDetail,
    IndexStatus,
    SourceChunk,
    delete_collection,
    get_collection_detail,
    get_index_status,
    search_sources,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_project_store()
    yield


app = FastAPI(
    title="Knovara API",
    version="0.1.0",
    description="Technical onboarding copilot demo API.",
    lifespan=lifespan,
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


@app.get("/index/status", response_model=IndexStatus)
def index_status() -> IndexStatus:
    return get_index_status()


@app.get("/projects", response_model=list[Project])
def projects() -> list[Project]:
    return list_projects()


@app.post("/projects", response_model=Project)
def project_create(request: ProjectCreate) -> Project:
    try:
        return create_project(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/projects/{project_id}", response_model=Project)
def project_detail(project_id: int) -> Project:
    try:
        return get_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.patch("/projects/{project_id}", response_model=Project)
def project_update(project_id: int, request: ProjectUpdate) -> Project:
    try:
        return update_project(project_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/projects/{project_id}", status_code=204)
def project_delete(project_id: int) -> None:
    try:
        delete_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return answer_question(request)


@app.post("/mentor", response_model=MentorBriefing)
def mentor(request: MentorRequest) -> MentorBriefing:
    return build_briefing(request)


@app.post("/ingest", response_model=IngestResult)
def ingest(request: IngestRequest) -> dict:
    try:
        return ingest_directory(request.directory, request.collection_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/projects/{project_id}/ingest", response_model=IngestResult)
def project_ingest(project_id: int) -> dict:
    try:
        project = get_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    set_project_ingest_status(project_id, "ingesting")
    try:
        result = ingest_directory(project.source_path, project.collection_name)
    except RuntimeError as exc:
        set_project_ingest_status(project_id, "failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_project_ingest_status(project_id, "failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    set_project_ingest_status(project_id, "ingested")
    return result


@app.delete("/collections/{collection_name}", response_model=IndexStatus)
def clear_collection(collection_name: str) -> IndexStatus:
    return delete_collection(collection_name)


@app.get("/collections/{collection_name}", response_model=CollectionDetail)
def collection_detail(collection_name: str) -> CollectionDetail:
    return get_collection_detail(collection_name)
