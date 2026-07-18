from pathlib import Path

from fastapi.testclient import TestClient
import main

from ingest import chunk_documents, load_files
from main import app
from models import Document


client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_health_reports_demo_mode_without_api_key() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "chat_model" in body


def test_sources_returns_demo_chunks() -> None:
    response = client.get("/sources", params={"query": "architecture decisions"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert {"title", "source", "content"} <= set(body[0])


def test_chat_returns_answer_with_citations() -> None:
    response = client.post(
        "/chat",
        json={
            "question": "What should I read before my first backend change?",
            "role": "Backend Engineer",
            "team": "Platform",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "Backend Engineer" in body["answer"]
    assert len(body["citations"]) == 3


def test_ingest_endpoint_returns_summary(monkeypatch) -> None:
    def fake_ingest_directory(directory: str, collection_name: str) -> dict:
        return {
            "files_processed": 3,
            "chunks_created": 4,
            "collection_name": collection_name,
        }

    monkeypatch.setattr(main, "ingest_directory", fake_ingest_directory)

    response = client.post(
        "/ingest",
        json={"directory": "../example_data", "collection_name": "seets"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "files_processed": 3,
        "chunks_created": 4,
        "collection_name": "seets",
    }


def test_mentor_returns_first_week_plan() -> None:
    response = client.post(
        "/mentor",
        json={
            "name": "Avery",
            "role": "Software Engineer",
            "team": "Platform",
            "background": "Backend services",
            "goal": "Ship a small change",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["headline"] == "Avery's ramp-up path for Platform"
    assert len(body["first_week"]) == 3


def test_chunk_documents_splits_supported_content() -> None:
    chunks = chunk_documents(
        [
            Document(
                content="Architecture decisions and onboarding context.",
                metadata={"file_path": "docs/example.md"},
            )
        ]
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].token_count > 0


def test_load_files_reads_supported_example_data() -> None:
    documents = load_files(str(REPO_ROOT / "example_data"))

    assert len(documents) >= 3
    assert {document.metadata["extension"] for document in documents} <= {
        ".md",
        ".py",
    }
