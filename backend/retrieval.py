"""Retrieval abstractions used by the demo and indexed API paths."""

import logging

import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI
from pydantic import BaseModel

from config import (
    CHROMA_PERSIST_DIR,
    DEFAULT_COLLECTION,
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
)


logger = logging.getLogger(__name__)


class SourceChunk(BaseModel):
    title: str
    source: str
    content: str
    relevance: str | None = None
    score: float | None = None


class CollectionStatus(BaseModel):
    name: str
    count: int
    sample_sources: list[str]


class IndexStatus(BaseModel):
    persist_dir: str
    default_collection: str
    openai_configured: bool
    collections: list[CollectionStatus]


DEMO_KNOWLEDGE = [
    SourceChunk(
        title="Architecture Overview",
        source="docs/architecture.md",
        content="Service boundaries, ownership, dependencies, and deployment topology.",
    ),
    SourceChunk(
        title="Onboarding Playbook",
        source="docs/onboarding.md",
        content="First-week setup, review norms, local development, and team rituals.",
    ),
    SourceChunk(
        title="Decision Records",
        source="docs/decisions/",
        content="Design tradeoffs, migration history, and technical rationale.",
    ),
]


def search_sources(
    query: str,
    collection_name: str = DEFAULT_COLLECTION,
    limit: int = 3,
) -> list[SourceChunk]:
    """Return indexed source chunks, falling back to representative demo chunks."""

    if OPENAI_API_KEY:
        indexed_sources = _search_chroma(query, collection_name, limit)
        if indexed_sources:
            return indexed_sources

    return _search_demo_sources(query, limit)


def get_index_status() -> IndexStatus:
    """Return available Chroma collections and whether live embeddings are configured."""

    collections: list[CollectionStatus] = []

    try:
        chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        for collection in chroma_client.list_collections():
            name = collection.name if hasattr(collection, "name") else str(collection)
            current = chroma_client.get_collection(name=name)
            collections.append(
                CollectionStatus(
                    name=name,
                    count=current.count(),
                    sample_sources=_peek_sources(current),
                )
            )
    except Exception as exc:
        logger.info("Chroma status unavailable: %s", exc)

    return IndexStatus(
        persist_dir=CHROMA_PERSIST_DIR,
        default_collection=DEFAULT_COLLECTION,
        openai_configured=bool(OPENAI_API_KEY),
        collections=collections,
    )


def delete_collection(collection_name: str) -> IndexStatus:
    """Delete a Chroma collection if it exists and return refreshed index status."""

    chroma_client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception as exc:
        logger.info("Collection delete skipped for %s: %s", collection_name, exc)

    return get_index_status()


def _search_demo_sources(query: str, limit: int) -> list[SourceChunk]:
    """Return representative fallback source chunks for the current demo query."""

    terms = {term.lower() for term in query.split() if len(term) > 2}
    ranked = sorted(
        DEMO_KNOWLEDGE,
        key=lambda chunk: sum(term in chunk.content.lower() for term in terms),
        reverse=True,
    )
    return ranked[:limit]


def _search_chroma(query: str, collection_name: str, limit: int) -> list[SourceChunk]:
    """Search a Chroma collection using OpenAI query embeddings."""

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        embedding = client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=query,
        ).data[0].embedding

        chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collection = chroma_client.get_collection(name=collection_name)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.info("Chroma retrieval unavailable; using demo sources: %s", exc)
        return []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks: list[SourceChunk] = []
    for index, content in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        source = metadata.get("file_path", "indexed-source")
        filename = metadata.get("filename") or source
        chunks.append(
            SourceChunk(
                title=filename,
                source=source,
                content=content,
                relevance=_summarize_relevance(content),
                score=distance,
            )
        )

    return chunks


def _summarize_relevance(content: str) -> str:
    compact = " ".join(content.split())
    return compact[:180] + ("..." if len(compact) > 180 else "")


def _peek_sources(collection) -> list[str]:
    try:
        peek = collection.peek(limit=8)
    except Exception:
        return []

    sources: list[str] = []
    for metadata in peek.get("metadatas", []) or []:
        if not metadata:
            continue
        source = metadata.get("file_path") or metadata.get("filename")
        if source and source not in sources:
            sources.append(source)

    return sources[:5]
