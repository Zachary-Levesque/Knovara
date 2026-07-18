"""Personalized onboarding plan generation for the Knovara demo backend."""

import json

from openai import OpenAI
from pydantic import BaseModel, Field

from config import DEFAULT_COLLECTION, OPENAI_API_KEY, OPENAI_CHAT_MODEL
from retrieval import SourceChunk, search_sources


class MentorRequest(BaseModel):
    name: str = Field(default="New teammate", max_length=80)
    role: str = Field(default="Software Engineer", max_length=80)
    team: str = Field(default="Platform", max_length=80)
    background: str = Field(default="General backend and product engineering", max_length=240)
    goal: str = Field(default="Become productive on the core system", max_length=240)
    collection_name: str = Field(default=DEFAULT_COLLECTION, max_length=80)


class LearningItem(BaseModel):
    title: str
    detail: str
    owner: str


class MentorBriefing(BaseModel):
    headline: str
    summary: str
    first_week: list[LearningItem]
    recommended_sources: list[str]
    people_to_meet: list[str]
    mode: str = "demo"
    collection_name: str = DEFAULT_COLLECTION


def build_briefing(request: MentorRequest) -> MentorBriefing:
    """Create an onboarding briefing from retrieved context with an LLM path when configured."""

    sources = search_sources(
        f"{request.team} {request.role} {request.goal}",
        collection_name=request.collection_name,
    )
    retrieval_mode = "indexed" if any(source.score is not None for source in sources) else "demo"
    if OPENAI_API_KEY:
        generated = _generate_briefing(request, sources, retrieval_mode)
        if generated:
            return generated

    return _fallback_briefing(request, sources, retrieval_mode)


def _fallback_briefing(
    request: MentorRequest,
    sources: list[SourceChunk],
    retrieval_mode: str,
) -> MentorBriefing:
    recommended_sources = [
        f"{source.title} ({source.source})"
        for source in sources
    ] or [
        "Architecture overview",
        "Recent design decisions",
        "Runbook and incident notes",
        "Team coding standards",
    ]
    source_names = ", ".join(source.title for source in sources[:2]) or "the project knowledge index"

    return MentorBriefing(
        headline=f"{request.name}'s ramp-up path for {request.team}",
        summary=(
            f"Knovara will focus your onboarding around the {request.role} "
            f"responsibilities on {request.team}. Given your background in "
            f"{request.background}, the first week should connect system "
            f"context directly to your goal: {request.goal}. Start with {source_names} "
            "and turn unclear ownership, dependencies, and release steps into mentor questions."
        ),
        first_week=[
            LearningItem(
                title="Map the indexed system context",
                detail=(
                    "Read the top recommended sources, identify upstream and downstream "
                    "systems, and write down the terms or owners that remain unclear."
                ),
                owner="Tech lead",
            ),
            LearningItem(
                title="Trace a real workflow",
                detail=(
                    "Follow one project workflow through code, data, deployment, and "
                    "operational notes using the retrieved source list as your starting point."
                ),
                owner="Senior engineer",
            ),
            LearningItem(
                title="Ship a bounded change",
                detail="Pick a low-risk issue that exercises local setup, review flow, tests, and release notes.",
                owner="Manager",
            ),
        ],
        recommended_sources=recommended_sources,
        people_to_meet=[
            "Tech lead for system boundaries",
            "Product partner for user context",
            "On-call owner for operational realities",
        ],
        mode=retrieval_mode,
        collection_name=request.collection_name,
    )


def _generate_briefing(
    request: MentorRequest,
    sources: list[SourceChunk],
    retrieval_mode: str,
) -> MentorBriefing | None:
    context = "\n\n".join(
        f"Source: {source.title} ({source.source})\n{source.relevance or source.content}"
        for source in sources
    )
    prompt = (
        "Create a concise engineer onboarding briefing as JSON with these keys: "
        "headline, summary, first_week, recommended_sources, people_to_meet. "
        "first_week must be a list of three objects with title, detail, and owner. "
        "Use only the provided context and the engineer profile.\n\n"
        f"Name: {request.name}\n"
        f"Role: {request.role}\n"
        f"Team: {request.team}\n"
        f"Background: {request.background}\n"
        f"Goal: {request.goal}\n\n"
        f"Context:\n{context}"
    )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are Knovara, a practical technical onboarding mentor.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        payload["mode"] = f"{retrieval_mode}+llm"
        payload["collection_name"] = request.collection_name
        return MentorBriefing.model_validate(payload)
    except Exception:
        return None
