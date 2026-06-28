"""
Pydantic data models.

This file defines the typed data contracts used by the ingestion pipeline,
including raw source documents, tokenized chunks, and ingestion result
summaries.
"""
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Raw file content and source metadata loaded from disk."""

    content: str
    metadata: dict[str, str]


class Chunk(BaseModel):
    """Token-bounded document fragment with inherited source metadata."""

    content: str
    metadata: dict[str, str]
    token_count: int = Field(ge=0)
    chunk_index: int = Field(ge=0)


class IngestResult(BaseModel):
    """Summary returned after a directory has been ingested into Chroma."""

    files_processed: int = Field(ge=0)
    chunks_created: int = Field(ge=0)
    collection_name: str
