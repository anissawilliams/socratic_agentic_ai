from typing import Literal

from pydantic import BaseModel, Field

from app.socratic.phases import SocraticPhase


RoutingAction = Literal[
    "stay",
    "switch",
    "revisit",
]

MoveType = Literal[
    "clarify",
    "probe_reason",
    "examine_evidence",
    "develop_idea",
    "test_limit",
    "apply_case",
    "compare",
    "synthesize",
    "scaffold",
]


class RoutingRecord(BaseModel):
    """One accepted routing decision retained in session memory."""

    phase: SocraticPhase

    topic: str = Field(
        description=(
            "Short stable label for the substantive topic, such as "
            "'verification_requirements' or 'citation_quality'."
        )
    )

    move_type: MoveType

    target: str = Field(
        description=(
            "The precise intellectual target assigned to the tutor."
        )
    )


class RouteDecision(BaseModel):
    """The router's proposed next conversational move."""

    action: RoutingAction = Field(
        description=(
            "Stay in the current role, switch to a new role, or revisit "
            "a role used earlier. Application code verifies this value."
        )
    )

    next_phase: SocraticPhase

    topic: str = Field(
        description=(
            "A short stable semantic label for the topic being pursued. "
            "Reuse an existing topic label when returning to that topic."
        )
    )

    move_type: MoveType = Field(
        description=(
            "The specific conversational operation the tutor should perform."
        )
    )

    target: str = Field(
        description=(
            "A precise, grounded description of what the next tutor response "
            "should help the learner examine, develop, test, or apply."
        )
    )

    reasoning_summary: str = Field(
        description=(
            "A concise internal explanation grounded in the dialogue."
        )
    )

    avoid_repeating: list[str] = Field(
        default_factory=list,
        description=(
            "Previously answered questions, established points, or semantic "
            "targets that the tutor must not request again."
        ),
    )