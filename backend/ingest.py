"""
Chunking and embedding pipeline.

This file loads supported source files from disk, splits them into token-bounded
chunks, embeds each chunk with Gemini, stores the vectors in Chroma, and exposes
a CLI entrypoint for running ingestion end to end.
"""
import argparse
import hashlib
import json
from pathlib import Path

import chromadb
from google import genai
from google.genai import types
import tiktoken
from chromadb.config import Settings as ChromaSettings

from config import CHROMA_PERSIST_DIR, GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL
from models import Chunk, Document, IngestResult


SUPPORTED_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
}
MAX_CHUNK_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
TOKEN_ENCODING = "cl100k_base"


def load_files(directory: str) -> list[Document]:
    """Recursively load supported files from a directory into documents."""
    root = Path(directory).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    documents: list[Document] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="replace")

        documents.append(
            Document(
                content=content,
                metadata={
                    "file_path": str(path),
                    "extension": path.suffix.lower(),
                    "filename": path.name,
                },
            )
        )

    return documents


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    """Split documents into chunks of up to 500 tokens with 50-token overlap."""
    encoding = tiktoken.get_encoding(TOKEN_ENCODING)
    chunks: list[Chunk] = []

    for document in documents:
        tokens = encoding.encode(document.content)
        if not tokens:
            continue

        start = 0
        chunk_index = 0
        while start < len(tokens):
            end = min(start + MAX_CHUNK_TOKENS, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = encoding.decode(chunk_tokens)
            metadata = {
                **document.metadata,
                "chunk_index": str(chunk_index),
                "token_start": str(start),
                "token_end": str(end),
            }
            chunks.append(
                Chunk(
                    content=chunk_text,
                    metadata=metadata,
                    token_count=len(chunk_tokens),
                    chunk_index=chunk_index,
                )
            )

            if end == len(tokens):
                break

            start = end - CHUNK_OVERLAP_TOKENS
            chunk_index += 1

    return chunks


def embed_and_store(chunks: list[Chunk], collection_name: str) -> None:
    """Embed chunks with Gemini and persist them in a Chroma collection."""
    if not chunks:
        return

    client = genai.Client(api_key=GEMINI_API_KEY)

    chroma_client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    collection = chroma_client.get_or_create_collection(name=collection_name)

    embeddings = []
    for chunk in chunks:
        result = client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=chunk.content,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        embeddings.append(result.embeddings[0].values)

    ids = [_chunk_id(chunk, collection_name) for chunk in chunks]
    collection.upsert(
        ids=ids,
        documents=[chunk.content for chunk in chunks],
        embeddings=embeddings,
        metadatas=[chunk.metadata for chunk in chunks],
    )


def ingest_directory(directory: str, collection_name: str) -> dict:
    """Load, chunk, embed, and store a directory, then return a summary."""
    documents = load_files(directory)
    chunks = chunk_documents(documents)
    embed_and_store(chunks, collection_name)
    return IngestResult(
        files_processed=len(documents),
        chunks_created=len(chunks),
        collection_name=collection_name,
    ).model_dump()


def _chunk_id(chunk: Chunk, collection_name: str) -> str:
    source = "|".join(
        [
            collection_name,
            chunk.metadata["file_path"],
            str(chunk.chunk_index),
            chunk.content,
        ]
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest files into Chroma.")
    parser.add_argument("--dir", required=True, help="Directory of files to ingest.")
    parser.add_argument(
        "--collection",
        required=True,
        help="Chroma collection name to create or update.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = ingest_directory(args.dir, args.collection)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()