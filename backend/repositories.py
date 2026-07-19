"""Repository source handling and structure analysis."""

import hashlib
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel

from config import BACKEND_DIR, REPOSITORY_CACHE_DIR


GITHUB_HTTPS_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_SSH_PATTERN = re.compile(
    r"^git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?$"
)

IGNORED_DIRECTORIES = {
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "out",
}

LANGUAGE_BY_EXTENSION = {
    ".css": "CSS",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "React / JavaScript",
    ".md": "Markdown",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".ts": "TypeScript",
    ".tsx": "React / TypeScript",
}

ENTRYPOINT_NAMES = {
    "app.py",
    "index.js",
    "index.ts",
    "main.go",
    "main.py",
    "main.rs",
    "manage.py",
    "package.json",
    "pyproject.toml",
    "server.js",
}


class RepositoryStructure(BaseModel):
    """High-signal repository structure for onboarding."""

    root_path: str
    top_level_directories: list[str]
    key_files: list[str]
    documentation_files: list[str]
    test_files: list[str]
    entry_points: list[str]
    languages: list[str]


def is_github_url(value: str) -> bool:
    """Return whether a value is a supported GitHub repository URL."""

    return bool(GITHUB_HTTPS_PATTERN.match(value.strip()) or GITHUB_SSH_PATTERN.match(value.strip()))


def normalize_github_url(value: str) -> str:
    """Normalize supported GitHub URLs to cloneable HTTPS URLs."""

    candidate = value.strip()
    https_match = GITHUB_HTTPS_PATTERN.match(candidate)
    ssh_match = GITHUB_SSH_PATTERN.match(candidate)
    match = https_match or ssh_match
    if not match:
        raise ValueError("Repository URL must be a GitHub HTTPS or SSH repository URL.")

    owner = match.group("owner")
    repo = match.group("repo").removesuffix(".git")
    return f"https://github.com/{owner}/{repo}.git"


def ensure_repository_checkout(repository_url: str) -> Path:
    """Clone a GitHub repository into the managed cache if needed."""

    normalized_url = normalize_github_url(repository_url)
    checkout_path = _checkout_path(normalized_url)

    if (checkout_path / ".git").exists():
        return checkout_path

    checkout_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", normalized_url, str(checkout_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(f"Unable to clone repository: {message}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Timed out while cloning repository.") from exc

    return checkout_path


def resolve_project_source_path(source_type: str, source_path: str, repository_url: str | None) -> Path:
    """Resolve a local or GitHub project source into a readable local directory."""

    if source_type == "github":
        return ensure_repository_checkout(repository_url or source_path)

    path = Path(source_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (BACKEND_DIR / path).resolve()


def analyze_repository_structure(root: Path) -> RepositoryStructure:
    """Extract repository structure signals useful for first-pass onboarding."""

    top_level_directories = sorted(
        item.name
        for item in root.iterdir()
        if item.is_dir() and item.name not in IGNORED_DIRECTORIES
    )[:12]
    files = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and not _has_ignored_part(path)
    ]
    relative_files = [_relative(root, path) for path in files]

    documentation_files = [
        value
        for value in relative_files
        if Path(value).suffix.lower() in {".md", ".txt"} or "docs/" in value.lower()
    ][:12]
    test_files = [
        value
        for value in relative_files
        if _looks_like_test_file(value)
    ][:12]
    entry_points = [
        value
        for value in relative_files
        if Path(value).name in ENTRYPOINT_NAMES or value.endswith("/app/page.tsx")
    ][:12]
    key_files = _dedupe(entry_points + documentation_files + test_files + relative_files[:12])[:16]
    languages = _languages(files)

    return RepositoryStructure(
        root_path=str(root),
        top_level_directories=top_level_directories,
        key_files=key_files,
        documentation_files=documentation_files,
        test_files=test_files,
        entry_points=entry_points,
        languages=languages,
    )


def _checkout_path(repository_url: str) -> Path:
    digest = hashlib.sha256(repository_url.encode("utf-8")).hexdigest()[:12]
    parsed = urlparse(repository_url)
    repo_name = Path(parsed.path).name.removesuffix(".git") or "repository"
    cache_root = Path(REPOSITORY_CACHE_DIR)
    if not cache_root.is_absolute():
        cache_root = BACKEND_DIR / cache_root
    return cache_root / f"{repo_name}-{digest}"


def _has_ignored_part(path: Path) -> bool:
    return any(part in IGNORED_DIRECTORIES for part in path.parts)


def _looks_like_test_file(value: str) -> bool:
    lowered = value.lower()
    name = Path(lowered).name
    return (
        "/test" in lowered
        or "/tests/" in lowered
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.ts")
        or name.endswith(".test.tsx")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.tsx")
    )


def _languages(files: list[Path]) -> list[str]:
    counts: dict[str, int] = {}
    for path in files:
        language = LANGUAGE_BY_EXTENSION.get(path.suffix.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1
    return [
        language
        for language, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ][:8]


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
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
