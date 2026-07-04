"""Personalized onboarding plan generation for the Knovara demo backend."""

from pydantic import BaseModel, Field


class MentorRequest(BaseModel):
    name: str = Field(default="New teammate", max_length=80)
    role: str = Field(default="Software Engineer", max_length=80)
    team: str = Field(default="Platform", max_length=80)
    background: str = Field(default="General backend and product engineering", max_length=240)
    goal: str = Field(default="Become productive on the core system", max_length=240)


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

    return MentorBriefing(
        headline=f"{request.name}'s ramp-up path for {request.team}",
        summary=(
            f"Knovara will focus your onboarding around the {request.role} "
            f"responsibilities on {request.team}. Given your background in "
            f"{request.background}, the first week should connect system "
            f"context directly to your goal: {request.goal}."
        ),
        first_week=[
            LearningItem(
                title="Map the system",
                detail="Read architecture notes, identify upstream and downstream services, and capture unknowns.",
                owner="Tech lead",
            ),
            LearningItem(
                title="Trace a real workflow",
                detail="Follow one customer-facing path through code, data, deploy, and observability surfaces.",
                owner="Senior engineer",
            ),
            LearningItem(
                title="Ship a bounded change",
                detail="Pick a low-risk issue that exercises local setup, review flow, tests, and release notes.",
                owner="Manager",
            ),
        ],
        recommended_sources=[
            "Architecture overview",
            "Recent design decisions",
            "Runbook and incident notes",
            "Team coding standards",
        ],
        people_to_meet=[
            "Tech lead for system boundaries",
            "Product partner for user context",
            "On-call owner for operational realities",
        ],
    )
