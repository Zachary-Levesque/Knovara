"""Project knowledge analysis for onboarding-oriented overviews."""

import json
import re
from collections import Counter
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel

from config import BACKEND_DIR, OPENAI_API_KEY, OPENAI_CHAT_MODEL
from ingest import load_files
from models import Document
from projects import Project
from repositories import (
    RepositoryActivity,
    RepositoryStructure,
    analyze_repository_activity,
    analyze_repository_structure,
    resolve_project_source_path,
)


class ProjectOverview(BaseModel):
    """Deterministic project overview derived from local project sources."""

    project_id: int
    project_name: str
    source_path: str
    source_type: str
    repository_url: str | None = None
    mode: str = "deterministic"
    summary: str
    source_count: int
    source_files: list[str]
    repository_structure: RepositoryStructure
    repository_activity: RepositoryActivity
    technologies: list[str]
    topics: list[str]
    components: list[str]
    ownership: list[str]
    decisions: list[str]
    learning_path: list[str]
    starter_questions: list[str]


STOPWORDS = {
    "about",
    "across",
    "after",
    "before",
    "between",
    "cloud",
    "company",
    "data",
    "does",
    "engineer",
    "engineers",
    "first",
    "from",
    "into",
    "local",
    "project",
    "should",
    "system",
    "team",
    "that",
    "their",
    "this",
    "through",
    "with",
}

TECHNOLOGY_BY_EXTENSION = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "React / TypeScript",
    ".md": "Markdown documentation",
    ".txt": "Text documentation",
    ".json": "JSON configuration",
    ".yaml": "YAML configuration",
    ".yml": "YAML configuration",
}


def build_project_overview(project: Project) -> ProjectOverview:
    """Build a concise overview of what matters in a project."""

    directory = resolve_project_source_path(
        project.source_type,
        project.source_path,
        project.repository_url,
    )
    documents = load_files(str(directory))
    source_files = [_relative_source(document) for document in documents]
    repository_structure = analyze_repository_structure(directory)
    repository_activity = analyze_repository_activity(directory)

    deterministic = ProjectOverview(
        project_id=project.id,
        project_name=project.name,
        source_path=project.source_path,
        source_type=project.source_type,
        repository_url=project.repository_url,
        mode="deterministic",
        summary=_summary(project, documents),
        source_count=len(documents),
        source_files=source_files[:12],
        repository_structure=repository_structure,
        repository_activity=repository_activity,
        technologies=_technologies(documents, repository_structure),
        topics=_topics(documents),
        components=_components(documents),
        ownership=_ownership(documents),
        decisions=_decisions(documents),
        learning_path=_learning_path(documents),
        starter_questions=_starter_questions(project, documents),
    )
    if OPENAI_API_KEY:
        generated = _generate_overview(project, documents, deterministic)
        if generated:
            return generated

    return deterministic


def _summary(project: Project, documents: list[Document]) -> str:
    readme = _find_document(documents, "readme")
    source = readme or (documents[0] if documents else None)
    paragraph = _first_paragraph(source.content) if source else ""
    if paragraph:
        return paragraph
    return f"{project.name} has {len(documents)} indexed source files ready for onboarding."


def _technologies(
    documents: list[Document],
    repository_structure: RepositoryStructure,
) -> list[str]:
    extensions = {
        document.metadata.get("extension", "")
        for document in documents
        if document.metadata.get("extension")
    }
    technologies = repository_structure.languages + [
        TECHNOLOGY_BY_EXTENSION[extension]
        for extension in sorted(extensions)
        if extension in TECHNOLOGY_BY_EXTENSION
    ]
    return _dedupe(technologies) or ["Project documentation"]


def _topics(documents: list[Document]) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", " ".join(document.content for document in documents))
    counts = Counter(word.lower().replace("_", "-") for word in words)
    topics = [
        topic
        for topic, _ in counts.most_common(40)
        if topic not in STOPWORDS and not topic.isdigit()
    ]
    return topics[:8]


def _components(documents: list[Document]) -> list[str]:
    architecture = _find_document(documents, "architecture")
    candidates = _bullet_lines(architecture.content if architecture else "")
    if candidates:
        return candidates[:6]

    headings = [
        heading
        for document in documents
        for heading in _headings(document.content)
        if "architecture" not in heading.lower()
    ]
    return headings[:6] or ["Read the source files to identify service boundaries."]


def _ownership(documents: list[Document]) -> list[str]:
    ownership_doc = _find_document(documents, "ownership")
    if ownership_doc:
        expert_lines = _bullet_lines(ownership_doc.content)
        prose_lines = [
            line.strip()
            for line in ownership_doc.content.splitlines()
            if " owns " in f" {line.lower()} " or "owner" in line.lower()
        ]
        ownership = prose_lines + expert_lines
        if ownership:
            return _dedupe(ownership)[:8]

    return ["Ask the project lead who owns core systems, review flow, and escalation paths."]


def _decisions(documents: list[Document]) -> list[str]:
    decision_doc = _find_document(documents, "decision") or _find_document(documents, "adr")
    if decision_doc:
        decisions = [
            heading
            for heading in _headings(decision_doc.content)
            if heading.lower().startswith("adr") or "decision" not in heading.lower()
        ]
        if decisions:
            return decisions[:8]

    headings = [
        heading
        for document in documents
        for heading in _headings(document.content)
        if "decision" in heading.lower() or heading.lower().startswith("adr")
    ]
    return headings[:8] or ["No explicit architecture decision records were found."]


def _learning_path(documents: list[Document]) -> list[str]:
    onboarding = _find_document(documents, "onboarding")
    if onboarding:
        numbered = re.findall(r"^\s*\d+\.\s+(.+)$", onboarding.content, flags=re.MULTILINE)
        if numbered:
            return [item.strip() for item in numbered[:6]]

    return [
        "Read the project overview and architecture notes.",
        "Trace one user or data workflow through the main components.",
        "Identify owners before changing cross-boundary behavior.",
        "Ship a small change with tests and review from the project owner.",
    ]


def _starter_questions(project: Project, documents: list[Document]) -> list[str]:
    topics = _topics(documents)[:3]
    topic = topics[0] if topics else project.name
    return [
        f"What should I understand first about {project.name}?",
        f"Who owns the highest-risk parts of {project.name}?",
        f"What recent decisions explain the current {topic} design?",
        "What is a good first production change for my role?",
    ]


def _generate_overview(
    project: Project,
    documents: list[Document],
    deterministic: ProjectOverview,
) -> ProjectOverview | None:
    context = _overview_context(documents, deterministic)
    prompt = (
        "Create an onboarding-focused technical project overview as JSON. "
        "Use only the provided project evidence. Return exactly these keys: "
        "summary, technologies, topics, components, ownership, decisions, learning_path, starter_questions. "
        "Lists should contain concise strings. The summary should be practical and specific.\n\n"
        f"Project: {project.name}\n"
        f"Source type: {project.source_type}\n"
        f"Repository URL: {project.repository_url or 'n/a'}\n\n"
        f"Evidence:\n{context}"
    )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are Knovara, a concise technical onboarding analyst.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        return deterministic.model_copy(
            update={
                "mode": "llm",
                "summary": _string_value(payload.get("summary"), deterministic.summary),
                "technologies": _string_list(payload.get("technologies"), deterministic.technologies),
                "topics": _string_list(payload.get("topics"), deterministic.topics),
                "components": _string_list(payload.get("components"), deterministic.components),
                "ownership": _string_list(payload.get("ownership"), deterministic.ownership),
                "decisions": _string_list(payload.get("decisions"), deterministic.decisions),
                "learning_path": _string_list(payload.get("learning_path"), deterministic.learning_path),
                "starter_questions": _string_list(
                    payload.get("starter_questions"),
                    deterministic.starter_questions,
                ),
            }
        )
    except Exception:
        return None


def _overview_context(documents: list[Document], overview: ProjectOverview) -> str:
    excerpts = []
    for document in documents[:8]:
        source = _relative_source(document)
        compact = " ".join(document.content.split())
        excerpts.append(f"Source: {source}\n{compact[:900]}")

    structure = overview.repository_structure
    activity = overview.repository_activity
    return "\n\n".join(
        [
            f"Files: {', '.join(overview.source_files)}",
            f"Languages: {', '.join(structure.languages)}",
            f"Entry points: {', '.join(structure.entry_points)}",
            f"Key files: {', '.join(structure.key_files)}",
            "Recent commits: "
            + "; ".join(
                f"{commit.sha} {commit.date} {commit.author}: {commit.message}"
                for commit in activity.recent_commits[:5]
            ),
            "Contributors: "
            + ", ".join(
                f"{contributor.name} ({contributor.commits})"
                for contributor in activity.contributors[:5]
            ),
            *excerpts,
        ]
    )


def _string_value(value: object, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _string_list(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    strings = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return strings[:10] or fallback


def _find_document(documents: list[Document], name_part: str) -> Document | None:
    needle = name_part.lower()
    for document in documents:
        filename = document.metadata.get("filename", "").lower()
        path = document.metadata.get("file_path", "").lower()
        if needle in filename or needle in path:
            return document
    return None


def _first_paragraph(content: str) -> str:
    without_headings = "\n".join(
        line for line in content.splitlines() if not line.lstrip().startswith("#")
    )
    for paragraph in re.split(r"\n\s*\n", without_headings):
        compact = " ".join(paragraph.split())
        if compact:
            return compact[:420]
    return ""


def _headings(content: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^\s*#{1,4}\s+(.+)$", content, flags=re.MULTILINE)
    ]


def _bullet_lines(content: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^\s*[-*]\s+(.+)$", content, flags=re.MULTILINE)
    ]


def _relative_source(document: Document) -> str:
    path = Path(document.metadata.get("file_path", ""))
    try:
        return str(path.relative_to(BACKEND_DIR.parent))
    except ValueError:
        return str(path)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
