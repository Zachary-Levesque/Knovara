"""
Grounded Q&A handler.

This file will coordinate retrieval and LLM calls for question answering,
ensuring responses are grounded in indexed organizational knowledge and include
the supporting context required by the frontend.
"""
from pydantic import BaseModel, Field

from retrieval import search_sources


class ChatRequest(BaseModel):
    """Question-answering request scoped to a user's onboarding context."""

    question: str = Field(min_length=3, max_length=500)
    role: str = Field(default="Software Engineer", max_length=80)
    team: str = Field(default="Platform", max_length=80)


class Citation(BaseModel):
    """Source attribution shown next to an answer."""

    title: str
    source: str
    relevance: str


class ChatResponse(BaseModel):
    """Grounded answer and source citations."""

    answer: str
    citations: list[Citation]


def answer_question(request: ChatRequest) -> ChatResponse:
    """Answer from retrieved demo sources without requiring an LLM key."""

    sources = search_sources(request.question)
    citations = [
        Citation(
            title=source.title,
            source=source.source,
            relevance=source.content,
        )
        for source in sources
    ]

    source_titles = ", ".join(source.title for source in sources)
    answer = (
        f"For a {request.role} joining {request.team}, start by reading {source_titles}. "
        "Use the architecture overview to understand service boundaries, then review "
        "onboarding norms and decision records before making your first change. "
        "Capture unclear ownership, dependencies, and deployment assumptions as questions "
        "for your tech lead or senior engineer."
    )

    return ChatResponse(answer=answer, citations=citations)
