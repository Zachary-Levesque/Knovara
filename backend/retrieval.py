"""Lightweight retrieval abstractions used by the demo API."""

from pydantic import BaseModel


class SourceChunk(BaseModel):
    title: str
    source: str
    content: str


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


def search_sources(query: str) -> list[SourceChunk]:
    """Return representative source chunks for the current demo query."""

    terms = {term.lower() for term in query.split() if len(term) > 2}
    ranked = sorted(
        DEMO_KNOWLEDGE,
        key=lambda chunk: sum(term in chunk.content.lower() for term in terms),
        reverse=True,
    )
    return ranked[:3]
