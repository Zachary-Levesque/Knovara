"""SQLite-backed project metadata store for Knovara."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from config import BACKEND_DIR, DEFAULT_COLLECTION, SQLITE_DB_PATH


class ProjectCreate(BaseModel):
    name: str = Field(default="Seets Sensor Mesh", max_length=120)
    collection_name: str = Field(default=DEFAULT_COLLECTION, max_length=80)
    source_path: str = Field(default="../example_data", max_length=500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    collection_name: str | None = Field(default=None, max_length=80)
    source_path: str | None = Field(default=None, max_length=500)
    ingest_status: str | None = Field(default=None, max_length=40)


class Project(BaseModel):
    id: int
    name: str
    collection_name: str
    source_path: str
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
                ingest_status text not null,
                created_at text not null,
                updated_at text not null
            )
            """
        )
        count = connection.execute("select count(*) from projects").fetchone()[0]
        if count == 0:
            now = _now()
            connection.execute(
                """
                insert into projects
                    (name, collection_name, source_path, ingest_status, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    "Seets Sensor Mesh",
                    DEFAULT_COLLECTION,
                    "../example_data",
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
    now = _now()
    with _connect() as connection:
        cursor = connection.execute(
            """
            insert into projects
                (name, collection_name, source_path, ingest_status, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                request.name,
                request.collection_name,
                request.source_path,
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
        ingest_status=row["ingest_status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


init_project_store()
