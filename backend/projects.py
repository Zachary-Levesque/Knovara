"""SQLite-backed project metadata store for Knovara."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from config import BACKEND_DIR, DEFAULT_COLLECTION, SQLITE_DB_PATH
from repositories import is_github_url, normalize_github_url


class ProjectCreate(BaseModel):
    name: str = Field(default="Seets Sensor Mesh", max_length=120)
    collection_name: str = Field(default=DEFAULT_COLLECTION, max_length=80)
    source_path: str = Field(default="../example_data", max_length=500)
    source_type: str = Field(default="local", max_length=20)
    repository_url: str | None = Field(default=None, max_length=500)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        if value not in {"local", "github"}:
            raise ValueError("source_type must be local or github.")
        return value

    @field_validator("repository_url")
    @classmethod
    def validate_repository_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return normalize_github_url(value)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    collection_name: str | None = Field(default=None, max_length=80)
    source_path: str | None = Field(default=None, max_length=500)
    source_type: str | None = Field(default=None, max_length=20)
    repository_url: str | None = Field(default=None, max_length=500)
    ingest_status: str | None = Field(default=None, max_length=40)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str | None) -> str | None:
        if value is not None and value not in {"local", "github"}:
            raise ValueError("source_type must be local or github.")
        return value

    @field_validator("repository_url")
    @classmethod
    def validate_repository_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return normalize_github_url(value)


class Project(BaseModel):
    id: int
    name: str
    collection_name: str
    source_path: str
    source_type: str = "local"
    repository_url: str | None = None
    ingest_status: str
    created_at: str
    updated_at: str


def init_project_store() -> None:
    """Create project metadata tables and seed the default demo project."""

    with _connect() as connection:
        connection.execute(
            """
            create table if not exists projects (
                id integer primary key autoincrement,
                name text not null,
                collection_name text not null unique,
                source_path text not null,
                source_type text not null default 'local',
                repository_url text,
                ingest_status text not null,
                created_at text not null,
                updated_at text not null
            )
            """
        )
        _ensure_column(connection, "source_type", "text not null default 'local'")
        _ensure_column(connection, "repository_url", "text")
        count = connection.execute("select count(*) from projects").fetchone()[0]
        if count == 0:
            now = _now()
            connection.execute(
                """
                insert into projects
                    (name, collection_name, source_path, source_type, repository_url, ingest_status, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Seets Sensor Mesh",
                    DEFAULT_COLLECTION,
                    "../example_data",
                    "local",
                    None,
                    "not_ingested",
                    now,
                    now,
                ),
            )


def list_projects() -> list[Project]:
    with _connect() as connection:
        rows = connection.execute("select * from projects order by created_at desc").fetchall()
    return [_project_from_row(row) for row in rows]


def get_project(project_id: int) -> Project:
    with _connect() as connection:
        row = connection.execute("select * from projects where id = ?", (project_id,)).fetchone()
    if row is None:
        raise KeyError(f"Project not found: {project_id}")
    return _project_from_row(row)


def create_project(request: ProjectCreate) -> Project:
    source_type, source_path, repository_url = _normalize_source(
        request.source_type,
        request.source_path,
        request.repository_url,
    )
    now = _now()
    with _connect() as connection:
        cursor = connection.execute(
            """
            insert into projects
                (name, collection_name, source_path, source_type, repository_url, ingest_status, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.name,
                request.collection_name,
                source_path,
                source_type,
                repository_url,
                "not_ingested",
                now,
                now,
            ),
        )
        project_id = int(cursor.lastrowid)
    return get_project(project_id)


def update_project(project_id: int, request: ProjectUpdate) -> Project:
    existing = get_project(project_id)
    updates = request.model_dump(exclude_none=True)
    if not updates:
        return existing
    source_type, source_path, repository_url = _normalize_source(
        updates.get("source_type", existing.source_type),
        updates.get("source_path", existing.source_path),
        updates.get("repository_url", existing.repository_url),
    )
    if "source_type" in updates or "source_path" in updates or "repository_url" in updates:
        updates["source_type"] = source_type
        updates["source_path"] = source_path
        updates["repository_url"] = repository_url

    if (
        {"collection_name", "source_path", "source_type", "repository_url"} & updates.keys()
        and "ingest_status" not in updates
    ):
        updates["ingest_status"] = "not_ingested"

    assignments = [f"{key} = ?" for key in updates]
    values = list(updates.values())
    assignments.append("updated_at = ?")
    values.append(_now())
    values.append(project_id)

    with _connect() as connection:
        connection.execute(
            f"update projects set {', '.join(assignments)} where id = ?",
            values,
        )
    return get_project(project_id)


def delete_project(project_id: int) -> None:
    with _connect() as connection:
        cursor = connection.execute("delete from projects where id = ?", (project_id,))
    if cursor.rowcount == 0:
        raise KeyError(f"Project not found: {project_id}")


def set_project_ingest_status(project_id: int, status: str) -> Project:
    return update_project(project_id, ProjectUpdate(ingest_status=status))


def _connect() -> sqlite3.Connection:
    path = Path(SQLITE_DB_PATH)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _project_from_row(row: sqlite3.Row) -> Project:
    return Project(
        id=row["id"],
        name=row["name"],
        collection_name=row["collection_name"],
        source_path=row["source_path"],
        source_type=row["source_type"],
        repository_url=row["repository_url"],
        ingest_status=row["ingest_status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_column(connection: sqlite3.Connection, name: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute("pragma table_info(projects)").fetchall()
    }
    if name not in columns:
        connection.execute(f"alter table projects add column {name} {definition}")


def _normalize_source(
    source_type: str | None,
    source_path: str,
    repository_url: str | None,
) -> tuple[str, str, str | None]:
    if source_type == "github" or is_github_url(source_path):
        normalized_url = normalize_github_url(repository_url or source_path)
        return "github", normalized_url, normalized_url
    return "local", source_path, None


init_project_store()
