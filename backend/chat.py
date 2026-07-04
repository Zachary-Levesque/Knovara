"""Grounded Q&A helpers for the Knovara demo backend."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    role: str = Field(default="Backend Engineer", max_length=80)
    team: str = Field(default="Platform", max_length=80)


class Citation(BaseModel):
    title: str
    source: str
    relevance: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    follow_ups: list[str]


def answer_question(request: ChatRequest) -> ChatResponse:
    """Return a deterministic grounded answer suitable for a portfolio demo."""

    normalized_question = request.question.strip()
    answer = (
        f"For a {request.role} joining {request.team}, start by mapping the "
        "service boundaries, reading the architecture notes, and tracing one "
        "recent production decision from problem statement to implementation. "
        f"For your question, '{normalized_question}', Knovara would retrieve "
        "the most relevant source chunks, synthesize the answer, and preserve "
        "citations so the new engineer can verify the context."
    )
    return ChatResponse(
        answer=answer,
        citations=[
            Citation(
                title="Architecture Overview",
                source="docs/architecture.md",
                relevance="Explains service ownership, core systems, and integration points.",
            ),
            Citation(
                title="Engineering Decisions",
                source="docs/decisions/",
                relevance="Shows why recent tradeoffs were made and who approved them.",
            ),
            Citation(
                title="Onboarding Playbook",
                source="docs/onboarding.md",
                relevance="Converts team context into first-week learning tasks.",
            ),
        ],
        follow_ups=[
            "Which repository should I inspect first?",
            "Who owns the deployment pipeline?",
            "What decisions changed this system recently?",
        ],
    )
