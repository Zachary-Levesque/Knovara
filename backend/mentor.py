"""Personalized onboarding plan generation for the Knovara demo backend."""

from pydantic import BaseModel, Field

from config import DEFAULT_COLLECTION
from retrieval import search_sources


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


def build_briefing(request: MentorRequest) -> MentorBriefing:
    """Create a credible deterministic briefing without requiring an LLM key."""

    sources = search_sources(
        f"{request.team} {request.role} {request.goal}",
        collection_name=request.collection_name,
    )
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
    )
