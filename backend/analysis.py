"""Project knowledge analysis for onboarding-oriented overviews."""

import re
from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from config import BACKEND_DIR
from ingest import load_files
from models import Document
from projects import Project


class ProjectOverview(BaseModel):
    """Deterministic project overview derived from local project sources."""

    project_id: int
    project_name: str
    source_path: str
    summary: str
    source_count: int
    source_files: list[str]
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

    directory = _resolve_source_path(project.source_path)
    documents = load_files(str(directory))
    source_files = [_relative_source(document) for document in documents]

    return ProjectOverview(
        project_id=project.id,
        project_name=project.name,
        source_path=project.source_path,
        summary=_summary(project, documents),
        source_count=len(documents),
        source_files=source_files[:12],
        technologies=_technologies(documents),
        topics=_topics(documents),
        components=_components(documents),
        ownership=_ownership(documents),
        decisions=_decisions(documents),
        learning_path=_learning_path(documents),
        starter_questions=_starter_questions(project, documents),
    )


def _resolve_source_path(source_path: str) -> Path:
    path = Path(source_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (BACKEND_DIR / path).resolve()


def _summary(project: Project, documents: list[Document]) -> str:
    readme = _find_document(documents, "readme")
    source = readme or (documents[0] if documents else None)
    paragraph = _first_paragraph(source.content) if source else ""
    if paragraph:
        return paragraph
    return f"{project.name} has {len(documents)} indexed source files ready for onboarding."


def _technologies(documents: list[Document]) -> list[str]:
    extensions = {
        document.metadata.get("extension", "")
        for document in documents
        if document.metadata.get("extension")
    }
    technologies = [
        TECHNOLOGY_BY_EXTENSION[extension]
        for extension in sorted(extensions)
        if extension in TECHNOLOGY_BY_EXTENSION
    ]
    return technologies or ["Project documentation"]


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
