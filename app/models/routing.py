from typing import Literal

from pydantic import BaseModel, Field

from app.socratic.phases import SocraticPhase


RoutingAction = Literal[
    "stay",
    "switch",
    "revisit",
]


class RouteDecision(BaseModel):
    action: RoutingAction = Field(
        description=(
            "Stay in the current role, switch to a different role, "
            "or revisit a role used earlier in the dialogue."
        )
    )

    next_phase: SocraticPhase = Field(
        description=(
            "The Socratic role best suited to the next conversational move."
        )
    )

    target: str = Field(
        description=(
            "The specific claim, reason, evidence, assumption, distinction, "
            "implication, or application that the next response should examine."
        )
    )

    reasoning_summary: str = Field(
        description=(
            "A concise, auditable explanation of why this role and target "
            "are appropriate, grounded in the dialogue and evaluation."
        )
    )

    avoid_repeating: list[str] = Field(
        default_factory=list,
        description=(
            "Questions, issues, or requests already addressed that the "
            "next response must not repeat."
        ),
    )