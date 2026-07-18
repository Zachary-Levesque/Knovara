"""
Grounded Q&A handler.

This file will coordinate retrieval and LLM calls for question answering,
ensuring responses are grounded in indexed organizational knowledge and include
the supporting context required by the frontend.
"""
from pydantic import BaseModel, Field
from openai import OpenAI

from config import DEFAULT_COLLECTION, OPENAI_API_KEY, OPENAI_CHAT_MODEL
from retrieval import search_sources


class ChatRequest(BaseModel):
    """Question-answering request scoped to a user's onboarding context."""

    question: str = Field(min_length=3, max_length=500)
    role: str = Field(default="Software Engineer", max_length=80)
    team: str = Field(default="Platform", max_length=80)
    collection_name: str = Field(default=DEFAULT_COLLECTION, max_length=80)


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
    """Answer from retrieved sources, with an LLM path when configured."""

    sources = search_sources(request.question, collection_name=request.collection_name)
    citations = [
        Citation(
            title=source.title,
            source=source.source,
            relevance=source.relevance or source.content,
        )
        for source in sources
    ]

    if OPENAI_API_KEY:
        generated_answer = _generate_answer(request, citations)
        if generated_answer:
            return ChatResponse(answer=generated_answer, citations=citations)

    return ChatResponse(answer=_fallback_answer(request, citations), citations=citations)


def _fallback_answer(request: ChatRequest, citations: list[Citation]) -> str:
    source_titles = ", ".join(citation.title for citation in citations)
    if not source_titles:
        source_titles = "the available project sources"
    return (
        f"For a {request.role} joining {request.team}, start by reading {source_titles}. "
        "Use the architecture overview to understand service boundaries, then review "
        "onboarding norms and decision records before making your first change. "
        "Capture unclear ownership, dependencies, and deployment assumptions as questions "
        "for your tech lead or senior engineer."
    )


def _generate_answer(request: ChatRequest, citations: list[Citation]) -> str:
    context = "\n\n".join(
        f"Source: {citation.title} ({citation.source})\n{citation.relevance}"
        for citation in citations
    )
    prompt = (
        "Answer the engineer's onboarding question using only the provided context. "
        "Be specific, practical, and mention which sources support the answer.\n\n"
        f"Role: {request.role}\n"
        f"Team: {request.team}\n"
        f"Question: {request.question}\n\n"
        f"Context:\n{context}"
    )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are Knovara, a concise technical onboarding mentor.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
    except Exception:
        return ""

    return response.choices[0].message.content or ""
