from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
import chat as chat_module
import main

from ingest import chunk_documents, load_files
from main import app
from models import Document
from repositories import analyze_repository_structure, normalize_github_url
from retrieval import CollectionDetail, SourceChunk, SourcePreview


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


def test_index_status_returns_collections_shape() -> None:
    response = client.get("/index/status")

    assert response.status_code == 200
    body = response.json()
    assert "default_collection" in body
    assert "openai_configured" in body
    assert isinstance(body["collections"], list)


def test_project_crud_flow() -> None:
    collection_name = f"test_{uuid4().hex[:8]}"
    create_response = client.post(
        "/projects",
        json={
            "name": "Test Project",
            "collection_name": collection_name,
            "source_path": "../example_data",
        },
    )

    assert create_response.status_code == 200
    project = create_response.json()
    assert project["name"] == "Test Project"
    assert project["source_type"] == "local"
    assert project["repository_url"] is None
    assert project["ingest_status"] == "not_ingested"

    list_response = client.get("/projects")
    assert list_response.status_code == 200
    assert any(item["id"] == project["id"] for item in list_response.json())

    update_response = client.patch(
        f"/projects/{project['id']}",
        json={"name": "Updated Project"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Project"

    delete_response = client.delete(f"/projects/{project['id']}")
    assert delete_response.status_code == 204


def test_project_edit_resets_ingest_status_when_index_scope_changes() -> None:
    collection_name = f"edit_{uuid4().hex[:8]}"
    project = client.post(
        "/projects",
        json={
            "name": "Editable Project",
            "collection_name": collection_name,
            "source_path": "../example_data",
        },
    ).json()

    status_response = client.patch(
        f"/projects/{project['id']}",
        json={"ingest_status": "ingested"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["ingest_status"] == "ingested"

    update_response = client.patch(
        f"/projects/{project['id']}",
        json={"source_path": "../example_data/subset"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["ingest_status"] == "not_ingested"

    client.delete(f"/projects/{project['id']}")


def test_project_overview_extracts_onboarding_context() -> None:
    collection_name = f"overview_{uuid4().hex[:8]}"
    project = client.post(
        "/projects",
        json={
            "name": "Overview Project",
            "collection_name": collection_name,
            "source_path": str(REPO_ROOT / "example_data"),
        },
    ).json()

    response = client.get(f"/projects/{project['id']}/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "Overview Project"
    assert body["source_type"] == "local"
    assert body["source_count"] >= 5
    assert "main.py" in body["repository_structure"]["entry_points"]
    assert "Markdown documentation" in body["technologies"]
    assert any("gateway" in item.lower() for item in body["components"])
    assert any("platform" in item.lower() for item in body["ownership"])
    assert any("ADR-001" in item for item in body["decisions"])
    assert len(body["learning_path"]) >= 3
    assert len(body["starter_questions"]) == 4

    client.delete(f"/projects/{project['id']}")


def test_project_create_accepts_github_repository_url() -> None:
    collection_name = f"github_{uuid4().hex[:8]}"
    create_response = client.post(
        "/projects",
        json={
            "name": "GitHub Project",
            "collection_name": collection_name,
            "source_type": "github",
            "source_path": "https://github.com/openai/openai-python",
        },
    )

    assert create_response.status_code == 200
    project = create_response.json()
    assert project["source_type"] == "github"
    assert project["source_path"] == "https://github.com/openai/openai-python.git"
    assert project["repository_url"] == "https://github.com/openai/openai-python.git"

    client.delete(f"/projects/{project['id']}")


def test_project_create_rejects_invalid_github_repository_url() -> None:
    collection_name = f"bad_github_{uuid4().hex[:8]}"
    response = client.post(
        "/projects",
        json={
            "name": "Invalid GitHub Project",
            "collection_name": collection_name,
            "source_type": "github",
            "source_path": "https://example.com/not-github/repo",
        },
    )

    assert response.status_code == 400
    assert "GitHub" in response.json()["detail"]


def test_project_ingest_resolves_github_checkout(monkeypatch) -> None:
    collection_name = f"github_ingest_{uuid4().hex[:8]}"
    project = client.post(
        "/projects",
        json={
            "name": "GitHub Ingest Project",
            "collection_name": collection_name,
            "source_type": "github",
            "source_path": "https://github.com/openai/openai-python",
        },
    ).json()

    def fake_resolve_project_source_path(
        source_type: str,
        source_path: str,
        repository_url: str | None,
    ) -> Path:
        assert source_type == "github"
        assert source_path == "https://github.com/openai/openai-python.git"
        assert repository_url == "https://github.com/openai/openai-python.git"
        return REPO_ROOT / "example_data"

    def fake_ingest_directory(directory: str, collection_name: str) -> dict:
        assert directory == str(REPO_ROOT / "example_data")
        return {
            "files_processed": 3,
            "chunks_created": 4,
            "collection_name": collection_name,
        }

    monkeypatch.setattr(main, "resolve_project_source_path", fake_resolve_project_source_path)
    monkeypatch.setattr(main, "ingest_directory", fake_ingest_directory)

    response = client.post(f"/projects/{project['id']}/ingest")

    assert response.status_code == 200
    assert response.json()["collection_name"] == collection_name

    client.delete(f"/projects/{project['id']}")


def test_project_overview_reports_missing_source_path() -> None:
    collection_name = f"missing_{uuid4().hex[:8]}"
    project = client.post(
        "/projects",
        json={
            "name": "Missing Source Project",
            "collection_name": collection_name,
            "source_path": "./does-not-exist",
        },
    ).json()

    response = client.get(f"/projects/{project['id']}/overview")

    assert response.status_code == 400
    assert "Directory does not exist" in response.json()["detail"]

    client.delete(f"/projects/{project['id']}")


def test_github_url_normalization_supports_https_and_ssh() -> None:
    assert (
        normalize_github_url("https://github.com/openai/openai-python")
        == "https://github.com/openai/openai-python.git"
    )
    assert (
        normalize_github_url("git@github.com:openai/openai-python.git")
        == "https://github.com/openai/openai-python.git"
    )


def test_repository_structure_extracts_key_files() -> None:
    structure = analyze_repository_structure(REPO_ROOT / "example_data")

    assert "main.py" in structure.entry_points
    assert "README.md" in structure.documentation_files
    assert "Python" in structure.languages
    assert "main.py" in structure.key_files


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
    assert body["mode"] in {"demo", "indexed", "demo+llm", "indexed+llm"}


def test_chat_reports_indexed_mode_when_retrieval_has_scores(monkeypatch) -> None:
    def fake_search_sources(query: str, collection_name: str = "seets"):
        return [
            SourceChunk(
                title="runbook.md",
                source="example_data/runbook.md",
                content="Gateway retries use bounded exponential backoff.",
                relevance="Gateway retries use bounded exponential backoff.",
                score=0.12,
            )
        ]

    monkeypatch.setattr(chat_module, "search_sources", fake_search_sources)

    response = client.post(
        "/chat",
        json={
            "question": "Who owns gateway retry behavior?",
            "role": "Backend Engineer",
            "team": "Platform",
            "collection_name": "seets",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "indexed"
    assert body["citations"][0]["score"] == 0.12


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


def test_ingest_endpoint_returns_clear_error(monkeypatch) -> None:
    def fake_ingest_directory(directory: str, collection_name: str) -> dict:
        raise RuntimeError("OPENAI_API_KEY is required to embed and store chunks.")

    monkeypatch.setattr(main, "ingest_directory", fake_ingest_directory)

    response = client.post(
        "/ingest",
        json={"directory": "../example_data", "collection_name": "seets"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "OPENAI_API_KEY is required to embed and store chunks."


def test_project_ingest_updates_status(monkeypatch) -> None:
    collection_name = f"ingest_{uuid4().hex[:8]}"
    project = client.post(
        "/projects",
        json={
            "name": "Ingest Project",
            "collection_name": collection_name,
            "source_path": "../example_data",
        },
    ).json()

    def fake_ingest_directory(directory: str, collection_name: str) -> dict:
        return {
            "files_processed": 7,
            "chunks_created": 8,
            "collection_name": collection_name,
        }

    monkeypatch.setattr(main, "ingest_directory", fake_ingest_directory)

    response = client.post(f"/projects/{project['id']}/ingest")

    assert response.status_code == 200
    assert response.json()["collection_name"] == collection_name

    detail = client.get(f"/projects/{project['id']}").json()
    assert detail["ingest_status"] == "ingested"

    client.delete(f"/projects/{project['id']}")


def test_collection_detail_endpoint_returns_preview(monkeypatch) -> None:
    def fake_get_collection_detail(collection_name: str) -> CollectionDetail:
        return CollectionDetail(
            name=collection_name,
            count=1,
            chunks=[
                SourcePreview(
                    title="runbook.md",
                    source="example_data/runbook.md",
                    content="Retries use bounded exponential backoff.",
                    chunk_index="0",
                )
            ],
        )

    monkeypatch.setattr(main, "get_collection_detail", fake_get_collection_detail)

    response = client.get("/collections/seets")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "seets"
    assert body["chunks"][0]["title"] == "runbook.md"


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
